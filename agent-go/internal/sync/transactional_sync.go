// Package sync — TransactionalSync handles the incremental synchronization of
// OE (invoice headers), OEDET (invoice lines), CARPRO (A/R & A/P movements),
// and ITEMACT (inventory movements) from Firebird to the Saicloud API.
//
// Each table uses a monotonic CONTEO (or NUMBER for OE) watermark, identical
// to the pattern used by GLSync.  OE must always run before OEDET because
// OEDET records have a FK dependency on FacturaEncabezado in the cloud DB.
package sync

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// TransactionalSync handles OE / OEDET / CARPRO / ITEMACT sync.
type TransactionalSync struct {
	cfg      *config.AgentConfig
	fbClient *firebird.Client
	sender   Sender
	logger   *slog.Logger
}

// NewTransactionalSync creates a new TransactionalSync handler.
func NewTransactionalSync(
	cfg *config.AgentConfig,
	fbClient *firebird.Client,
	sender Sender,
	logger *slog.Logger,
) *TransactionalSync {
	return &TransactionalSync{
		cfg:      cfg,
		fbClient: fbClient,
		sender:   sender,
		logger:   logger,
	}
}

// SyncAll runs OE → OEDET → CARPRO → ITEMACT in order.
// OE must precede OEDET to satisfy the FK constraint in the cloud DB.
func (ts *TransactionalSync) SyncAll(conn config.Connection) error {
	ts.logger.Info("transactional sync starting", "conn_id", conn.ID)

	if err := ts.syncOE(conn); err != nil {
		ts.logger.Error("OE sync failed", "conn_id", conn.ID, "error", err)
		return fmt.Errorf("OE: %w", err)
	}

	if err := ts.syncOEDet(conn); err != nil {
		ts.logger.Error("OEDET sync failed", "conn_id", conn.ID, "error", err)
		return fmt.Errorf("OEDET: %w", err)
	}

	if err := ts.syncCARPRO(conn); err != nil {
		ts.logger.Error("CARPRO sync failed", "conn_id", conn.ID, "error", err)
		return fmt.Errorf("CARPRO: %w", err)
	}

	if err := ts.syncITEMACT(conn); err != nil {
		ts.logger.Error("ITEMACT sync failed", "conn_id", conn.ID, "error", err)
		return fmt.Errorf("ITEMACT: %w", err)
	}

	ts.logger.Info("transactional sync complete", "conn_id", conn.ID)
	return nil
}

// syncOE performs incremental sync of OE (invoice headers) using per-TIPO watermarks.
// NUMBER is per document type (each TIPDOC.CLASE has its own consecutive sequence),
// so a single global watermark would miss new invoices of types with lower numbers.
// All tipos are discovered dynamically from TIPDOC.CLASE on every sync run.
func (ts *TransactionalSync) syncOE(conn config.Connection) error {
	ts.logger.Info("OE sync starting — discovering tipos from TIPDOC", "conn_id", conn.ID)

	tipos, err := ts.fbClient.QueryOETipos()
	if err != nil {
		return fmt.Errorf("OE: cannot fetch tipos from TIPDOC: %w", err)
	}
	if len(tipos) == 0 {
		ts.logger.Warn("OE sync: no tipos found in TIPDOC, skipping", "conn_id", conn.ID)
		return nil
	}

	ts.logger.Info("OE tipos discovered", "conn_id", conn.ID, "tipos", tipos)

	batchSize := conn.Sync.BatchSize
	totalRecords := 0

	for _, tipo := range tipos {
		var lastNumber int64
		if conn.Sync.LastOEWatermarks != nil {
			lastNumber = conn.Sync.LastOEWatermarks[tipo]
		}

		ts.logger.Info("OE sync tipo starting", "conn_id", conn.ID, "tipo", tipo, "last_number", lastNumber)
		batchCount := 0

		for {
			records, err := ts.fbClient.QueryOEIncremental(tipo, lastNumber, batchSize)
			if err != nil {
				return fmt.Errorf("OE query tipo=%s watermark=%d: %w", tipo, lastNumber, err)
			}
			if len(records) == 0 {
				break
			}

			batchCount++
			newNumber := int64(records[len(records)-1].Number)

			payload := api.OEBatchPayload{
				Type:      "oe_batch",
				CompanyID: conn.Saicloud.CompanyID,
				ConnID:    conn.ID,
				Timestamp: time.Now().UTC().Format(time.RFC3339),
				Data:      map[string]interface{}{"records": records, "tipo": tipo},
			}

			ts.logger.Info("sending OE batch",
				"conn_id", conn.ID, "tipo", tipo, "batch", batchCount,
				"records", len(records), "new_number", newNumber,
			)

			if err := ts.sender.PostOEBatch(payload); err != nil {
				return fmt.Errorf("OE batch POST tipo=%s batch=%d: %w", tipo, batchCount, err)
			}

			if err := ts.cfg.UpdateOEWatermarks(conn.ID, "oe", map[string]int64{tipo: newNumber}); err != nil {
				return fmt.Errorf("OE watermark update tipo=%s: %w", tipo, err)
			}

			lastNumber = newNumber
			totalRecords += len(records)

			if len(records) < batchSize {
				break
			}
		}

		ts.logger.Info("OE sync tipo complete", "conn_id", conn.ID, "tipo", tipo, "batches", batchCount)
	}

	ts.logger.Info("OE sync complete", "conn_id", conn.ID, "total", totalRecords)
	return nil
}

// syncOEDet performs incremental sync of OEDET (invoice lines) using per-TIPO watermarks.
// OEDET.CONTEO is per-invoice line number (1, 2, 3…), NOT a global counter.
// OEDET.NUMBER (FK to OE header) is per document type — same constraint as OE.
// Must run after syncOE to avoid FK violations in the cloud DB.
func (ts *TransactionalSync) syncOEDet(conn config.Connection) error {
	ts.logger.Info("OEDET sync starting — discovering tipos from TIPDOC", "conn_id", conn.ID)

	tipos, err := ts.fbClient.QueryOETipos()
	if err != nil {
		return fmt.Errorf("OEDET: cannot fetch tipos from TIPDOC: %w", err)
	}
	if len(tipos) == 0 {
		ts.logger.Warn("OEDET sync: no tipos found in TIPDOC, skipping", "conn_id", conn.ID)
		return nil
	}

	batchSize := conn.Sync.BatchSize
	totalRecords := 0

	for _, tipo := range tipos {
		var lastNumber int64
		if conn.Sync.LastOEDetWatermarks != nil {
			lastNumber = conn.Sync.LastOEDetWatermarks[tipo]
		}

		ts.logger.Info("OEDET sync tipo starting", "conn_id", conn.ID, "tipo", tipo, "last_number", lastNumber)
		batchCount := 0

		for {
			records, err := ts.fbClient.QueryOEDetIncremental(tipo, lastNumber, batchSize)
			if err != nil {
				return fmt.Errorf("OEDET query tipo=%s watermark=%d: %w", tipo, lastNumber, err)
			}
			if len(records) == 0 {
				break
			}

			batchCount++
			newLastNumber := int64(records[len(records)-1].FacturaNumber)

			payload := api.OEBatchPayload{
				Type:      "oedet_batch",
				CompanyID: conn.Saicloud.CompanyID,
				ConnID:    conn.ID,
				Timestamp: time.Now().UTC().Format(time.RFC3339),
				Data:      map[string]interface{}{"records": records, "tipo": tipo},
			}

			ts.logger.Info("sending OEDET batch",
				"conn_id", conn.ID, "tipo", tipo, "batch", batchCount,
				"records", len(records), "last_number", newLastNumber,
			)

			if err := ts.sender.PostOEDetBatch(payload); err != nil {
				return fmt.Errorf("OEDET batch POST tipo=%s batch=%d: %w", tipo, batchCount, err)
			}

			if err := ts.cfg.UpdateOEWatermarks(conn.ID, "oedet", map[string]int64{tipo: newLastNumber}); err != nil {
				return fmt.Errorf("OEDET watermark update tipo=%s: %w", tipo, err)
			}

			lastNumber = newLastNumber
			totalRecords += len(records)

			if len(records) < batchSize {
				break
			}
		}

		ts.logger.Info("OEDET sync tipo complete", "conn_id", conn.ID, "tipo", tipo, "batches", batchCount)
	}

	ts.logger.Info("OEDET sync complete", "conn_id", conn.ID, "total", totalRecords)
	return nil
}

// syncCARPRO performs incremental sync of CARPRO (A/R & A/P movements).
func (ts *TransactionalSync) syncCARPRO(conn config.Connection) error {
	lastConteo := conn.Sync.LastConteoCARPRO
	batchSize := conn.Sync.BatchSize
	batchCount := 0
	totalRecords := 0

	ts.logger.Info("CARPRO sync starting", "conn_id", conn.ID, "last_conteo", lastConteo)

	for {
		records, err := ts.fbClient.QueryCARPROIncremental(lastConteo, batchSize)
		if err != nil {
			return fmt.Errorf("CARPRO query at conteo %d: %w", lastConteo, err)
		}
		if len(records) == 0 {
			break
		}

		batchCount++
		newLastConteo := records[len(records)-1].Conteo

		payload := api.OEBatchPayload{
			Type:      "carpro_batch",
			CompanyID: conn.Saicloud.CompanyID,
			ConnID:    conn.ID,
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Data:      map[string]interface{}{"records": records},
		}

		ts.logger.Info("sending CARPRO batch",
			"conn_id", conn.ID, "batch", batchCount,
			"records", len(records), "last_conteo", newLastConteo,
		)

		if err := ts.sender.PostCARPROBatch(payload); err != nil {
			return fmt.Errorf("CARPRO batch POST (batch %d): %w", batchCount, err)
		}

		if err := ts.cfg.UpdateTransactionalWatermark(conn.ID, "carpro", newLastConteo); err != nil {
			return fmt.Errorf("CARPRO watermark update: %w", err)
		}

		lastConteo = newLastConteo
		totalRecords += len(records)

		if len(records) < batchSize {
			break
		}
	}

	ts.logger.Info("CARPRO sync complete", "conn_id", conn.ID, "total", totalRecords, "batches", batchCount)
	return nil
}

// syncITEMACT performs incremental sync of ITEMACT (inventory movements).
func (ts *TransactionalSync) syncITEMACT(conn config.Connection) error {
	lastConteo := conn.Sync.LastConteoITEMACT
	batchSize := conn.Sync.BatchSize
	batchCount := 0
	totalRecords := 0

	ts.logger.Info("ITEMACT sync starting", "conn_id", conn.ID, "last_conteo", lastConteo)

	for {
		records, err := ts.fbClient.QueryITEMACTIncremental(lastConteo, batchSize)
		if err != nil {
			return fmt.Errorf("ITEMACT query at conteo %d: %w", lastConteo, err)
		}
		if len(records) == 0 {
			break
		}

		batchCount++
		newLastConteo := records[len(records)-1].Conteo

		payload := api.OEBatchPayload{
			Type:      "itemact_batch",
			CompanyID: conn.Saicloud.CompanyID,
			ConnID:    conn.ID,
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Data:      map[string]interface{}{"records": records},
		}

		ts.logger.Info("sending ITEMACT batch",
			"conn_id", conn.ID, "batch", batchCount,
			"records", len(records), "last_conteo", newLastConteo,
		)

		if err := ts.sender.PostITEMACTBatch(payload); err != nil {
			return fmt.Errorf("ITEMACT batch POST (batch %d): %w", batchCount, err)
		}

		if err := ts.cfg.UpdateTransactionalWatermark(conn.ID, "itemact", newLastConteo); err != nil {
			return fmt.Errorf("ITEMACT watermark update: %w", err)
		}

		lastConteo = newLastConteo
		totalRecords += len(records)

		if len(records) < batchSize {
			break
		}
	}

	ts.logger.Info("ITEMACT sync complete", "conn_id", conn.ID, "total", totalRecords, "batches", batchCount)
	return nil
}
