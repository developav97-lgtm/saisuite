// Package firebird provides a client for connecting to Firebird 2.5 databases
// and executing the queries needed to extract Saiopen ERP data (GL, ACCT, CUST, LISTA,
// PROYECTOS, ACTIVIDADES).
package firebird

import (
	"database/sql"
	"fmt"
	"log/slog"
	"strings"
	"time"

	_ "github.com/nakagami/firebirdsql"
)

// Client wraps a Firebird database connection with methods for extracting
// Saiopen data tables.
type Client struct {
	dsn    string
	db     *sql.DB
	logger *slog.Logger
}

// GLRecord represents a single denormalized General Ledger record
// with all JOINed reference data (account hierarchy, third party, cost centers, etc.).
type GLRecord struct {
	Conteo             int64   `json:"conteo"`
	Fecha              string  `json:"fecha"`
	DueDate            string  `json:"duedate"`
	Invc               string  `json:"invc"`
	TerceroID          string  `json:"tercero_id"`
	TerceroNombre      string  `json:"tercero_nombre"`
	Auxiliar           float64 `json:"auxiliar"`
	AuxiliarNombre     string  `json:"auxiliar_nombre"`
	TituloCodigo       int     `json:"titulo_codigo"`
	TituloNombre       string  `json:"titulo_nombre"`
	GrupoCodigo        int     `json:"grupo_codigo"`
	GrupoNombre        string  `json:"grupo_nombre"`
	CuentaCodigo       int     `json:"cuenta_codigo"`
	CuentaNombre       string  `json:"cuenta_nombre"`
	SubcuentaCodigo    int     `json:"subcuenta_codigo"`
	SubcuentaNombre    string  `json:"subcuenta_nombre"`
	Debito             string  `json:"debito"`
	Credito            string  `json:"credito"`
	Tipo               string  `json:"tipo"`
	Batch              int     `json:"batch"`
	Descripcion        string  `json:"descripcion"`
	Periodo            string  `json:"periodo"`
	DepartamentoCodigo *int    `json:"departamento_codigo"`
	DepartamentoNombre string  `json:"departamento_nombre"`
	CentroCostoCodigo  *int    `json:"centro_costo_codigo"`
	CentroCostoNombre  string  `json:"centro_costo_nombre"`
	ProyectoCodigo     *string `json:"proyecto_codigo"`
	ProyectoNombre     string  `json:"proyecto_nombre"`
	ActividadCodigo    *string `json:"actividad_codigo"`
	ActividadNombre    string  `json:"actividad_nombre"`
}

// AcctRecord represents a chart of accounts entry from the ACCT table.
type AcctRecord struct {
	Acct           float64 `json:"acct"`
	Descripcion    string  `json:"descripcion"`
	Tipo           string  `json:"tipo"`
	Class          string  `json:"class"`
	Nvel           int     `json:"nvel"`
	CdgoTtl        int     `json:"cdgo_ttl"`
	CdgoGrpo       int     `json:"cdgo_grpo"`
	CdgoCnta       int     `json:"cdgo_cnta"`
	CdgoSbCnta     int     `json:"cdgo_sbcnta"`
	DprtmntoCsto   string  `json:"dprtmnto_csto"`
	Jbno           string  `json:"jbno"`
	Activo         string  `json:"activo"`
}

// CustRecord represents a third-party entity from the CUST table.
type CustRecord struct {
	IDN           string  `json:"id_n"`
	NIT           string  `json:"nit"`
	Company       string  `json:"company"`
	Addr1         string  `json:"addr1"`
	City          string  `json:"city"`
	Phone1        string  `json:"phone1"`
	Email         string  `json:"email"`
	Cliente       string  `json:"cliente"`
	Proveedor     string  `json:"proveedor"`
	Empleado      string  `json:"empleado"`
	Activo        bool    `json:"activo"`
}

// ListaRecord represents a department or cost center from the LISTA table.
type ListaRecord struct {
	Tipo        string `json:"tipo"`
	Codigo      int    `json:"codigo"`
	Descripcion string `json:"descripcion"`
	DpccEst     string `json:"dpcc_est"`
}

// ProyectoRecord represents a project from the PROYECTOS table.
type ProyectoRecord struct {
	Codigo      string  `json:"codigo"`
	IDNit       string  `json:"id_nit"`
	Descripcion string  `json:"descripcion"`
	FechaI      *string `json:"fecha_i"`
	FechaEstT   *string `json:"fecha_est_t"`
	CostoEst    float64 `json:"costo_est"`
	ProEst      string  `json:"pro_est"`
}

// ActividadRecord represents an activity from the ACTIVIDADES table.
type ActividadRecord struct {
	Codigo      string  `json:"codigo"`
	Descripcion string  `json:"descripcion"`
	Proyecto    string  `json:"proyecto"`
	DP          int     `json:"dp"`
	CC          int     `json:"cc"`
}

// New creates a new Firebird client with the given DSN.
// Format: user:password@host:port/path/to/database.fdb
func New(dsn string, logger *slog.Logger) *Client {
	return &Client{
		dsn:    dsn,
		logger: logger,
	}
}

// Connect opens the Firebird database connection.
func (c *Client) Connect() error {
	db, err := sql.Open("firebirdsql", c.dsn)
	if err != nil {
		return fmt.Errorf("failed to open firebird connection: %w", err)
	}

	// Configure connection pool for a single-server agent
	db.SetMaxOpenConns(3)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(30 * time.Minute)

	if err := db.Ping(); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping firebird: %w", err)
	}

	c.db = db
	c.logger.Info("firebird connection established", "dsn", maskDSN(c.dsn))
	return nil
}

// Close closes the Firebird database connection.
func (c *Client) Close() error {
	if c.db != nil {
		return c.db.Close()
	}
	return nil
}

// Ping tests the Firebird database connection.
func (c *Client) Ping() error {
	if c.db == nil {
		return fmt.Errorf("database not connected")
	}
	return c.db.Ping()
}

// QueryGLIncremental fetches GL records with CONTEO greater than lastConteo,
// limited to batchSize rows. Returns denormalized records with all JOINs applied.
func (c *Client) QueryGLIncremental(lastConteo int64, batchSize int) ([]GLRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT G.CONTEO, G.FECHA, G.DUEDATE, G.INVC,
			C.ID_N AS TERCERO_ID, C.COMPANY AS TERCERO_NOMBRE,
			A.ACCT AS AUXILIAR, A.DESCRIPCION AS AUXILIAR_NOMBRE,
			A.CDGOTTL AS TITULO_CODIGO, ACT.DESCRIPCION AS TITULO_NOMBRE,
			A.CDGOGRPO AS GRUPO_CODIGO, ACG.DESCRIPCION AS GRUPO_NOMBRE,
			A.CDGOCNTA AS CUENTA_CODIGO, ACC.DESCRIPCION AS CUENTA_NOMBRE,
			A.CDGOSBCNTA AS SUBCUENTA_CODIGO, ACS.DESCRIPCION AS SUBCUENTA_NOMBRE,
			G.DEBIT, G.CREDIT, G.TIPO, G.BATCH, G.DESCRIPCION, G.PERIOD,
			G.DEPTO, LD.DESCRIPCION AS DEPARTAMENTO_NOMBRE,
			G.CCOST, LC.DESCRIPCION AS CENTRO_COSTO_NOMBRE,
			G.PROYECTO, P.DESCRIPCION AS PROYECTO_NOMBRE,
			G.ACTIVIDAD, AC.DESCRIPCION AS ACTIVIDAD_NOMBRE
		FROM GL G
		INNER JOIN CUST C ON C.ID_N = G.ID_N
		INNER JOIN ACCT A ON A.ACCT = G.ACCT
		INNER JOIN ACCT ACT ON A.CDGOTTL = ACT.ACCT
		INNER JOIN ACCT ACG ON A.CDGOGRPO = ACG.ACCT
		INNER JOIN ACCT ACC ON A.CDGOCNTA = ACC.ACCT
		INNER JOIN ACCT ACS ON A.CDGOSBCNTA = ACS.ACCT
		LEFT JOIN LISTA LD ON LD.CODIGO = G.DEPTO AND LD.TIPO = 'DP'
		LEFT JOIN LISTA LC ON LC.CODIGO = G.CCOST AND LC.TIPO = 'CC'
		LEFT JOIN PROYECTOS P ON P.CODIGO = G.PROYECTO
		LEFT JOIN ACTIVIDADES AC ON AC.CODIGO = G.ACTIVIDAD
		WHERE G.CONTEO > ?
		ORDER BY G.CONTEO ASC
		ROWS 1 TO ?`

	c.logger.Debug("executing GL query", "last_conteo", lastConteo, "batch_size", batchSize)

	rows, err := c.db.Query(query, lastConteo, batchSize)
	if err != nil {
		return nil, fmt.Errorf("GL query failed: %w", err)
	}
	defer rows.Close()

	var records []GLRecord
	for rows.Next() {
		var r GLRecord
		var fecha, duedate sql.NullTime
		var invc sql.NullString
		var debit, credit sql.NullFloat64
		var tipo, descripcion, period sql.NullString
		var batch sql.NullInt64
		var depto, ccost sql.NullInt64
		var deptoNombre, ccostNombre sql.NullString
		var proyecto, proyectoNombre sql.NullString
		var actividad, actividadNombre sql.NullString
		var terceroID, terceroNombre sql.NullString
		var auxiliar sql.NullFloat64
		var auxiliarNombre sql.NullString
		var tituloCodigo, grupoCodigo, cuentaCodigo, subcuentaCodigo sql.NullInt64
		var tituloNombre, grupoNombre, cuentaNombre, subcuentaNombre sql.NullString

		err := rows.Scan(
			&r.Conteo, &fecha, &duedate, &invc,
			&terceroID, &terceroNombre,
			&auxiliar, &auxiliarNombre,
			&tituloCodigo, &tituloNombre,
			&grupoCodigo, &grupoNombre,
			&cuentaCodigo, &cuentaNombre,
			&subcuentaCodigo, &subcuentaNombre,
			&debit, &credit, &tipo, &batch, &descripcion, &period,
			&depto, &deptoNombre,
			&ccost, &ccostNombre,
			&proyecto, &proyectoNombre,
			&actividad, &actividadNombre,
		)
		if err != nil {
			return nil, fmt.Errorf("GL row scan failed: %w", err)
		}

		// Map nullable values
		if fecha.Valid {
			r.Fecha = fecha.Time.Format("2006-01-02")
		}
		if duedate.Valid {
			r.DueDate = duedate.Time.Format("2006-01-02")
		}
		r.Invc = trimString(invc)
		r.TerceroID = trimString(terceroID)
		r.TerceroNombre = trimString(terceroNombre)
		if auxiliar.Valid {
			r.Auxiliar = auxiliar.Float64
		}
		r.AuxiliarNombre = trimString(auxiliarNombre)
		if tituloCodigo.Valid {
			r.TituloCodigo = int(tituloCodigo.Int64)
		}
		r.TituloNombre = trimString(tituloNombre)
		if grupoCodigo.Valid {
			r.GrupoCodigo = int(grupoCodigo.Int64)
		}
		r.GrupoNombre = trimString(grupoNombre)
		if cuentaCodigo.Valid {
			r.CuentaCodigo = int(cuentaCodigo.Int64)
		}
		r.CuentaNombre = trimString(cuentaNombre)
		if subcuentaCodigo.Valid {
			r.SubcuentaCodigo = int(subcuentaCodigo.Int64)
		}
		r.SubcuentaNombre = trimString(subcuentaNombre)

		// Monetary values as string "1500000.00" — never float in JSON
		r.Debito = formatMoney(debit)
		r.Credito = formatMoney(credit)

		r.Tipo = trimString(tipo)
		if batch.Valid {
			r.Batch = int(batch.Int64)
		}
		r.Descripcion = trimString(descripcion)
		r.Periodo = trimString(period)

		if depto.Valid && depto.Int64 > 0 {
			v := int(depto.Int64)
			r.DepartamentoCodigo = &v
		}
		r.DepartamentoNombre = trimString(deptoNombre)

		if ccost.Valid && ccost.Int64 > 0 {
			v := int(ccost.Int64)
			r.CentroCostoCodigo = &v
		}
		r.CentroCostoNombre = trimString(ccostNombre)

		proy := trimString(proyecto)
		if proy != "" {
			r.ProyectoCodigo = &proy
		}
		r.ProyectoNombre = trimString(proyectoNombre)

		act := trimString(actividad)
		if act != "" {
			r.ActividadCodigo = &act
		}
		r.ActividadNombre = trimString(actividadNombre)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GL rows iteration error: %w", err)
	}

	c.logger.Debug("GL query returned records", "count", len(records))
	return records, nil
}

// QueryAllAcct fetches the complete chart of accounts from the ACCT table.
func (c *Client) QueryAllAcct() ([]AcctRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT ACCT, DESCRIPCION, TIPO, CLASS, NVEL,
			CDGOTTL, CDGOGRPO, CDGOCNTA, CDGOSBCNTA,
			DPRTMNTOCSTO, JBNO, ACTIVO
		FROM ACCT
		ORDER BY ACCT`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("ACCT query failed: %w", err)
	}
	defer rows.Close()

	var records []AcctRecord
	for rows.Next() {
		var r AcctRecord
		var desc, tipo, class sql.NullString
		var nvel sql.NullInt64
		var cdgoTtl, cdgoGrpo, cdgoCnta, cdgoSbCnta sql.NullInt64
		var dprtmntoCsto, jbno, activo sql.NullString

		err := rows.Scan(
			&r.Acct, &desc, &tipo, &class, &nvel,
			&cdgoTtl, &cdgoGrpo, &cdgoCnta, &cdgoSbCnta,
			&dprtmntoCsto, &jbno, &activo,
		)
		if err != nil {
			return nil, fmt.Errorf("ACCT row scan failed: %w", err)
		}

		r.Descripcion = trimString(desc)
		r.Tipo = trimString(tipo)
		r.Class = trimString(class)
		if nvel.Valid {
			r.Nvel = int(nvel.Int64)
		}
		if cdgoTtl.Valid {
			r.CdgoTtl = int(cdgoTtl.Int64)
		}
		if cdgoGrpo.Valid {
			r.CdgoGrpo = int(cdgoGrpo.Int64)
		}
		if cdgoCnta.Valid {
			r.CdgoCnta = int(cdgoCnta.Int64)
		}
		if cdgoSbCnta.Valid {
			r.CdgoSbCnta = int(cdgoSbCnta.Int64)
		}
		r.DprtmntoCsto = trimString(dprtmntoCsto)
		r.Jbno = trimString(jbno)
		r.Activo = trimString(activo)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("ACCT rows iteration error: %w", err)
	}

	c.logger.Info("ACCT query completed", "count", len(records))
	return records, nil
}

// QueryAllCust fetches all third-party entities from the CUST table.
func (c *Client) QueryAllCust() ([]CustRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT ID_N, NIT, COMPANY, ADDR1, CITY, PHONE1, EMAIL,
			CLIENTE, PROVEEDOR, EMPLEADO, INACTIVO
		FROM CUST
		ORDER BY ID_N`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("CUST query failed: %w", err)
	}
	defer rows.Close()

	var records []CustRecord
	for rows.Next() {
		var r CustRecord
		var idn, nit, company, addr1, city, phone1, email sql.NullString
		var cliente, proveedor, empleado, inactivo sql.NullString

		err := rows.Scan(
			&idn, &nit, &company, &addr1, &city, &phone1, &email,
			&cliente, &proveedor, &empleado, &inactivo,
		)
		if err != nil {
			return nil, fmt.Errorf("CUST row scan failed: %w", err)
		}

		r.IDN = trimString(idn)
		r.NIT = trimString(nit)
		r.Company = trimString(company)
		r.Addr1 = trimString(addr1)
		r.City = trimString(city)
		r.Phone1 = trimString(phone1)
		r.Email = trimString(email)
		r.Cliente = trimString(cliente)
		r.Proveedor = trimString(proveedor)
		r.Empleado = trimString(empleado)
		// INACTIVO is CHAR(1): 'S' means inactive
		r.Activo = trimString(inactivo) != "S"

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("CUST rows iteration error: %w", err)
	}

	c.logger.Info("CUST query completed", "count", len(records))
	return records, nil
}

// QueryAllLista fetches all department and cost center entries from the LISTA table.
// Pass tipo="DP" for departments, tipo="CC" for cost centers, or "" for all.
func (c *Client) QueryAllLista(tipo string) ([]ListaRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	var query string
	var args []interface{}

	if tipo != "" {
		query = `SELECT TIPO, CODIGO, DESCRIPCION, DPCCEST FROM LISTA WHERE TIPO = ? ORDER BY TIPO, CODIGO`
		args = append(args, tipo)
	} else {
		query = `SELECT TIPO, CODIGO, DESCRIPCION, DPCCEST FROM LISTA WHERE TIPO IN ('DP', 'CC') ORDER BY TIPO, CODIGO`
	}

	rows, err := c.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("LISTA query failed: %w", err)
	}
	defer rows.Close()

	var records []ListaRecord
	for rows.Next() {
		var r ListaRecord
		var tipoVal, desc, dpccEst sql.NullString
		var codigo sql.NullInt64

		err := rows.Scan(&tipoVal, &codigo, &desc, &dpccEst)
		if err != nil {
			return nil, fmt.Errorf("LISTA row scan failed: %w", err)
		}

		r.Tipo = trimString(tipoVal)
		if codigo.Valid {
			r.Codigo = int(codigo.Int64)
		}
		r.Descripcion = trimString(desc)
		r.DpccEst = trimString(dpccEst)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("LISTA rows iteration error: %w", err)
	}

	c.logger.Info("LISTA query completed", "tipo", tipo, "count", len(records))
	return records, nil
}

// QueryAllProyectos fetches all projects from the PROYECTOS table.
func (c *Client) QueryAllProyectos() ([]ProyectoRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT CODIGO, ID_NIT, DESCRIPCION, FECHA_I, FECHA_EST_T, COSTOEST, PROEST
		FROM PROYECTOS
		ORDER BY CODIGO`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("PROYECTOS query failed: %w", err)
	}
	defer rows.Close()

	var records []ProyectoRecord
	for rows.Next() {
		var r ProyectoRecord
		var codigo, idNit, desc, proEst sql.NullString
		var fechaI, fechaEstT sql.NullTime
		var costoEst sql.NullFloat64

		err := rows.Scan(&codigo, &idNit, &desc, &fechaI, &fechaEstT, &costoEst, &proEst)
		if err != nil {
			return nil, fmt.Errorf("PROYECTOS row scan failed: %w", err)
		}

		r.Codigo = trimString(codigo)
		r.IDNit = trimString(idNit)
		r.Descripcion = trimString(desc)
		if fechaI.Valid {
			s := fechaI.Time.Format("2006-01-02")
			r.FechaI = &s
		}
		if fechaEstT.Valid {
			s := fechaEstT.Time.Format("2006-01-02")
			r.FechaEstT = &s
		}
		if costoEst.Valid {
			r.CostoEst = costoEst.Float64
		}
		r.ProEst = trimString(proEst)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("PROYECTOS rows iteration error: %w", err)
	}

	c.logger.Info("PROYECTOS query completed", "count", len(records))
	return records, nil
}

// QueryAllActividades fetches all activities from the ACTIVIDADES table.
func (c *Client) QueryAllActividades() ([]ActividadRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT CODIGO, DESCRIPCION, PROYECTO, DP, CC
		FROM ACTIVIDADES
		ORDER BY CODIGO`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("ACTIVIDADES query failed: %w", err)
	}
	defer rows.Close()

	var records []ActividadRecord
	for rows.Next() {
		var r ActividadRecord
		var codigo, desc, proyecto sql.NullString
		var dp, cc sql.NullInt64

		err := rows.Scan(&codigo, &desc, &proyecto, &dp, &cc)
		if err != nil {
			return nil, fmt.Errorf("ACTIVIDADES row scan failed: %w", err)
		}

		r.Codigo = trimString(codigo)
		r.Descripcion = trimString(desc)
		r.Proyecto = trimString(proyecto)
		if dp.Valid {
			r.DP = int(dp.Int64)
		}
		if cc.Valid {
			r.CC = int(cc.Int64)
		}

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("ACTIVIDADES rows iteration error: %w", err)
	}

	c.logger.Info("ACTIVIDADES query completed", "count", len(records))
	return records, nil
}

// CountGL returns the total number of GL records and the max CONTEO value.
func (c *Client) CountGL() (total int64, maxConteo int64, err error) {
	if c.db == nil {
		return 0, 0, fmt.Errorf("database not connected")
	}

	row := c.db.QueryRow("SELECT COUNT(*), COALESCE(MAX(CONTEO), 0) FROM GL")
	err = row.Scan(&total, &maxConteo)
	if err != nil {
		return 0, 0, fmt.Errorf("GL count query failed: %w", err)
	}
	return total, maxConteo, nil
}

// trimString extracts a string from a NullString and trims whitespace.
// Firebird CHAR fields are right-padded with spaces.
func trimString(ns sql.NullString) string {
	if !ns.Valid {
		return ""
	}
	return strings.TrimSpace(ns.String)
}

// formatMoney formats a nullable float as a string with 2 decimal places.
// Returns "0.00" if null. Monetary values are always transmitted as strings.
func formatMoney(nf sql.NullFloat64) string {
	if !nf.Valid {
		return "0.00"
	}
	return fmt.Sprintf("%.2f", nf.Float64)
}

// maskDSN masks the password in a DSN string for safe logging.
func maskDSN(dsn string) string {
	// Format: user:password@host:port/path
	parts := strings.SplitN(dsn, "@", 2)
	if len(parts) != 2 {
		return "***"
	}
	userParts := strings.SplitN(parts[0], ":", 2)
	if len(userParts) != 2 {
		return "***"
	}
	return userParts[0] + ":***@" + parts[1]
}
