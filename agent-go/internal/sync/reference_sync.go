package sync

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// ReferenceSync handles the synchronization of reference tables.
// ACCT, LISTA, PROYECTOS, ACTIVIDADES: full sync each cycle.
// CUST: incremental by Version field, always atomic with SHIPTO and TRIBUTARIA.
type ReferenceSync struct {
	cfg      *config.AgentConfig
	fbClient *firebird.Client
	sender   Sender
	logger   *slog.Logger
}

// NewReferenceSync creates a new reference table sync handler.
func NewReferenceSync(
	cfg *config.AgentConfig,
	fbClient *firebird.Client,
	sender Sender,
	logger *slog.Logger,
) *ReferenceSync {
	return &ReferenceSync{
		cfg:      cfg,
		fbClient: fbClient,
		sender:   sender,
		logger:   logger,
	}
}

// SyncAll runs full sync for all reference tables (ACCT, LISTA, PROYECTOS, ACTIVIDADES).
// CUST is NOT called here — it runs on the GL ticker via SyncCustIncremental.
func (rs *ReferenceSync) SyncAll(conn config.Connection) error {
	rs.logger.Info("reference sync starting", "conn_id", conn.ID)

	var errs []error

	if err := rs.syncAcct(conn); err != nil {
		rs.logger.Error("ACCT sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("ACCT: %w", err))
	}

	if err := rs.syncLista(conn); err != nil {
		rs.logger.Error("LISTA sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("LISTA: %w", err))
	}

	if err := rs.syncProyectos(conn); err != nil {
		rs.logger.Error("PROYECTOS sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("PROYECTOS: %w", err))
	}

	if err := rs.syncActividades(conn); err != nil {
		rs.logger.Error("ACTIVIDADES sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("ACTIVIDADES: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("reference sync had %d errors: %v", len(errs), errs)
	}

	rs.logger.Info("reference sync complete", "conn_id", conn.ID)
	return nil
}

// SyncCustIncremental fetches only CUST records newer than LastVersionCust.
// On first run (LastVersionCust == 0) it fetches everything.
// For each affected ID_N it also fetches SHIPTO and TRIBUTARIA atomically.
// Call this on the GL ticker (every gl_interval_minutes) for near-realtime delivery.
func (rs *ReferenceSync) SyncCustIncremental(conn config.Connection) error {
	lastVersion := conn.Sync.LastVersionCust
	rs.logger.Info("syncing CUST incremental", "conn_id", conn.ID, "last_version", lastVersion)

	custRecords, maxVersion, err := rs.fbClient.QueryCustSince(lastVersion)
	if err != nil {
		return fmt.Errorf("CUST query failed: %w", err)
	}

	if len(custRecords) == 0 {
		rs.logger.Debug("CUST incremental: no changes", "conn_id", conn.ID)
		return nil
	}

	// On first sync (lastVersion==0) do a full scan of SHIPTO/TRIBUTARIA (no IN clause).
	// On incremental syncs filter by the affected ID_N values only.
	var shiptoIDNs []string
	var tributariaIDNs []string
	if lastVersion > 0 {
		for _, r := range custRecords {
			shiptoIDNs = append(shiptoIDNs, r.IDN)
			tributariaIDNs = append(tributariaIDNs, r.IDN)
		}
	}
	// Empty slice → QueryShipToByIDN / QueryTributariaByIDN do a full scan

	// Fetch SHIPTO and TRIBUTARIA atomically with the CUST batch
	shiptoRecords, err := rs.fbClient.QueryShipToByIDN(shiptoIDNs)
	if err != nil {
		return fmt.Errorf("SHIPTO query failed: %w", err)
	}

	tributariaRecords, err := rs.fbClient.QueryTributariaByIDN(tributariaIDNs)
	if err != nil {
		return fmt.Errorf("TRIBUTARIA query failed: %w", err)
	}

	msgType := "cust_batch"
	if lastVersion == 0 {
		msgType = "cust_full"
	}

	payload := api.ReferencePayload{
		Type:      msgType,
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.CustBatchData{
			Records:    custRecords,
			ShipTo:     shiptoRecords,
			Tributaria: tributariaRecords,
			TotalCount: len(custRecords),
		},
	}

	if err := rs.sender.PostReference("cust", payload); err != nil {
		return err
	}

	// Persist the new watermark
	if err := rs.cfg.UpdateCustVersion(conn.ID, maxVersion); err != nil {
		rs.logger.Warn("failed to update CUST version watermark", "error", err)
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "cust"); err != nil {
		rs.logger.Warn("failed to update CUST sync time", "error", err)
	}

	rs.logger.Info("CUST incremental sync complete",
		"conn_id", conn.ID,
		"cust_records", len(custRecords),
		"shipto_records", len(shiptoRecords),
		"tributaria_records", len(tributariaRecords),
		"max_version", maxVersion,
	)
	return nil
}

// syncAcct fetches and sends the complete chart of accounts.
func (rs *ReferenceSync) syncAcct(conn config.Connection) error {
	rs.logger.Info("syncing ACCT", "conn_id", conn.ID)

	records, err := rs.fbClient.QueryAllAcct()
	if err != nil {
		return err
	}

	payload := api.ReferencePayload{
		Type:      "acct_full",
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.ReferenceData{
			Records:    records,
			TotalCount: len(records),
		},
	}

	if err := rs.sender.PostReference("acct", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "acct"); err != nil {
		rs.logger.Warn("failed to update ACCT sync time", "error", err)
	}

	rs.logger.Info("ACCT sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}

// syncLista fetches and sends all departments and cost centers.
func (rs *ReferenceSync) syncLista(conn config.Connection) error {
	rs.logger.Info("syncing LISTA", "conn_id", conn.ID)

	records, err := rs.fbClient.QueryAllLista("")
	if err != nil {
		return err
	}

	payload := api.ReferencePayload{
		Type:      "lista_full",
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.ReferenceData{
			Records:    records,
			TotalCount: len(records),
		},
	}

	if err := rs.sender.PostReference("lista", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "lista"); err != nil {
		rs.logger.Warn("failed to update LISTA sync time", "error", err)
	}

	rs.logger.Info("LISTA sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}

// syncProyectos fetches and sends all projects.
func (rs *ReferenceSync) syncProyectos(conn config.Connection) error {
	rs.logger.Info("syncing PROYECTOS", "conn_id", conn.ID)

	records, err := rs.fbClient.QueryAllProyectos()
	if err != nil {
		return err
	}

	payload := api.ReferencePayload{
		Type:      "proyectos_full",
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.ReferenceData{
			Records:    records,
			TotalCount: len(records),
		},
	}

	if err := rs.sender.PostReference("proyectos", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "proyectos"); err != nil {
		rs.logger.Warn("failed to update PROYECTOS sync time", "error", err)
	}

	rs.logger.Info("PROYECTOS sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}

// syncActividades fetches and sends all activities.
func (rs *ReferenceSync) syncActividades(conn config.Connection) error {
	rs.logger.Info("syncing ACTIVIDADES", "conn_id", conn.ID)

	records, err := rs.fbClient.QueryAllActividades()
	if err != nil {
		return err
	}

	payload := api.ReferencePayload{
		Type:      "actividades_full",
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.ReferenceData{
			Records:    records,
			TotalCount: len(records),
		},
	}

	if err := rs.sender.PostReference("actividades", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "actividades"); err != nil {
		rs.logger.Warn("failed to update ACTIVIDADES sync time", "error", err)
	}

	rs.logger.Info("ACTIVIDADES sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}
