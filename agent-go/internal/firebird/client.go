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
	dsn      string
	db       *sql.DB
	logger   *slog.Logger
	oeColMap map[string]string // detected column names for OE/OEDET variant fields
}

// GLRecord represents a single denormalized General Ledger record
// with all JOINed reference data (account hierarchy, third party, cost centers, etc.).
type GLRecord struct {
	Conteo             int64   `json:"conteo"`
	Fecha              string  `json:"fecha"`
	DueDate            string  `json:"duedate"`
	Invc               string  `json:"invc"`
	Cruce              string  `json:"cruce"`
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
	Acct         float64 `json:"acct"`
	Descripcion  string  `json:"descripcion"`
	Tipo         string  `json:"tipo"`
	Class        string  `json:"class"`
	Nvel         int     `json:"nvel"`
	CdgoTtl      int     `json:"cdgo_ttl"`
	CdgoGrpo     int     `json:"cdgo_grpo"`
	CdgoCnta     int     `json:"cdgo_cnta"`
	CdgoSbCnta   int     `json:"cdgo_sbcnta"`
	DprtmntoCsto string  `json:"dprtmnto_csto"`
	Jbno         string  `json:"jbno"`
	Activo       string  `json:"activo"`
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
	Codigo      string `json:"codigo"`
	Descripcion string `json:"descripcion"`
	Proyecto    string `json:"proyecto"`
	DP          int    `json:"dp"`
	CC          int    `json:"cc"`
}

// OERecord represents an invoice header from the OE table.
type OERecord struct {
	Conteo          int64  `json:"conteo,omitempty"` // global sequential counter (when available)
	Number          int    `json:"number"`
	Tipo            string `json:"tipo"`
	IDSucursal      int    `json:"id_sucursal"`
	TerceroID       string `json:"tercero_id"`
	TerceroNombre   string `json:"tercero_nombre"`
	TerceroRazonSocial string `json:"tercero_razon_social"` // CUST.COMPANY_EXTENDIDO
	Salesman        int    `json:"salesman"`
	SalesmanNombre  string `json:"salesman_nombre"`
	Fecha           string `json:"fecha"`
	DueDate         string `json:"duedate"`
	Periodo         string `json:"periodo"`
	Subtotal        string `json:"subtotal"`
	Costo           string `json:"costo"`
	IVA             string `json:"iva"`
	DescuentoGlobal string `json:"descuento_global"`
	Destotal        string `json:"destotal"`
	Otroscargos     string `json:"otroscargos"`
	Total           string `json:"total"`
	// Retenciones (denormalizadas desde OE y RETEN)
	Porcrtfte         string `json:"porcrtfte"`
	Reteica           string `json:"reteica"`
	PorcentajeReteica string `json:"porcentaje_reteica"`
	Reteiva           string `json:"reteiva"`
	// Tipo de documento (denormalizado desde TIPDOC)
	TipoDescripcion string `json:"tipo_descripcion"`
	Posted          bool   `json:"posted"`
	Closed          bool   `json:"closed"`
	CodMoneda       string `json:"cod_moneda"`
	Comentarios     string `json:"comentarios"`
}

// OEDetRecord represents an invoice line from the OEDET table.
type OEDetRecord struct {
	Conteo            int64  `json:"conteo"`
	FacturaNumber     int    `json:"factura_number"`
	FacturaTipo       string `json:"factura_tipo"`
	FacturaIDSucursal int    `json:"factura_id_sucursal"`
	ItemCodigo        string `json:"item_codigo"`
	ItemDescripcion   string `json:"item_descripcion"`
	Location          string `json:"location"`
	QtyOrder          string `json:"qty_order"`
	QtyShip           string `json:"qty_ship"`
	PrecioUnitario    string `json:"precio_unitario"`
	PrecioExtendido   string `json:"precio_extendido"`
	CostoUnitario     string `json:"costo_unitario"`
	ValorIVA          string `json:"valor_iva"`
	PorcIVA           string `json:"porc_iva"`
	Descuento         string `json:"descuento"`
	TotalDescuento    string `json:"total_descuento"`
	MargenValor       string `json:"margen_valor"`
	MargenPorcentaje  string `json:"margen_porcentaje"`
	ProyectoCodigo      string `json:"proyecto_codigo"`
	DepartamentoCodigo  string `json:"departamento_codigo"`
	CentroCostoCodigo   string `json:"centro_costo_codigo"`
	ActividadCodigo     string `json:"actividad_codigo"`
}

// CARPRORecord represents an accounts receivable/payable movement from CARPRO.
type CARPRORecord struct {
	Conteo         int64  `json:"conteo"`
	TerceroID      string `json:"tercero_id"`
	TerceroNombre  string `json:"tercero_nombre"`
	CuentaContable string `json:"cuenta_contable"`
	Tipo           string `json:"tipo"`
	Batch          int    `json:"batch"`
	Invc           string `json:"invc"`
	Descripcion    string `json:"descripcion"`
	Fecha          string `json:"fecha"`
	DueDate        string `json:"duedate"`
	Periodo        string `json:"periodo"`
	Debito         string `json:"debito"`
	Credito        string `json:"credito"`
	Saldo          string `json:"saldo"`
	Departamento   int    `json:"departamento"`
	CentroCosto    int    `json:"centro_costo"`
	ProyectoCodigo string `json:"proyecto_codigo"`
	TipoCartera    string `json:"tipo_cartera"` // derived: CXC (acct ~13xx) or CXP (acct ~22xx)
}

// ITEMACTRecord represents an inventory movement from the ITEMACT table.
type ITEMACTRecord struct {
	Conteo     int64  `json:"conteo"`
	ItemCodigo string `json:"item_codigo"`
	Location   string `json:"location"`
	TerceroID       string `json:"tercero_id"`
	Tipo            string `json:"tipo"`
	Batch           int    `json:"batch"`
	Fecha           string `json:"fecha"`
	Periodo         string `json:"periodo"`
	Cantidad        string `json:"cantidad"`
	ValorUnitario   string `json:"valor_unitario"`
	CostoPromedio   string `json:"costo_promedio"`
	Total           string `json:"total"`
	Lote            string `json:"lote"`
	Serie           string `json:"serie"`
	LoteVencimiento string `json:"lote_vencimiento"` // "YYYY-MM-DD" or ""
}

// TipdocRecord represents a document type from the TIPDOC table.
// PK: (CLASE, E, S). CLASE is the same value stored in GL.TIPO.
type TipdocRecord struct {
	Clase         string `json:"clase"`
	E             int    `json:"e"`
	S             int    `json:"s"`
	Tipo          string `json:"tipo"`
	Consecutivo   int    `json:"consecutivo"`
	Descripcion   string `json:"descripcion"`
	Sigla         string `json:"sigla"`
	Operar        string `json:"operar"`
	EnviaFacElect string `json:"enviafacelect"`
	PrefijoDIAN   string `json:"prefijo_dian"`
}

// TaxAuthRecord represents a tax authority entry from the TAXAUTH table.
type TaxAuthRecord struct {
	Codigo    int     `json:"codigo"`
	Authority string  `json:"authority"`
	Rate      float64 `json:"rate"`
}

// ItemRecord represents a product/item from the ITEM table.
// Only core fields are synced to avoid complexity with the 295-column table.
type ItemRecord struct {
	Item             string  `json:"item"`
	Descripcion      string  `json:"descripcion"`
	Class            string  `json:"class"`
	Grupo            string  `json:"grupo"`
	Price            float64 `json:"price"`
	UofmSales        string  `json:"uofmsales"`
	ImpoVenta        string  `json:"impoventa"`
	// Clasificación (desde ITEM + JOINs a LINEA/GRUPO/SUBGRUPO)
	Reffabrica       string  `json:"reffabrica"`
	LineaCodigo      string  `json:"linea_codigo"`
	LineaDescripcion string  `json:"linea_descripcion"`
	GrupoDescripcion string  `json:"grupo_descripcion"`
	SubgrupoDescripcion string `json:"subgrupo_descripcion"`
}

// VendedorRecord represents a salesperson from the VENDEDOR table.
type VendedorRecord struct {
	Codigo   int    `json:"codigo"`   // IDVEND (PK)
	Nombre   string `json:"nombre"`   // NOMBRE
	Telefono string `json:"telefono"` // TELEFONO
	Activo   bool   `json:"activo"`   // ACTIVO ('True'/'False')
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

	// Detect variant column names for OE/OEDET once at connect time.
	c.oeColMap = c.detectOEColumns()
	c.logger.Info("OE variant columns detected", "cols", c.oeColMap)

	return nil
}

// detectColumn returns the first matching column name found in the given Firebird table,
// or "" if none of the candidates exist.
func (c *Client) detectColumn(tableName string, candidates []string) string {
	for _, col := range candidates {
		row := c.db.QueryRow(
			`SELECT COUNT(*) FROM RDB$RELATION_FIELDS
			 WHERE RDB$RELATION_NAME = ? AND TRIM(RDB$FIELD_NAME) = ?`,
			tableName, col,
		)
		var count int
		if err := row.Scan(&count); err == nil && count > 0 {
			return col
		}
	}
	return ""
}

// detectOEColumns queries the Firebird system catalog to find the actual names
// of columns that differ across Saiopen versions in OE, OEDET and ITEM tables.
// Each key is a logical name; value is the real column name (or "" if not found).
func (c *Client) detectOEColumns() map[string]string {
	// OE columns (queried against the OE table)
	oeVariants := map[string][]string{
		"sucursal":      {"ID_SUCURSAL", "IDSUCURSAL", "IDSUC", "SUCURSAL", "ID_SUC", "BRANCH"},
		"salesman":      {"SALESMAN", "SLSMN", "SLSMAN", "VENDEDOR", "ID_VEND"},
		"period":        {"PERIOD", "PERIODO", "PER", "PERIODOOE"},
		"duedate":       {"DUEDATE", "FECHAVEN", "FECHA_VEN", "FECVEN"},
		"subtotal":      {"SUBTOTAL", "SUB_TOTAL", "BASE"},
		"costo":         {"COSTO", "COST", "COSTOOE"},
		"iva":           {"IVA", "IMPUESTO", "TAX"},
		"disc1":         {"DISC1", "DESCUENTO", "DISC"},
		"posted":        {"POSTED", "CONTABILIZADO", "POST"},
		"closed":        {"CLOSED", "CERRADO", "CLOSE"},
		"moneda":        {"CODMONEDA", "COD_MONEDA", "MONEDA", "CURRENCY"},
		"comment":       {"COMMENT1", "COMENTARIO", "NOTAS", "COMMENT"},
		// Retenciones
		"oe_porcrtfte":   {"PORCRTFTE", "PORC_RTFTE"},
		"oe_disc2":       {"DISC2"},
		"oe_disc3":       {"DISC3"},
		"oe_destotal":    {"DESTOTAL", "DESCUENTO_TOTAL"},
		"oe_otroscargos": {"OTROSCARGOS", "OTROS_CARGOS", "OCARGOS"},
		"oe_rfaplicada2": {"RFAPLICADA2", "RF_APLICADA2"},  // FK → RETEN join
		"oe_empresa":     {"ID_EMPRESA", "EMPRESA"},          // FK → TIPDOC join
	}

	result := make(map[string]string)
	for key, candidates := range oeVariants {
		result[key] = c.detectColumn("OE", candidates)
	}

	// OE global sequential counter (exists in most Saiopen versions).
	// If present, use it as watermark instead of NUMBER (which is per document type).
	result["oe_conteo"] = c.detectColumn("OE", []string{"CONTEO", "CONT", "SEQ", "SECUENCIA"})

	// CUST — nombre extendido del tercero (razón social)
	result["cust_company_extendido"] = c.detectColumn("CUST", []string{"COMPANY_EXTENDIDO", "NOMBCOMEX", "RAZON_SOCIAL"})

	// TIPDOC — claves de JOIN (E, S, CLASE) + descripción del tipo
	result["tipdoc_e"]     = c.detectColumn("TIPDOC", []string{"E", "ID_EMPRESA", "EMPRESA"})
	result["tipdoc_s"]     = c.detectColumn("TIPDOC", []string{"S", "ID_SUCURSAL", "SUCURSAL"})
	result["tipdoc_clase"] = c.detectColumn("TIPDOC", []string{"CLASE", "TIPO", "CODTIPO"})
	result["tipdoc_desc"]  = c.detectColumn("TIPDOC", []string{"DESCRIPCION", "DESCRIPN", "NOMBRE"})

	// RETEN — clave de JOIN + porcentaje de retención ICA
	result["reten_tipo"]       = c.detectColumn("RETEN", []string{"TIPO", "COD_RETEN", "CODTIPO"})
	result["reten_porcentaje"] = c.detectColumn("RETEN", []string{"PORCENTAJE", "PORC", "PCT"})

	// Item code column candidates (shared across OEDET, ITEMACT, and ITEM tables).
	// "ITEM" is the most common PK/FK name in Saiopen 2.x+; listed first so it wins quickly.
	itemCandidates := []string{"ITEM", "ITEMNO", "ITEM_NO", "COD_ITEM", "CODIGO", "ID_ITEM"}
	// ITEM table may use additional key names in some Saiopen versions.
	itemPKCandidates := append(itemCandidates, "CLAVE", "NUMITEM", "CODIGO_ITEM", "ITEM_CODE", "CODIGOITEM")
	result["oedet_itemno"]   = c.detectColumn("OEDET",   itemCandidates)
	// ITEMACT may use additional item code names in some Saiopen versions.
	itemactItemCandidates := append(itemCandidates, "CODITEM", "COD_ITEM2", "REFERENCIA", "COD_PROD", "PRODUCTO")
	result["itemact_itemno"] = c.detectColumn("ITEMACT", itemactItemCandidates)
	result["item_itemno"]   = c.detectColumn("ITEM",    itemPKCandidates)

	// ITEM: description column
	result["item_desc"] = c.detectColumn("ITEM", []string{"DESCRIPCION", "DESCRIPN", "DESC", "NOMBRE", "DESCRIP"})

	// OEDET: other potentially-variant columns
	result["oedet_period"] = c.detectColumn("OEDET", []string{"PERIOD", "PERIODO", "PER"})
	result["oedet_price"]  = c.detectColumn("OEDET", []string{"PRICE", "PRECIO", "UNITPRICE"})
	result["oedet_extended"] = c.detectColumn("OEDET", []string{"EXTEND", "EXTENDED", "EXTENDIDO", "TOTAL", "EXTENDED_PRICE"})
	result["oedet_cost"]   = c.detectColumn("OEDET", []string{"COST", "COSTO", "COSTODET"})
	result["oedet_ivalr"]  = c.detectColumn("OEDET", []string{"IVALR", "VLR_IVA", "IVA", "IMPUESTO", "TAX"})
	result["oedet_ivapct"] = c.detectColumn("OEDET", []string{"IVAPCT", "IVAPCT", "PORC_IVA", "TAXRATE"})
	result["oedet_disc1"]  = c.detectColumn("OEDET", []string{"DISC1", "DESCUENTO", "DISC"})
	result["oedet_totaldct"]  = c.detectColumn("OEDET", []string{"TOTALDCT", "TOTAL_DCT", "TOTALDESCUENTO"})
	result["oedet_proyecto"]  = c.detectColumn("OEDET", []string{"PROYECTO", "CODPROYECTO", "COD_PROYECTO", "PROJECT"})
	result["oedet_dpto"]      = c.detectColumn("OEDET", []string{"DPTO", "DEPARTAMENTO", "DEPTO", "COD_DEPTO"})
	result["oedet_ccost"]     = c.detectColumn("OEDET", []string{"CCOST", "CENTRO_COSTO", "CENTCOST", "CC"})
	result["oedet_actividad"] = c.detectColumn("OEDET", []string{"ACTIVIDAD", "ACT", "COD_ACT", "CODACTIVIDAD"})
	result["oedet_location"] = c.detectColumn("OEDET", []string{"LOCATION", "BODEGA", "UBICACION", "LOC"})
	result["oedet_qtyorder"] = c.detectColumn("OEDET", []string{"QTYORDER", "QTY_ORDER", "CANTPEDIDA", "CANT_PED"})
	result["oedet_qtyship"]  = c.detectColumn("OEDET", []string{"QTYSHIP", "QTY_SHIP", "CANTDESP", "CANT_DES"})

	// ITEM — clasificación de producto
	result["item_reffabrica"] = c.detectColumn("ITEM", []string{"REFFABRICA", "REF_FABRICA", "REFERENCIA"})
	result["item_class"]      = c.detectColumn("ITEM", []string{"CLASS", "CLASE"})
	result["item_itemmstr"]   = c.detectColumn("ITEM", []string{"ITEMMSTR", "LINEA", "CODLINEA"})
	result["item_grupo"]      = c.detectColumn("ITEM", []string{"GRUPO", "CODGRUPO", "COD_GRUPO"})

	// LINEA — tabla maestra de líneas de producto
	result["linea_codlinea"] = c.detectColumn("LINEA", []string{"CODLINEA", "COD_LINEA"})
	result["linea_desc"]     = c.detectColumn("LINEA", []string{"DESCLINEA", "DESCRIPCION", "NOMBRE"})

	// GRUPO — tabla maestra de grupos
	result["grupo_codlinea"] = c.detectColumn("GRUPO", []string{"CODLINEA", "COD_LINEA"})
	result["grupo_codgrupo"] = c.detectColumn("GRUPO", []string{"CODGRUPO", "COD_GRUPO"})
	result["grupo_desc"]     = c.detectColumn("GRUPO", []string{"DESCGRUPO", "DESCRIPCION", "NOMBRE"})

	// SUBGRUPO — tabla maestra de subgrupos
	result["subgrupo_codsubgrupo"] = c.detectColumn("SUBGRUPO", []string{"CODSUBGRUPO", "COD_SUBGRUPO"})
	result["subgrupo_codgrupo"]    = c.detectColumn("SUBGRUPO", []string{"CODGRUPO", "COD_GRUPO"})
	result["subgrupo_codlinea"]    = c.detectColumn("SUBGRUPO", []string{"CODLINEA", "COD_LINEA"})
	result["subgrupo_desc"]        = c.detectColumn("SUBGRUPO", []string{"DESCSUBGRUPO", "DESCRIPCION", "NOMBRE"})

	// ITEMACT: all potentially-variant columns
	result["itemact_period"]     = c.detectColumn("ITEMACT", []string{"PERIOD", "PERIODO", "PER"})
	result["itemact_location"]   = c.detectColumn("ITEMACT", []string{"LOCATION", "BODEGA", "UBICACION", "LOC"})
	result["itemact_idn"]        = c.detectColumn("ITEMACT", []string{"ID_N", "IDN", "TERCERO", "ID_TERCERO", "NUMER"})
	result["itemact_batch"]      = c.detectColumn("ITEMACT", []string{"BATCH", "LOTE_INT", "LOTEINT", "NUMBATCH"})
	result["itemact_qty"]        = c.detectColumn("ITEMACT", []string{"QTY", "CANTIDAD", "CANT", "UNIDADES"})
	result["itemact_cost"]       = c.detectColumn("ITEMACT", []string{"VALUNIT", "COST", "COSTO", "PRECIO_COSTO"})
	result["itemact_costop"]     = c.detectColumn("ITEMACT", []string{"COSTOP", "COST_PROM", "COSTO_PROM", "COSTPEPS"})
	result["itemact_total"]      = c.detectColumn("ITEMACT", []string{"TOTPARCIAL", "TOTAL", "VALOR", "IMPORTE"})
	result["itemact_lote"]       = c.detectColumn("ITEMACT", []string{"LOTE", "LOT", "NUM_LOTE"})
	result["itemact_serie"]      = c.detectColumn("ITEMACT", []string{"NOSERIE", "SERIE", "SERIAL", "NUM_SERIE"})
	result["itemact_lote_ven"]   = c.detectColumn("ITEMACT", []string{"LOTEFVENCE", "LOTE_VEN", "VENCIMIENTO", "FECHA_VEN", "LOTE_VENCIMIENTO"})

	return result
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
		SELECT G.CONTEO, G.FECHA, G.DUEDATE, G.INVC, G.CRUCE,
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
		var invc, cruce sql.NullString
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
			&r.Conteo, &fecha, &duedate, &invc, &cruce,
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
		r.Cruce = trimString(cruce)
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

// QueryAllTipdoc fetches all document types from the TIPDOC table.
// PK: (CLASE, E, S). Only fetches columns needed for Django sync.
func (c *Client) QueryAllTipdoc() ([]TipdocRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT CLASE, E, S, TIPO, CONSECUTIVO, DESCRIPCION, SIGLA,
		       OPERAR, ENVIAFACELECT, PREFIJO_DIAN
		FROM TIPDOC
		ORDER BY CLASE, E, S`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("TIPDOC query failed: %w", err)
	}
	defer rows.Close()

	var records []TipdocRecord
	for rows.Next() {
		var r TipdocRecord
		var clase, tipo, desc, sigla, operar, enviaFacElect, prefijoDIAN sql.NullString
		var e, s, consecutivo sql.NullInt64

		err := rows.Scan(
			&clase, &e, &s, &tipo, &consecutivo, &desc,
			&sigla, &operar, &enviaFacElect, &prefijoDIAN,
		)
		if err != nil {
			return nil, fmt.Errorf("TIPDOC row scan failed: %w", err)
		}

		r.Clase = trimString(clase)
		if e.Valid {
			r.E = int(e.Int64)
		}
		if s.Valid {
			r.S = int(s.Int64)
		}
		r.Tipo = trimString(tipo)
		if consecutivo.Valid {
			r.Consecutivo = int(consecutivo.Int64)
		}
		r.Descripcion = trimString(desc)
		r.Sigla = trimString(sigla)
		r.Operar = trimString(operar)
		r.EnviaFacElect = trimString(enviaFacElect)
		r.PrefijoDIAN = trimString(prefijoDIAN)

		records = append(records, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("TIPDOC rows iteration error: %w", err)
	}

	c.logger.Info("TIPDOC query completed", "count", len(records))
	return records, nil
}

// QueryOETipos returns all document type codes (CLASE) defined in TIPDOC.
// OE.TIPO = TIPDOC.CLASE, so this gives the complete list of types that can
// appear in OE. Querying TIPDOC ensures new types are picked up automatically.
func (c *Client) QueryOETipos() ([]string, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}
	rows, err := c.db.Query(`SELECT DISTINCT CLASE FROM TIPDOC WHERE CLASE IS NOT NULL ORDER BY CLASE`)
	if err != nil {
		return nil, fmt.Errorf("TIPDOC CLASE query failed: %w", err)
	}
	defer rows.Close()
	var tipos []string
	for rows.Next() {
		var clase string
		if err := rows.Scan(&clase); err != nil {
			return nil, fmt.Errorf("TIPDOC CLASE scan failed: %w", err)
		}
		tipos = append(tipos, strings.TrimSpace(clase))
	}
	return tipos, rows.Err()
}

// QueryOEIncremental fetches OE (invoice header) records for a specific document type (tipo),
// with NUMBER > lastNumber, ordered by NUMBER ASC.
//
// Watermark: NUMBER is per document type — each TIPDOC.CLASE sequence is independent.
// The caller iterates over all tipos (from QueryOETipos) and maintains a separate
// watermark per tipo in LastOEWatermarks.
func (c *Client) QueryOEIncremental(tipo string, lastNumber int64, batchSize int) ([]OERecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	// Build SELECT dynamically — every optional column is only included if detected.
	type optCol struct {
		key   string
		alias string
		table string
	}
	optCols := []optCol{
		{"sucursal",      "SUCURSAL",   "O"},
		{"salesman",      "SALESMAN",   "O"},
		{"duedate",       "DUEDATE",    "O"},
		{"period",        "PERIOD",     "O"},
		{"subtotal",      "SUBTOTAL",   "O"},
		{"costo",         "COSTO",      "O"},
		{"iva",           "IVA",        "O"},
		{"disc1",         "DISC1",      "O"},
		{"posted",        "POSTED",     "O"},
		{"closed",        "CLOSED",     "O"},
		{"moneda",        "CODMONEDA",  "O"},
		{"comment",       "COMMENT1",   "O"},
		// Retenciones y cargos adicionales
		{"oe_porcrtfte",   "PORCRTFTE",   "O"},
		{"oe_disc2",       "DISC2",       "O"},
		{"oe_disc3",       "DISC3",       "O"},
		{"oe_destotal",    "DESTOTAL",    "O"},
		{"oe_otroscargos", "OTROSCARGOS", "O"},
	}

	var extraSelect string
	for _, oc := range optCols {
		if col := c.oeColMap[oc.key]; col != "" {
			extraSelect += fmt.Sprintf(", %s.%s AS %s", oc.table, col, oc.alias)
		}
	}

	// JOIN VENDEDOR to resolve salesperson name when the column is present.
	salesmanCol := c.oeColMap["salesman"]
	var vendedorJoin, salesmanNombreSelect string
	if salesmanCol != "" {
		vendedorJoin = fmt.Sprintf("\n\t\t\tLEFT JOIN VENDEDOR V ON V.IDVEND = O.%s", salesmanCol)
		salesmanNombreSelect = ", V.NOMBRE AS SALESMAN_NOMBRE"
	}

	// CUST.COMPANY_EXTENDIDO — nombre extendido del tercero (JOIN a CUST ya existe).
	companyExtCol := c.oeColMap["cust_company_extendido"]
	var companyExtSelect string
	if companyExtCol != "" {
		companyExtSelect = fmt.Sprintf(", C.%s AS COMPANY_EXTENDIDO", companyExtCol)
	}

	// TIPDOC JOIN — descripción del tipo de documento (condicional).
	empresaCol   := c.oeColMap["oe_empresa"]
	tipdocECol   := c.oeColMap["tipdoc_e"]
	tipdocSCol   := c.oeColMap["tipdoc_s"]
	tipdocClsCol := c.oeColMap["tipdoc_clase"]
	tipdocDescCol := c.oeColMap["tipdoc_desc"]
	sucursalOECol := c.oeColMap["sucursal"]
	tipdocActive := empresaCol != "" && tipdocECol != "" && tipdocSCol != "" &&
		tipdocClsCol != "" && tipdocDescCol != "" && sucursalOECol != ""
	var tipdocJoin, tipdocSelect string
	if tipdocActive {
		tipdocJoin = fmt.Sprintf(
			"\n\t\t\tLEFT JOIN TIPDOC T ON O.%s=T.%s AND O.%s=T.%s AND O.TIPO=T.%s",
			empresaCol, tipdocECol, sucursalOECol, tipdocSCol, tipdocClsCol)
		tipdocSelect = fmt.Sprintf(", T.%s AS TIPDOC_DESC", tipdocDescCol)
	}

	// RETEN JOIN — porcentaje de reteica (condicional).
	rfaplicada2Col  := c.oeColMap["oe_rfaplicada2"]
	retenTipoCol    := c.oeColMap["reten_tipo"]
	retenPorcCol    := c.oeColMap["reten_porcentaje"]
	retenActive := rfaplicada2Col != "" && retenTipoCol != "" && retenPorcCol != ""
	var retenJoin, retenSelect string
	if retenActive {
		retenJoin = fmt.Sprintf(
			"\n\t\t\tLEFT JOIN RETEN R ON O.%s=R.%s", rfaplicada2Col, retenTipoCol)
		retenSelect = fmt.Sprintf(", R.%s AS RETEN_PORC", retenPorcCol)
	}

	query := fmt.Sprintf(`
		SELECT O.NUMBER, O.TIPO, O.ID_N, C.COMPANY AS TERCERO_NOMBRE, O.FECHA, O.TOTAL%s%s%s%s%s
		FROM OE O
		LEFT JOIN CUST C ON C.ID_N = O.ID_N%s%s%s
		WHERE O.TIPO = ? AND O.NUMBER > ?
		ORDER BY O.NUMBER ASC
		ROWS 1 TO ?`,
		extraSelect, salesmanNombreSelect, companyExtSelect, tipdocSelect, retenSelect,
		vendedorJoin, tipdocJoin, retenJoin)

	rows, err := c.db.Query(query, tipo, lastNumber, batchSize)
	if err != nil {
		return nil, fmt.Errorf("OE query failed (tipo=%s): %w", tipo, err)
	}
	defer rows.Close()

	var records []OERecord
	for rows.Next() {
		var r OERecord
		var tipoVal, idN, terceroNombre sql.NullString
		var fecha sql.NullTime
		var total sql.NullFloat64

		// Optional vars
		var sucursal, salesman sql.NullInt64
		var duedate sql.NullTime
		var period, posted, closed, codMoneda, comment sql.NullString
		var subtotal, costo, iva, disc1 sql.NullFloat64
		var porcrtfte, disc2, disc3, destotal, otroscargos sql.NullFloat64

		var salesmanNombre, companyExt, tipdocDesc sql.NullString
		var retenPorc sql.NullFloat64

		scanArgs := []interface{}{&r.Number, &tipoVal, &idN, &terceroNombre, &fecha, &total}
		for _, oc := range optCols {
			if c.oeColMap[oc.key] == "" {
				continue
			}
			switch oc.key {
			case "sucursal":
				scanArgs = append(scanArgs, &sucursal)
			case "salesman":
				scanArgs = append(scanArgs, &salesman)
			case "duedate":
				scanArgs = append(scanArgs, &duedate)
			case "period":
				scanArgs = append(scanArgs, &period)
			case "subtotal":
				scanArgs = append(scanArgs, &subtotal)
			case "costo":
				scanArgs = append(scanArgs, &costo)
			case "iva":
				scanArgs = append(scanArgs, &iva)
			case "disc1":
				scanArgs = append(scanArgs, &disc1)
			case "posted":
				scanArgs = append(scanArgs, &posted)
			case "closed":
				scanArgs = append(scanArgs, &closed)
			case "moneda":
				scanArgs = append(scanArgs, &codMoneda)
			case "comment":
				scanArgs = append(scanArgs, &comment)
			case "oe_porcrtfte":
				scanArgs = append(scanArgs, &porcrtfte)
			case "oe_disc2":
				scanArgs = append(scanArgs, &disc2)
			case "oe_disc3":
				scanArgs = append(scanArgs, &disc3)
			case "oe_destotal":
				scanArgs = append(scanArgs, &destotal)
			case "oe_otroscargos":
				scanArgs = append(scanArgs, &otroscargos)
			}
		}
		// Append trailing scan vars in SELECT order.
		if salesmanCol != "" {
			scanArgs = append(scanArgs, &salesmanNombre)
		}
		if companyExtCol != "" {
			scanArgs = append(scanArgs, &companyExt)
		}
		if tipdocActive {
			scanArgs = append(scanArgs, &tipdocDesc)
		}
		if retenActive {
			scanArgs = append(scanArgs, &retenPorc)
		}

		if err := rows.Scan(scanArgs...); err != nil {
			return nil, fmt.Errorf("OE row scan failed (tipo=%s): %w", tipo, err)
		}

		r.Tipo = trimString(tipoVal)
		if sucursal.Valid {
			r.IDSucursal = int(sucursal.Int64)
		} else {
			r.IDSucursal = 1
		}
		r.TerceroID = trimString(idN)
		r.TerceroNombre = trimString(terceroNombre)
		r.TerceroRazonSocial = trimString(companyExt)
		if salesman.Valid {
			r.Salesman = int(salesman.Int64)
		}
		r.SalesmanNombre = trimString(salesmanNombre)
		if fecha.Valid {
			r.Fecha = fecha.Time.Format("2006-01-02")
		}
		if duedate.Valid {
			r.DueDate = duedate.Time.Format("2006-01-02")
		}
		r.Periodo = trimString(period)
		// Fallback: si PERIOD no está disponible en OE, calcularlo desde FECHA (formato YYYY-MM)
		if r.Periodo == "" && r.Fecha != "" && len(r.Fecha) >= 7 {
			r.Periodo = r.Fecha[:7]
		}
		r.Subtotal        = formatMoney(subtotal)
		r.Costo           = formatMoney(costo)
		r.IVA             = formatMoney(iva)
		r.DescuentoGlobal = formatMoney(disc1)
		r.Destotal        = formatMoney(destotal)
		r.Otroscargos     = formatMoney(otroscargos)
		r.Total           = formatMoney(total)
		r.Porcrtfte        = formatMoney(porcrtfte)
		r.Reteica          = formatMoney(disc2)
		r.PorcentajeReteica = formatMoney(retenPorc)
		r.Reteiva          = formatMoney(disc3)
		r.TipoDescripcion  = trimString(tipdocDesc)
		r.Posted = trimString(posted) == "Y"
		r.Closed = trimString(closed) == "Y"
		r.CodMoneda = trimString(codMoneda)
		if r.CodMoneda == "" {
			r.CodMoneda = "COP"
		}
		r.Comentarios = trimString(comment)

		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("OE rows iteration error (tipo=%s): %w", tipo, err)
	}
	c.logger.Debug("OE query returned records", "tipo", tipo, "count", len(records))
	return records, nil
}

// QueryOEDetIncremental fetches OEDET (invoice line) records for a specific document type (tipo),
// where NUMBER > lastNumber, ordered by NUMBER ASC, CONTEO ASC.
// OEDET.CONTEO is the line sequence within a single invoice (1, 2, 3…), NOT a global counter.
// NUMBER (FK to OE header) is the correct incremental key, and it is per document type —
// so a separate watermark per tipo must be maintained (same as OE).
// All other column names are resolved dynamically from oeColMap.
// Classification fields (linea/grupo/subgrupo) are denormalized here to avoid extra JOINs
// in the Django BI layer — their master tables are conditionally joined only when detected.
func (c *Client) QueryOEDetIncremental(tipo string, lastNumber int64, batchSize int) ([]OEDetRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	// Resolve detected column names (fall back to empty string = omit from SELECT).
	sucursalCol   := c.oeColMap["sucursal"]
	itemnoDetCol  := c.oeColMap["oedet_itemno"]  // item code col in OEDET
	itemnoItemCol := c.oeColMap["item_itemno"]   // item code col in ITEM (for JOIN)
	itemDescCol   := c.oeColMap["item_desc"]
	locationCol   := c.oeColMap["oedet_location"]
	qtyOrderCol   := c.oeColMap["oedet_qtyorder"]
	qtyShipCol    := c.oeColMap["oedet_qtyship"]
	priceCol      := c.oeColMap["oedet_price"]
	extendedCol   := c.oeColMap["oedet_extended"]
	costCol       := c.oeColMap["oedet_cost"]
	ivalrCol      := c.oeColMap["oedet_ivalr"]
	ivapctCol     := c.oeColMap["oedet_ivapct"]
	disc1Col      := c.oeColMap["oedet_disc1"]
	totaldctCol    := c.oeColMap["oedet_totaldct"]
	proyectoCol    := c.oeColMap["oedet_proyecto"]
	dptoCol        := c.oeColMap["oedet_dpto"]
	ccostCol       := c.oeColMap["oedet_ccost"]
	actividadCol   := c.oeColMap["oedet_actividad"]
	// JOIN to ITEM is only possible when both sides have a matching item code column.
	joinActive := itemnoDetCol != "" && itemnoItemCol != ""

	// itemdesc lives on table I — only when JOIN is active.
	activeItemDescCol := itemDescCol
	if !joinActive {
		activeItemDescCol = ""
	}

	// Build optional SELECT expressions (columns on D or I only).
	type optDet struct{ key, col, alias, tbl string }
	opts := []optDet{
		{"sucursal",   sucursalCol,          "SUCURSAL",   "D"},
		{"itemno",     itemnoDetCol,          "ITEMNO",     "D"},
		{"itemdesc",   activeItemDescCol,     "ITEMDESC",   "I"},
		{"location",   locationCol,           "LOCATION",   "D"},
		{"qtyorder",   qtyOrderCol,           "QTYORDER",   "D"},
		{"qtyship",    qtyShipCol,            "QTYSHIP",    "D"},
		{"price",      priceCol,              "PRICE",      "D"},
		{"extended",   extendedCol,           "EXTENDED",   "D"},
		{"cost",       costCol,               "COST",       "D"},
		{"ivalr",      ivalrCol,              "IVALR",      "D"},
		{"ivapct",     ivapctCol,             "IVAPCT",     "D"},
		{"disc1",      disc1Col,              "DISC1",      "D"},
		{"totaldct",   totaldctCol,           "TOTALDCT",   "D"},
		{"proyecto",   proyectoCol,           "PROYECTO",   "D"},
		{"dpto",       dptoCol,               "DPTO",       "D"},
		{"ccost",      ccostCol,              "CCOST",      "D"},
		{"actividad",  actividadCol,          "ACTIVIDAD",  "D"},
	}

	var extraSelect string
	for _, o := range opts {
		if o.col != "" {
			extraSelect += fmt.Sprintf(", %s.%s AS %s", o.tbl, o.col, o.alias)
		}
	}

	// JOIN to ITEM — only for description. Classification lives in CrmProducto (sync'd via ITEM sync).
	var itemJoin string
	if joinActive {
		itemJoin = fmt.Sprintf("LEFT JOIN ITEM I ON I.%s = D.%s", itemnoItemCol, itemnoDetCol)
	}

	query := fmt.Sprintf(`
		SELECT D.NUMBER, D.CONTEO, D.TIPO%s
		FROM OEDET D %s
		WHERE D.TIPO = ? AND D.NUMBER > ?
		ORDER BY D.NUMBER ASC, D.CONTEO ASC
		ROWS 1 TO ?`,
		extraSelect, itemJoin)

	rows, err := c.db.Query(query, tipo, lastNumber, batchSize)
	if err != nil {
		return nil, fmt.Errorf("OEDET query failed (tipo=%s): %w", tipo, err)
	}
	defer rows.Close()

	var records []OEDetRecord
	for rows.Next() {
		var r OEDetRecord
		var tipoVal sql.NullString
		var sucursal sql.NullInt64
		var itemno, itemDesc, location, proyecto sql.NullString
		var dptoVal, ccostVal, actividadVal sql.NullString
		var qtyOrder, qtyShip, price, extended, cost sql.NullFloat64
		var ivalr, ivapct, disc1, totalDct sql.NullFloat64

		scanArgs := []interface{}{&r.FacturaNumber, &r.Conteo, &tipoVal}
		for _, o := range opts {
			if o.col == "" {
				continue
			}
			switch o.key {
			case "sucursal":
				scanArgs = append(scanArgs, &sucursal)
			case "itemno":
				scanArgs = append(scanArgs, &itemno)
			case "itemdesc":
				scanArgs = append(scanArgs, &itemDesc)
			case "location":
				scanArgs = append(scanArgs, &location)
			case "qtyorder":
				scanArgs = append(scanArgs, &qtyOrder)
			case "qtyship":
				scanArgs = append(scanArgs, &qtyShip)
			case "price":
				scanArgs = append(scanArgs, &price)
			case "extended":
				scanArgs = append(scanArgs, &extended)
			case "cost":
				scanArgs = append(scanArgs, &cost)
			case "ivalr":
				scanArgs = append(scanArgs, &ivalr)
			case "ivapct":
				scanArgs = append(scanArgs, &ivapct)
			case "disc1":
				scanArgs = append(scanArgs, &disc1)
			case "totaldct":
				scanArgs = append(scanArgs, &totalDct)
			case "proyecto":
				scanArgs = append(scanArgs, &proyecto)
			case "dpto":
				scanArgs = append(scanArgs, &dptoVal)
			case "ccost":
				scanArgs = append(scanArgs, &ccostVal)
			case "actividad":
				scanArgs = append(scanArgs, &actividadVal)
			}
		}

		if err := rows.Scan(scanArgs...); err != nil {
			return nil, fmt.Errorf("OEDET row scan failed: %w", err)
		}

		r.FacturaTipo = trimString(tipoVal)
		if sucursal.Valid {
			r.FacturaIDSucursal = int(sucursal.Int64)
		} else {
			r.FacturaIDSucursal = 1
		}
		r.ItemCodigo      = trimString(itemno)
		r.ItemDescripcion = trimString(itemDesc)
		r.Location        = trimString(location)
		r.QtyOrder        = formatQty(qtyOrder)
		r.QtyShip         = formatQty(qtyShip)
		r.PrecioUnitario  = formatQty(price)
		r.PrecioExtendido = formatMoney(extended)
		r.CostoUnitario   = formatQty(cost)
		r.ValorIVA        = formatMoney(ivalr)
		r.PorcIVA         = formatMoney(ivapct)
		r.Descuento       = formatMoney(disc1)
		r.TotalDescuento  = formatMoney(totalDct)
		r.ProyectoCodigo     = trimString(proyecto)
		r.DepartamentoCodigo = trimString(dptoVal)
		r.CentroCostoCodigo  = trimString(ccostVal)
		r.ActividadCodigo    = trimString(actividadVal)
		// Margin fields are not stored in OEDET — default to "0" to avoid
		// Decimal parse errors on the Django side.
		r.MargenValor = "0"
		r.MargenPorcentaje = "0"

		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("OEDET rows iteration error: %w", err)
	}
	c.logger.Debug("OEDET query returned records", "count", len(records))
	return records, nil
}

// QueryCARPROIncremental fetches CARPRO (A/R + A/P movements) records with CONTEO > lastConteo.
func (c *Client) QueryCARPROIncremental(lastConteo int64, batchSize int) ([]CARPRORecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `
		SELECT CP.CONTEO, CP.ID_N, C.COMPANY AS TERCERO_NOMBRE,
			CP.ACCT, CP.TIPO, CP.BATCH, CP.INVC,
			CP.DESCRIPCION, CP.FECHA, CP.DUEDATE, CP.PERIOD,
			CP.DEBIT, CP.CREDIT, CP.SALDO,
			CP.DEPTO, CP.CCOST, CP.PROYECTO
		FROM CARPRO CP
		LEFT JOIN CUST C ON C.ID_N = CP.ID_N
		WHERE CP.CONTEO > ?
		ORDER BY CP.CONTEO ASC
		ROWS 1 TO ?`

	rows, err := c.db.Query(query, lastConteo, batchSize)
	if err != nil {
		return nil, fmt.Errorf("CARPRO query failed: %w", err)
	}
	defer rows.Close()

	var records []CARPRORecord
	for rows.Next() {
		var r CARPRORecord
		var idN, terceroNombre, tipo, invc, desc, period, proyecto sql.NullString
		var acct sql.NullFloat64
		var batch, depto, ccost sql.NullInt64
		var fecha, duedate sql.NullTime
		var debit, credit, saldo sql.NullFloat64

		err := rows.Scan(
			&r.Conteo, &idN, &terceroNombre,
			&acct, &tipo, &batch, &invc,
			&desc, &fecha, &duedate, &period,
			&debit, &credit, &saldo,
			&depto, &ccost, &proyecto,
		)
		if err != nil {
			return nil, fmt.Errorf("CARPRO row scan failed: %w", err)
		}

		r.TerceroID = trimString(idN)
		r.TerceroNombre = trimString(terceroNombre)
		if acct.Valid {
			r.CuentaContable = fmt.Sprintf("%.4f", acct.Float64)
			// Derive tipo_cartera from account prefix
			acctInt := int64(acct.Float64)
			switch {
			case acctInt >= 1300000000 && acctInt < 1400000000:
				r.TipoCartera = "CXC"
			case acctInt >= 2200000000 && acctInt < 2300000000:
				r.TipoCartera = "CXP"
			default:
				r.TipoCartera = "CXC"
			}
		}
		r.Tipo = trimString(tipo)
		if batch.Valid {
			r.Batch = int(batch.Int64)
		}
		r.Invc = trimString(invc)
		r.Descripcion = trimString(desc)
		if fecha.Valid {
			r.Fecha = fecha.Time.Format("2006-01-02")
		}
		if duedate.Valid {
			r.DueDate = duedate.Time.Format("2006-01-02")
		}
		r.Periodo = trimString(period)
		r.Debito = formatMoney(debit)
		r.Credito = formatMoney(credit)
		r.Saldo = formatMoney(saldo)
		if depto.Valid {
			r.Departamento = int(depto.Int64)
		}
		if ccost.Valid {
			r.CentroCosto = int(ccost.Int64)
		}
		r.ProyectoCodigo = trimString(proyecto)

		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("CARPRO rows iteration error: %w", err)
	}
	c.logger.Debug("CARPRO query returned records", "count", len(records))
	return records, nil
}

// QueryITEMACTIncremental fetches ITEMACT (inventory movement) records with CONTEO > lastConteo.
// All column names are resolved dynamically from oeColMap to handle Saiopen schema variants.
// Fixed columns: CONTEO, FECHA, TIPO. Everything else is optional.
func (c *Client) QueryITEMACTIncremental(lastConteo int64, batchSize int) ([]ITEMACTRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	itemactItemnoCol := c.oeColMap["itemact_itemno"]

	type optIA struct{ key, col, alias, tbl string }
	opts := []optIA{
		{"itemno",     itemactItemnoCol,                        "ITEMNO",      "I"},
		{"location",   c.oeColMap["itemact_location"],          "LOCATION",    "I"},
		{"idn",        c.oeColMap["itemact_idn"],               "ID_N",        "I"},
		{"batch",      c.oeColMap["itemact_batch"],             "BATCH",       "I"},
		{"qty",        c.oeColMap["itemact_qty"],               "QTY",         "I"},
		{"cost",       c.oeColMap["itemact_cost"],              "VALUNIT",     "I"},
		{"costop",     c.oeColMap["itemact_costop"],            "COSTOP",      "I"},
		{"total",      c.oeColMap["itemact_total"],             "TOTPARCIAL",  "I"},
		{"lote",       c.oeColMap["itemact_lote"],              "LOTE",        "I"},
		{"serie",      c.oeColMap["itemact_serie"],             "NOSERIE",     "I"},
		{"lote_ven",   c.oeColMap["itemact_lote_ven"],          "LOTEFVENCE",  "I"},
		{"period",     c.oeColMap["itemact_period"],            "PERIOD",      "I"},
	}

	var extraSelect string
	for _, o := range opts {
		if o.col != "" {
			extraSelect += fmt.Sprintf(", %s.%s AS %s", o.tbl, o.col, o.alias)
		}
	}

	query := fmt.Sprintf(`
		SELECT I.CONTEO, I.FECHA, I.TIPO%s
		FROM ITEMACT I
		WHERE I.CONTEO > ?
		ORDER BY I.CONTEO ASC
		ROWS 1 TO ?`, extraSelect)

	rows, err := c.db.Query(query, lastConteo, batchSize)
	if err != nil {
		return nil, fmt.Errorf("ITEMACT query failed: %w", err)
	}
	defer rows.Close()

	var records []ITEMACTRecord
	for rows.Next() {
		var r ITEMACTRecord
		var fecha sql.NullTime

		scanArgs := []interface{}{&r.Conteo, &fecha, &r.Tipo}

		// Optional scan vars
		var itemno, location, idN, lote, serie sql.NullString
		var batch sql.NullInt64
		var loteVen sql.NullTime
		var qty, cost, costOP, total sql.NullFloat64
		var period sql.NullString

		for _, o := range opts {
			if o.col == "" {
				continue
			}
			switch o.key {
			case "itemno":
				scanArgs = append(scanArgs, &itemno)
			case "location":
				scanArgs = append(scanArgs, &location)
			case "idn":
				scanArgs = append(scanArgs, &idN)
			case "batch":
				scanArgs = append(scanArgs, &batch)
			case "qty":
				scanArgs = append(scanArgs, &qty)
			case "cost":
				scanArgs = append(scanArgs, &cost)
			case "costop":
				scanArgs = append(scanArgs, &costOP)
			case "total":
				scanArgs = append(scanArgs, &total)
			case "lote":
				scanArgs = append(scanArgs, &lote)
			case "serie":
				scanArgs = append(scanArgs, &serie)
			case "lote_ven":
				scanArgs = append(scanArgs, &loteVen)
			case "period":
				scanArgs = append(scanArgs, &period)
			}
		}

		if err := rows.Scan(scanArgs...); err != nil {
			return nil, fmt.Errorf("ITEMACT row scan failed: %w", err)
		}

		if fecha.Valid {
			r.Fecha = fecha.Time.Format("2006-01-02")
		}
		r.ItemCodigo = trimString(itemno)
		r.Location   = trimString(location)
		r.TerceroID       = trimString(idN)
		if batch.Valid {
			r.Batch = int(batch.Int64)
		}
		r.Periodo = trimString(period)
		// ITEMACT no tiene columna PERIOD: siempre calcular desde FECHA en formato YYYYMM (ej. 202401)
		if r.Fecha != "" && len(r.Fecha) >= 7 {
			r.Periodo = r.Fecha[:4] + r.Fecha[5:7]
		}
		r.Cantidad       = formatQty(qty)
		r.ValorUnitario  = formatQty(cost)
		r.CostoPromedio  = formatQty(costOP)
		r.Total          = formatMoney(total)
		r.Lote           = trimString(lote)
		r.Serie         = trimString(serie)
		if loteVen.Valid {
			r.LoteVencimiento = loteVen.Time.Format("2006-01-02")
		}

		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("ITEMACT rows iteration error: %w", err)
	}
	c.logger.Debug("ITEMACT query returned records", "count", len(records))
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

// formatQty formats a nullable float as a string with 4 decimal places.
// Used for quantity and unit price fields (NUMERIC 15,4).
func formatQty(nf sql.NullFloat64) string {
	if !nf.Valid {
		return "0.0000"
	}
	return fmt.Sprintf("%.4f", nf.Float64)
}

// QueryAllTaxAuth fetches all tax authority records from TAXAUTH.
// This is a small table (typically <20 rows) so a full sync is always done.
func (c *Client) QueryAllTaxAuth() ([]TaxAuthRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	query := `SELECT CODIGO, AUTHORITY, RATE FROM TAXAUTH ORDER BY CODIGO`

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("TAXAUTH query failed: %w", err)
	}
	defer rows.Close()

	var records []TaxAuthRecord
	for rows.Next() {
		var r TaxAuthRecord
		var authority sql.NullString
		var rate sql.NullFloat64
		if err := rows.Scan(&r.Codigo, &authority, &rate); err != nil {
			return nil, fmt.Errorf("TAXAUTH row scan failed: %w", err)
		}
		r.Authority = trimString(authority)
		if rate.Valid {
			r.Rate = rate.Float64
		}
		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("TAXAUTH rows iteration error: %w", err)
	}
	c.logger.Debug("TAXAUTH query returned records", "count", len(records))
	return records, nil
}

// QueryAllItem fetches product/item records from the ITEM table.
// Only core fields are synced. offset and limit enable chunked full-sync.
func (c *Client) QueryAllItem(offset, limit int) ([]ItemRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	// Detect ITEM column name (same as used in OEDET/ITEMACT JOINs)
	itemnoCol := c.oeColMap["item_itemno"]
	if itemnoCol == "" {
		itemnoCol = "ITEM" // default PK column
	}
	descCol := c.oeColMap["item_desc"]
	if descCol == "" {
		descCol = "DESCRIPCION"
	}

	// Optional classification columns from ITEM
	reffabricaCol := c.oeColMap["item_reffabrica"]
	itemmstrCol   := c.oeColMap["item_itemmstr"]
	classCol      := c.oeColMap["item_class"]
	grupoItemCol  := c.oeColMap["item_grupo"]

	// Optional descriptors via JOINs to LINEA, GRUPO, SUBGRUPO
	linCodCol     := c.oeColMap["linea_codlinea"]
	linDescCol    := c.oeColMap["linea_desc"]
	grpCodLineaCol := c.oeColMap["grupo_codlinea"]
	grpCodGrpCol  := c.oeColMap["grupo_codgrupo"]
	grpDescCol    := c.oeColMap["grupo_desc"]
	subCodSubgrpCol := c.oeColMap["subgrupo_codsubgrupo"]
	subCodGrpCol  := c.oeColMap["subgrupo_codgrupo"]
	subCodLineaCol := c.oeColMap["subgrupo_codlinea"]
	subDescCol    := c.oeColMap["subgrupo_desc"]

	var extraItemSelect string
	if reffabricaCol != "" {
		extraItemSelect += fmt.Sprintf(", I.%s AS REFFABRICA", reffabricaCol)
	}
	if itemmstrCol != "" {
		extraItemSelect += fmt.Sprintf(", I.%s AS ITEMMSTR", itemmstrCol)
	}

	lineaItemActive := linCodCol != "" && linDescCol != "" && itemmstrCol != ""
	grupoItemActive := grpCodLineaCol != "" && grpCodGrpCol != "" && grpDescCol != "" && itemmstrCol != "" && classCol != ""
	subgrupoItemActive := subCodSubgrpCol != "" && subCodGrpCol != "" && subCodLineaCol != "" && subDescCol != "" &&
		grupoItemCol != "" && classCol != "" && itemmstrCol != ""

	var lineaItemJoin, grupoItemJoin, subgrupoItemJoin string
	if lineaItemActive {
		lineaItemJoin = fmt.Sprintf("LEFT JOIN LINEA L ON I.%s = L.%s", itemmstrCol, linCodCol)
		extraItemSelect += fmt.Sprintf(", L.%s AS DESCLINEA", linDescCol)
	}
	if grupoItemActive {
		grupoItemJoin = fmt.Sprintf("LEFT JOIN GRUPO G ON I.%s = G.%s AND I.%s = G.%s", itemmstrCol, grpCodLineaCol, classCol, grpCodGrpCol)
		extraItemSelect += fmt.Sprintf(", G.%s AS DESCGRUPO", grpDescCol)
	}
	if subgrupoItemActive {
		subgrupoItemJoin = fmt.Sprintf("LEFT JOIN SUBGRUPO S ON I.%s = S.%s AND I.%s = S.%s AND I.%s = S.%s",
			grupoItemCol, subCodSubgrpCol, classCol, subCodGrpCol, itemmstrCol, subCodLineaCol)
		extraItemSelect += fmt.Sprintf(", S.%s AS DESCSUBGRUPO", subDescCol)
	}

	query := fmt.Sprintf(`
		SELECT FIRST %d SKIP %d I.%s, I.%s, I.CLASS, I.GRUPO, I.PRICE, I.UOFMSALES, I.IMPOVENTA%s
		FROM ITEM I %s %s %s
		ORDER BY I.%s`,
		limit, offset, itemnoCol, descCol, extraItemSelect,
		lineaItemJoin, grupoItemJoin, subgrupoItemJoin, itemnoCol)

	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("ITEM query failed: %w", err)
	}
	defer rows.Close()

	var records []ItemRecord
	for rows.Next() {
		var r ItemRecord
		var descripcion, class, grupo, uofmSales, impoVenta sql.NullString
		var price sql.NullFloat64
		scanArgs := []interface{}{&r.Item, &descripcion, &class, &grupo, &price, &uofmSales, &impoVenta}

		var reffabrica, itemmstr sql.NullString
		if reffabricaCol != "" {
			scanArgs = append(scanArgs, &reffabrica)
		}
		if itemmstrCol != "" {
			scanArgs = append(scanArgs, &itemmstr)
		}
		var descLinea, descGrupo, descSubgrupo sql.NullString
		if lineaItemActive {
			scanArgs = append(scanArgs, &descLinea)
		}
		if grupoItemActive {
			scanArgs = append(scanArgs, &descGrupo)
		}
		if subgrupoItemActive {
			scanArgs = append(scanArgs, &descSubgrupo)
		}

		if err := rows.Scan(scanArgs...); err != nil {
			return nil, fmt.Errorf("ITEM row scan failed: %w", err)
		}
		r.Item = strings.TrimSpace(r.Item)
		r.Descripcion      = trimString(descripcion)
		r.Class            = trimString(class)
		r.Grupo            = trimString(grupo)
		r.UofmSales        = trimString(uofmSales)
		r.ImpoVenta        = trimString(impoVenta)
		r.Reffabrica       = trimString(reffabrica)
		r.LineaCodigo      = trimString(itemmstr)
		r.LineaDescripcion = trimString(descLinea)
		r.GrupoDescripcion = trimString(descGrupo)
		r.SubgrupoDescripcion = trimString(descSubgrupo)
		if price.Valid {
			r.Price = price.Float64
		}
		records = append(records, r)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("ITEM rows iteration error: %w", err)
	}
	c.logger.Debug("ITEM query returned records", "count", len(records), "offset", offset)
	return records, nil
}

// UpsertItems writes ItemRecord entries to the Firebird ITEM table using UPDATE+INSERT pattern.
// Returns the total number of rows affected.
func (c *Client) UpsertItems(items []ItemRecord) (int, error) {
	if c.db == nil {
		return 0, fmt.Errorf("database not connected")
	}

	itemnoCol := c.oeColMap["item_itemno"]
	if itemnoCol == "" {
		itemnoCol = "ITEM"
	}
	descCol := c.oeColMap["item_desc"]
	if descCol == "" {
		descCol = "DESCRIPCION"
	}

	total := 0
	for _, item := range items {
		if item.Item == "" {
			continue
		}

		// Try UPDATE first
		updateSQL := fmt.Sprintf(`
			UPDATE ITEM SET %s=?, CLASS=?, GRUPO=?, PRICE=?, UOFMSALES=?, IMPOVENTA=?
			WHERE %s=?`, descCol, itemnoCol)

		res, err := c.db.Exec(updateSQL,
			item.Descripcion, item.Class, item.Grupo, item.Price, item.UofmSales, item.ImpoVenta,
			item.Item,
		)
		if err != nil {
			return total, fmt.Errorf("ITEM UPDATE failed for %s: %w", item.Item, err)
		}

		rowsAffected, _ := res.RowsAffected()
		if rowsAffected == 0 {
			// INSERT if not exists
			insertSQL := fmt.Sprintf(`
				INSERT INTO ITEM (%s, %s, CLASS, GRUPO, PRICE, UOFMSALES, IMPOVENTA)
				VALUES (?, ?, ?, ?, ?, ?, ?)`, itemnoCol, descCol)

			_, err := c.db.Exec(insertSQL,
				item.Item, item.Descripcion, item.Class, item.Grupo, item.Price, item.UofmSales, item.ImpoVenta,
			)
			if err != nil {
				return total, fmt.Errorf("ITEM INSERT failed for %s: %w", item.Item, err)
			}
			rowsAffected = 1
		}
		total += int(rowsAffected)
	}

	c.logger.Info("ITEM upsert complete", "total", total)
	return total, nil
}

// QueryAllVendedores fetches all salesperson records from the VENDEDOR table.
// Returns IDVEND, NOMBRE, TELEFONO, ACTIVO ordered by IDVEND.
func (c *Client) QueryAllVendedores() ([]VendedorRecord, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database not connected")
	}

	rows, err := c.db.Query(`
		SELECT IDVEND, NOMBRE, TELEFONO, ACTIVO
		FROM VENDEDOR
		ORDER BY IDVEND ASC`)
	if err != nil {
		return nil, fmt.Errorf("VENDEDOR query failed: %w", err)
	}
	defer rows.Close()

	var records []VendedorRecord
	for rows.Next() {
		var r VendedorRecord
		var nombre, telefono, activo sql.NullString
		if err := rows.Scan(&r.Codigo, &nombre, &telefono, &activo); err != nil {
			return nil, fmt.Errorf("VENDEDOR row scan failed: %w", err)
		}
		r.Nombre = trimString(nombre)
		r.Telefono = trimString(telefono)
		// ACTIVO CHAR(5): 'True' = activo, 'False' = inactivo
		r.Activo = trimString(activo) != "False"
		records = append(records, r)
	}
	return records, rows.Err()
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
