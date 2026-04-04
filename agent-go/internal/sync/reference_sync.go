package sync

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// ReferenceSync handles the full synchronization of reference tables
// (ACCT, CUST, LISTA, PROYECTOS, ACTIVIDADES). These tables are synced
// entirely on each cycle since they are relatively small and change infrequently.
type ReferenceSync struct {
	cfg       *config.AgentConfig
	fbClient  *firebird.Client
	apiClient *api.Client
	logger    *slog.Logger
}

// NewReferenceSync creates a new reference table sync handler.
func NewReferenceSync(
	cfg *config.AgentConfig,
	fbClient *firebird.Client,
	apiClient *api.Client,
	logger *slog.Logger,
) *ReferenceSync {
	return &ReferenceSync{
		cfg:       cfg,
		fbClient:  fbClient,
		apiClient: apiClient,
		logger:    logger,
	}
}

// SyncAll runs the full sync for all reference tables.
// Failures in individual tables are logged but do not stop the remaining tables.
func (rs *ReferenceSync) SyncAll(conn config.Connection) error {
	rs.logger.Info("reference sync starting", "conn_id", conn.ID)

	var errs []error

	if err := rs.syncAcct(conn); err != nil {
		rs.logger.Error("ACCT sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("ACCT: %w", err))
	}

	if err := rs.syncCust(conn); err != nil {
		rs.logger.Error("CUST sync failed", "conn_id", conn.ID, "error", err)
		errs = append(errs, fmt.Errorf("CUST: %w", err))
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

	if err := rs.apiClient.PostReference("acct", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "acct"); err != nil {
		rs.logger.Warn("failed to update ACCT sync time", "error", err)
	}

	rs.logger.Info("ACCT sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}

// syncCust fetches and sends all third-party entities.
func (rs *ReferenceSync) syncCust(conn config.Connection) error {
	rs.logger.Info("syncing CUST", "conn_id", conn.ID)

	records, err := rs.fbClient.QueryAllCust()
	if err != nil {
		return err
	}

	payload := api.ReferencePayload{
		Type:      "cust_full",
		CompanyID: conn.Saicloud.CompanyID,
		ConnID:    conn.ID,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Data: api.ReferenceData{
			Records:    records,
			TotalCount: len(records),
		},
	}

	if err := rs.apiClient.PostReference("cust", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "cust"); err != nil {
		rs.logger.Warn("failed to update CUST sync time", "error", err)
	}

	rs.logger.Info("CUST sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}

// syncLista fetches and sends all departments and cost centers.
func (rs *ReferenceSync) syncLista(conn config.Connection) error {
	rs.logger.Info("syncing LISTA", "conn_id", conn.ID)

	// Fetch both DP (departments) and CC (cost centers)
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

	if err := rs.apiClient.PostReference("lista", payload); err != nil {
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

	if err := rs.apiClient.PostReference("proyectos", payload); err != nil {
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

	if err := rs.apiClient.PostReference("actividades", payload); err != nil {
		return err
	}

	if err := rs.cfg.UpdateReferenceSyncTime(conn.ID, "actividades"); err != nil {
		rs.logger.Warn("failed to update ACTIVIDADES sync time", "error", err)
	}

	rs.logger.Info("ACTIVIDADES sync complete", "conn_id", conn.ID, "records", len(records))
	return nil
}
