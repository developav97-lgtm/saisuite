package sync

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// GLSync handles the incremental synchronization of GL (General Ledger) records.
// It uses the CONTEO column as a watermark to fetch only new records since the last sync.
type GLSync struct {
	cfg       *config.AgentConfig
	fbClient  *firebird.Client
	apiClient *api.Client
	logger    *slog.Logger
}

// NewGLSync creates a new GL sync handler.
func NewGLSync(
	cfg *config.AgentConfig,
	fbClient *firebird.Client,
	apiClient *api.Client,
	logger *slog.Logger,
) *GLSync {
	return &GLSync{
		cfg:       cfg,
		fbClient:  fbClient,
		apiClient: apiClient,
		logger:    logger,
	}
}

// Sync performs the incremental GL sync for a connection.
// It fetches batches of records where CONTEO > last_conteo_gl until there are no more.
// After each successful batch POST, the watermark is updated and persisted.
func (g *GLSync) Sync(conn config.Connection) error {
	lastConteo := conn.Sync.LastConteoGL
	batchSize := conn.Sync.BatchSize
	batchCount := 0
	totalRecords := 0

	g.logger.Info("GL sync starting",
		"conn_id", conn.ID,
		"last_conteo", lastConteo,
		"batch_size", batchSize,
	)

	for {
		records, err := g.fbClient.QueryGLIncremental(lastConteo, batchSize)
		if err != nil {
			g.logger.Error("GL query failed",
				"conn_id", conn.ID,
				"last_conteo", lastConteo,
				"error", err,
			)
			return fmt.Errorf("GL query at conteo %d: %w", lastConteo, err)
		}

		if len(records) == 0 {
			g.logger.Info("GL sync complete, no more records",
				"conn_id", conn.ID,
				"total_records", totalRecords,
				"total_batches", batchCount,
			)
			break
		}

		batchCount++
		newLastConteo := records[len(records)-1].Conteo

		// Build the payload matching the contract
		payload := api.GLBatchPayload{
			Type:      "gl_batch",
			CompanyID: conn.Saicloud.CompanyID,
			ConnID:    conn.ID,
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Data: api.GLBatchData{
				Records:    convertGLRecords(records),
				LastConteo: newLastConteo,
				BatchCount: batchCount,
			},
		}

		g.logger.Info("sending GL batch",
			"conn_id", conn.ID,
			"batch", batchCount,
			"records", len(records),
			"first_conteo", records[0].Conteo,
			"last_conteo", newLastConteo,
		)

		if err := g.apiClient.PostGLBatch(payload); err != nil {
			g.logger.Error("GL batch POST failed",
				"conn_id", conn.ID,
				"batch", batchCount,
				"error", err,
			)
			return fmt.Errorf("GL batch POST (batch %d): %w", batchCount, err)
		}

		// Update watermark after successful POST
		if err := g.cfg.UpdateWatermark(conn.ID, newLastConteo); err != nil {
			g.logger.Error("watermark update failed",
				"conn_id", conn.ID,
				"new_conteo", newLastConteo,
				"error", err,
			)
			return fmt.Errorf("watermark update: %w", err)
		}

		lastConteo = newLastConteo
		totalRecords += len(records)

		g.logger.Info("GL batch sent successfully",
			"conn_id", conn.ID,
			"batch", batchCount,
			"new_watermark", newLastConteo,
		)

		// If we got fewer records than batch_size, we have caught up
		if len(records) < batchSize {
			g.logger.Info("GL sync complete, caught up",
				"conn_id", conn.ID,
				"total_records", totalRecords,
				"total_batches", batchCount,
			)
			break
		}
	}

	return nil
}

// convertGLRecords converts firebird.GLRecord to the API contract format.
func convertGLRecords(records []firebird.GLRecord) []api.GLRecord {
	result := make([]api.GLRecord, len(records))
	for i, r := range records {
		result[i] = api.GLRecord{
			Conteo:             r.Conteo,
			Fecha:              r.Fecha,
			DueDate:            r.DueDate,
			Invc:               r.Invc,
			TerceroID:          r.TerceroID,
			TerceroNombre:      r.TerceroNombre,
			Auxiliar:           r.Auxiliar,
			AuxiliarNombre:     r.AuxiliarNombre,
			TituloCodigo:       r.TituloCodigo,
			TituloNombre:       r.TituloNombre,
			GrupoCodigo:        r.GrupoCodigo,
			GrupoNombre:        r.GrupoNombre,
			CuentaCodigo:       r.CuentaCodigo,
			CuentaNombre:       r.CuentaNombre,
			SubcuentaCodigo:    r.SubcuentaCodigo,
			SubcuentaNombre:    r.SubcuentaNombre,
			Debito:             r.Debito,
			Credito:            r.Credito,
			Tipo:               r.Tipo,
			Batch:              r.Batch,
			Descripcion:        r.Descripcion,
			Periodo:            r.Periodo,
			DepartamentoCodigo: r.DepartamentoCodigo,
			DepartamentoNombre: r.DepartamentoNombre,
			CentroCostoCodigo:  r.CentroCostoCodigo,
			CentroCostoNombre:  r.CentroCostoNombre,
			ProyectoCodigo:     r.ProyectoCodigo,
			ProyectoNombre:     r.ProyectoNombre,
			ActividadCodigo:    r.ActividadCodigo,
			ActividadNombre:    r.ActividadNombre,
		}
	}
	return result
}
