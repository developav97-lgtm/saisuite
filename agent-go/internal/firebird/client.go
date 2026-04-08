// Package firebird provides a client for connecting to Firebird 2.5 databases
// and executing the queries needed to extract Saiopen ERP data (GL, ACCT, CUST, LISTA,
// PROYECTOS, ACTIVIDADES).
package firebird

import (
	"context"
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
	Departamento  string  `json:"departamento"`
	Phone1        string  `json:"phone1"`
	Phone2        string  `json:"phone2"`
	Email         string  `json:"email"`
	Cliente       string  `json:"cliente"`
	Proveedor     string  `json:"proveedor"`
	Empleado      string  `json:"empleado"`
	Activo        bool    `json:"activo"`
	Version       int64   `json:"version"`
	Acct          string  `json:"acct"`
	AcctP         string  `json:"acctp"`
	Regimen       string  `json:"regimen"`
	FechaCreacion string  `json:"fecha_creacion"`
	Descuento     float64 `json:"descuento"`
	CreditLmt     float64 `json:"creditlmt"`
}

// ShipToRecord represents a shipping address (SHIPTO) linked to a CUST entry.
type ShipToRecord struct {
	IDN          string `json:"id_n"`
	SucCliente   int    `json:"succliente"`
	Descripcion  string `json:"descripcion"`
	Company      string `json:"company"`
	Addr1        string `json:"addr1"`
	Addr2        string `json:"addr2"`
	City         string `json:"city"`
	Departamento string `json:"departamento"`
	CodDpto      string `json:"cod_dpto"`
	CodMunicipio string `json:"cod_municipio"`
	Phone1       string `json:"phone1"`
	Email        string `json:"email"`
	Pais         string `json:"pais"`
	Zona         int    `json:"zona"`
	IDVend       int    `json:"id_vend"`
	Estado       string `json:"estado"`
}

// TributariaRecord represents the tax/tributaria info for a CUST entry (1:1).
type TributariaRecord struct {
	IDN               string `json:"id_n"`
	Company           string `json:"company"`
	Tdoc              int    `json:"tdoc"`
	TipoContribuyente int    `json:"tipo_contribuyente"`
	PrimerNombre      string `json:"primer_nombre"`
	SegundoNombre     string `json:"segundo_nombre"`
	PrimerApellido    string `json:"primer_apellido"`
	SegundoApellido   string `json:"segundo_apellido"`
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

// queryCust executes a CUST SELECT with optional WHERE clause and args.
// Returns records and the max Version seen (0 if empty result).
func (c *Client) queryCust(lastVersion int64) ([]CustRecord, int64, error) {
	// "Version" must be quoted — it is a reserved word in Firebird SQL.
	where := ""
	if lastVersion > 0 {
		where = fmt.Sprintf(` WHERE "Version" > %d`, lastVersion)
	}

	query := fmt.Sprintf(`
		SELECT ID_N, NIT, COMPANY, ADDR1, CITY, DEPARTAMENTO, PHONE1, PHONE2, EMAIL,
			CLIENTE, PROVEEDOR, EMPLEADO, INACTIVO, "Version",
			ACCT, ACCTP, REGIMEN, FECHA_CREACION, DESCUENTO, CREDITLMT
		FROM CUST%s`, where)

	c.logger.Info("CUST query executing", "last_version", lastVersion)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	rows, err := c.db.QueryContext(ctx, query)
	if err != nil {
		return nil, 0, fmt.Errorf("CUST query failed: %w", err)
	}
	defer rows.Close()

	var records []CustRecord
	var maxVersion int64
	for rows.Next() {
		var r CustRecord
		var idn, nit, company, addr1, city, depto, phone1, phone2, email sql.NullString
		var cliente, proveedor, empleado, inactivo sql.NullString
		var version sql.NullInt64
		var acct, acctp sql.NullFloat64
		var regimen, fechaCreacion sql.NullString
		var descuento, creditlmt sql.NullFloat64

		if err := rows.Scan(
			&idn, &nit, &company, &addr1, &city, &depto, &phone1, &phone2, &email,
			&cliente, &proveedor, &empleado, &inactivo, &version,
			&acct, &acctp, &regimen, &fechaCreacion, &descuento, &creditlmt,
		); err != nil {
			return nil, 0, fmt.Errorf("CUST row scan failed: %w", err)
		}

		r.IDN = trimString(idn)
		r.NIT = trimString(nit)
		r.Company = trimString(company)
		r.Addr1 = trimString(addr1)
		r.City = trimString(city)
		r.Departamento = trimString(depto)
		r.Phone1 = trimString(phone1)
		r.Phone2 = trimString(phone2)
		r.Email = trimString(email)
		r.Cliente = trimString(cliente)
		r.Proveedor = trimString(proveedor)
		r.Empleado = trimString(empleado)
		r.Activo = trimString(inactivo) != "S"
		if version.Valid {
			r.Version = version.Int64
			if r.Version > maxVersion {
				maxVersion = r.Version
			}
		}
		if acct.Valid && acct.Float64 != 0 {
			r.Acct = fmt.Sprintf("%.0f", acct.Float64)
		}
		if acctp.Valid && acctp.Float64 != 0 {
			r.AcctP = fmt.Sprintf("%.0f", acctp.Float64)
		}
		r.Regimen = trimString(regimen)
		r.FechaCreacion = strings.TrimSpace(fechaCreacion.String)
		if descuento.Valid {
			r.Descuento = descuento.Float64
		}
		if creditlmt.Valid {
			r.CreditLmt = creditlmt.Float64
		}

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("CUST rows iteration error: %w", err)
	}
	return records, maxVersion, nil
}

// QueryAllCust fetches all CUST records (first sync / full reset).
// Returns records and the max Version seen.
func (c *Client) QueryAllCust() ([]CustRecord, int64, error) {
	if c.db == nil {
		return nil, 0, fmt.Errorf("database not connected")
	}
	records, maxVersion, err := c.queryCust(0)
	if err != nil {
		return nil, 0, err
	}
	c.logger.Info("CUST full query completed", "count", len(records), "max_version", maxVersion)
	return records, maxVersion, nil
}

// QueryCustSince fetches only CUST records with Version > lastVersion.
// Returns records and the new max Version (caller should persist this).
func (c *Client) QueryCustSince(lastVersion int64) ([]CustRecord, int64, error) {
	if c.db == nil {
		return nil, 0, fmt.Errorf("database not connected")
	}
	records, maxVersion, err := c.queryCust(lastVersion)
	if err != nil {
		return nil, 0, err
	}
	c.logger.Info("CUST incremental query completed",
		"last_version", lastVersion, "count", len(records), "max_version", maxVersion)
	return records, maxVersion, nil
}

// QueryShipToByIDN fetches SHIPTO records for the given ID_N values.
// If idns is empty, returns all SHIPTO records (used on first sync).
// Chunks requests to stay within Firebird's IN-list limit (~1500).
func (c *Client) QueryShipToByIDN(idns []string) ([]ShipToRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	var all []ShipToRecord
	if len(idns) == 0 {
		// Full sync — no filter
		return c.queryShipTo("", nil)
	}

	const chunkSize = 500
	for i := 0; i < len(idns); i += chunkSize {
		end := i + chunkSize
		if end > len(idns) {
			end = len(idns)
		}
		chunk := idns[i:end]
		placeholders := make([]string, len(chunk))
		args := make([]interface{}, len(chunk))
		for j, id := range chunk {
			placeholders[j] = "?"
			args[j] = id
		}
		where := " WHERE ID_N IN (" + strings.Join(placeholders, ",") + ")"
		batch, err := c.queryShipTo(where, args)
		if err != nil {
			return nil, err
		}
		all = append(all, batch...)
	}
	return all, nil
}

func (c *Client) queryShipTo(where string, args []interface{}) ([]ShipToRecord, error) {
	query := `
		SELECT ID_N, SUCCLIENTE, DESCRIPCION, COMPANY, ADDR1, ADDR2, CITY, DEPARTAMENTO,
			COD_DPTO, COD_MUNICIPIO, PHONE1, EMAIL, PAIS, ZONA, ID_VEND, ESTADO
		FROM SHIPTO` + where + `
		ORDER BY ID_N, SUCCLIENTE`

	rows, err := c.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("SHIPTO query failed: %w", err)
	}
	defer rows.Close()

	var records []ShipToRecord
	for rows.Next() {
		var r ShipToRecord
		var idn, desc, company, addr1, addr2, city, depto sql.NullString
		var codDpto, codMun, phone1, email, pais, estado sql.NullString
		var sucCliente, zona, idVend sql.NullInt64

		err := rows.Scan(
			&idn, &sucCliente, &desc, &company, &addr1, &addr2, &city, &depto,
			&codDpto, &codMun, &phone1, &email, &pais, &zona, &idVend, &estado,
		)
		if err != nil {
			return nil, fmt.Errorf("SHIPTO row scan failed: %w", err)
		}

		r.IDN = trimString(idn)
		if sucCliente.Valid {
			r.SucCliente = int(sucCliente.Int64)
		}
		r.Descripcion = trimString(desc)
		r.Company = trimString(company)
		r.Addr1 = trimString(addr1)
		r.Addr2 = trimString(addr2)
		r.City = trimString(city)
		r.Departamento = trimString(depto)
		r.CodDpto = trimString(codDpto)
		r.CodMunicipio = trimString(codMun)
		r.Phone1 = trimString(phone1)
		r.Email = trimString(email)
		r.Pais = trimString(pais)
		if zona.Valid {
			r.Zona = int(zona.Int64)
		}
		if idVend.Valid {
			r.IDVend = int(idVend.Int64)
		}
		r.Estado = trimString(estado)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("SHIPTO rows iteration error: %w", err)
	}
	return records, nil
}

// QueryTributariaByIDN fetches TRIBUTARIA records for the given ID_N values.
// If idns is empty, returns all TRIBUTARIA records (used on first sync).
func (c *Client) QueryTributariaByIDN(idns []string) ([]TributariaRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	var all []TributariaRecord
	if len(idns) == 0 {
		return c.queryTributaria("", nil)
	}

	const chunkSize = 500
	for i := 0; i < len(idns); i += chunkSize {
		end := i + chunkSize
		if end > len(idns) {
			end = len(idns)
		}
		chunk := idns[i:end]
		placeholders := make([]string, len(chunk))
		args := make([]interface{}, len(chunk))
		for j, id := range chunk {
			placeholders[j] = "?"
			args[j] = id
		}
		where := " WHERE ID_N IN (" + strings.Join(placeholders, ",") + ")"
		batch, err := c.queryTributaria(where, args)
		if err != nil {
			return nil, err
		}
		all = append(all, batch...)
	}
	return all, nil
}

func (c *Client) queryTributaria(where string, args []interface{}) ([]TributariaRecord, error) {
	query := `
		SELECT ID_N, COMPANY, TDOC, TIPO_CONTRIBUYENTE,
			PRIMER_NOMBRE, SEGUNDO_NOMBRE, PRIMER_APELLIDO, SEGUNDO_APELLIDO
		FROM TRIBUTARIA` + where + `
		ORDER BY ID_N`

	rows, err := c.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("TRIBUTARIA query failed: %w", err)
	}
	defer rows.Close()

	var records []TributariaRecord
	for rows.Next() {
		var r TributariaRecord
		var idn, company, primerNombre, segundoNombre, primerApe, segundoApe sql.NullString
		var tdoc, tipoContrib sql.NullInt64

		err := rows.Scan(
			&idn, &company, &tdoc, &tipoContrib,
			&primerNombre, &segundoNombre, &primerApe, &segundoApe,
		)
		if err != nil {
			return nil, fmt.Errorf("TRIBUTARIA row scan failed: %w", err)
		}

		r.IDN = trimString(idn)
		r.Company = trimString(company)
		if tdoc.Valid {
			r.Tdoc = int(tdoc.Int64)
		}
		if tipoContrib.Valid {
			r.TipoContribuyente = int(tipoContrib.Int64)
		}
		r.PrimerNombre = trimString(primerNombre)
		r.SegundoNombre = trimString(segundoNombre)
		r.PrimerApellido = trimString(primerApe)
		r.SegundoApellido = trimString(segundoApe)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("TRIBUTARIA rows iteration error: %w", err)
	}
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
