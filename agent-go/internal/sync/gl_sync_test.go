package sync

import (
	"testing"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

func TestConvertGLRecords(t *testing.T) {
	departamento := 5
	centroCosto := 10
	proyecto := "PRY001"
	actividad := "ACT"

	fbRecords := []firebird.GLRecord{
		{
			Conteo:             100,
			Fecha:              "2026-03-15",
			DueDate:            "2026-04-15",
			Invc:               "FV-001234",
			TerceroID:          "800123456",
			TerceroNombre:      "Cliente ABC S.A.S",
			Auxiliar:           130505.01,
			AuxiliarNombre:     "Cuentas por cobrar",
			TituloCodigo:       1,
			TituloNombre:       "ACTIVO",
			GrupoCodigo:        13,
			GrupoNombre:        "DEUDORES",
			CuentaCodigo:       1305,
			CuentaNombre:       "CLIENTES",
			SubcuentaCodigo:    130505,
			SubcuentaNombre:    "NACIONALES",
			Debito:             "1500000.00",
			Credito:            "0.00",
			Tipo:               "FV",
			Batch:              1234,
			Descripcion:        "Venta mercancias",
			Periodo:            "2026-03",
			DepartamentoCodigo: &departamento,
			DepartamentoNombre: "VENTAS",
			CentroCostoCodigo:  &centroCosto,
			CentroCostoNombre:  "BOGOTA",
			ProyectoCodigo:     &proyecto,
			ProyectoNombre:     "Proyecto demo",
			ActividadCodigo:    &actividad,
			ActividadNombre:    "Actividad principal",
		},
		{
			Conteo:         101,
			Fecha:          "2026-03-15",
			TerceroID:      "800123456",
			TerceroNombre:  "Cliente ABC S.A.S",
			Auxiliar:       411505.01,
			AuxiliarNombre: "Ingresos",
			Debito:         "0.00",
			Credito:        "1500000.00",
			Tipo:           "FV",
			Batch:          1234,
			Descripcion:    "Venta mercancias",
			Periodo:        "2026-03",
		},
	}

	apiRecords := convertGLRecords(fbRecords)

	if len(apiRecords) != 2 {
		t.Fatalf("expected 2 records, got %d", len(apiRecords))
	}

	// Verify first record
	r := apiRecords[0]
	if r.Conteo != 100 {
		t.Errorf("expected conteo 100, got %d", r.Conteo)
	}
	if r.Debito != "1500000.00" {
		t.Errorf("expected debito '1500000.00', got '%s'", r.Debito)
	}
	if r.Credito != "0.00" {
		t.Errorf("expected credito '0.00', got '%s'", r.Credito)
	}
	if r.TerceroID != "800123456" {
		t.Errorf("expected tercero_id '800123456', got '%s'", r.TerceroID)
	}
	if r.DepartamentoCodigo == nil || *r.DepartamentoCodigo != 5 {
		t.Error("expected departamento_codigo 5")
	}
	if r.ProyectoCodigo == nil || *r.ProyectoCodigo != "PRY001" {
		t.Error("expected proyecto_codigo PRY001")
	}

	// Verify second record has nil optional fields
	r2 := apiRecords[1]
	if r2.DepartamentoCodigo != nil {
		t.Error("expected nil departamento_codigo for second record")
	}
	if r2.ProyectoCodigo != nil {
		t.Error("expected nil proyecto_codigo for second record")
	}
	if r2.Credito != "1500000.00" {
		t.Errorf("expected credito '1500000.00', got '%s'", r2.Credito)
	}
}

func TestConvertGLRecordsEmpty(t *testing.T) {
	result := convertGLRecords([]firebird.GLRecord{})
	if len(result) != 0 {
		t.Errorf("expected 0 records for empty input, got %d", len(result))
	}
}

func TestConvertGLRecordsMonetaryFormat(t *testing.T) {
	records := []firebird.GLRecord{
		{
			Conteo:  1,
			Debito:  "0.00",
			Credito: "999999999.99",
		},
		{
			Conteo:  2,
			Debito:  "12345.67",
			Credito: "0.00",
		},
	}

	apiRecords := convertGLRecords(records)

	// Monetary values must always be strings
	if apiRecords[0].Credito != "999999999.99" {
		t.Errorf("expected credito '999999999.99', got '%s'", apiRecords[0].Credito)
	}
	if apiRecords[1].Debito != "12345.67" {
		t.Errorf("expected debito '12345.67', got '%s'", apiRecords[1].Debito)
	}
}

func TestGLBatchPayloadStructure(t *testing.T) {
	payload := api.GLBatchPayload{
		Type:      "gl_batch",
		CompanyID: "uuid-test",
		ConnID:    "conn_001",
		Timestamp: "2026-04-01T15:00:00Z",
		Data: api.GLBatchData{
			Records: []api.GLRecord{
				{
					Conteo:  100,
					Debito:  "1000.00",
					Credito: "0.00",
				},
			},
			LastConteo: 100,
			BatchCount: 1,
		},
	}

	if payload.Type != "gl_batch" {
		t.Errorf("expected type 'gl_batch', got '%s'", payload.Type)
	}
	if payload.Data.LastConteo != 100 {
		t.Errorf("expected last_conteo 100, got %d", payload.Data.LastConteo)
	}
	if len(payload.Data.Records) != 1 {
		t.Errorf("expected 1 record, got %d", len(payload.Data.Records))
	}
}
