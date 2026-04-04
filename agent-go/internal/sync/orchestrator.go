// Package sync orchestrates the data synchronization between Firebird databases
// and the Saicloud API. Each enabled connection runs in its own goroutine with
// independent sync cycles for GL (incremental) and reference tables (full).
package sync

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	stdsync "sync"
	"syscall"
	"time"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// Orchestrator manages sync workers for all enabled connections.
// Each connection gets its own goroutine, so a failure in one connection
// does not affect the others.
type Orchestrator struct {
	cfg    *config.AgentConfig
	logger *slog.Logger
}

// NewOrchestrator creates a new sync orchestrator.
func NewOrchestrator(cfg *config.AgentConfig, logger *slog.Logger) *Orchestrator {
	return &Orchestrator{
		cfg:    cfg,
		logger: logger,
	}
}

// Run starts sync workers for all enabled connections and blocks until
// a SIGINT or SIGTERM signal is received.
func (o *Orchestrator) Run() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Graceful shutdown on OS signals
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	enabled := o.cfg.EnabledConnections()
	if len(enabled) == 0 {
		o.logger.Warn("no enabled connections found, nothing to sync")
		fmt.Println("No enabled connections. Use 'agent.exe config' to add connections.")
		return
	}

	o.logger.Info("starting sync orchestrator", "connections", len(enabled))

	var wg stdsync.WaitGroup

	for _, conn := range enabled {
		wg.Add(1)
		go func(c config.Connection) {
			defer wg.Done()
			o.runWorker(ctx, c)
		}(conn)
	}

	// Wait for shutdown signal
	sig := <-sigCh
	o.logger.Info("received shutdown signal", "signal", sig.String())
	fmt.Printf("\nReceived %s, shutting down gracefully...\n", sig)
	cancel()

	// Wait for all workers to finish
	wg.Wait()
	o.logger.Info("all sync workers stopped")
}

// RunOnce executes a single sync cycle for all enabled connections.
// Used for testing and one-shot execution.
func (o *Orchestrator) RunOnce() error {
	enabled := o.cfg.EnabledConnections()
	if len(enabled) == 0 {
		return fmt.Errorf("no enabled connections")
	}

	var firstErr error
	for _, conn := range enabled {
		if err := o.syncOnce(conn); err != nil {
			o.logger.Error("sync failed for connection",
				"conn_id", conn.ID,
				"conn_name", conn.Name,
				"error", err,
			)
			if firstErr == nil {
				firstErr = err
			}
		}
	}
	return firstErr
}

// TestConnection tests both the Firebird and Saicloud API connections
// for a given connection configuration.
func (o *Orchestrator) TestConnection(conn *config.Connection) error {
	// Test Firebird connection
	fmt.Print("  Testing Firebird connection... ")
	fbClient := firebird.New(conn.Firebird.DSN(), o.logger)
	if err := fbClient.Connect(); err != nil {
		fmt.Println("FAILED")
		return fmt.Errorf("firebird connection failed: %w", err)
	}
	defer fbClient.Close()

	total, maxConteo, err := fbClient.CountGL()
	if err != nil {
		fmt.Println("FAILED")
		return fmt.Errorf("firebird GL count query failed: %w", err)
	}
	fmt.Printf("OK (GL records: %d, max CONTEO: %d)\n", total, maxConteo)

	// Test Saicloud API connection
	fmt.Print("  Testing Saicloud API connection... ")
	apiClient := api.NewClient(conn.Saicloud.APIURL, conn.Saicloud.AgentToken, o.logger)
	if err := apiClient.HealthCheck(); err != nil {
		fmt.Println("FAILED")
		return fmt.Errorf("saicloud API health check failed: %w", err)
	}
	fmt.Println("OK")

	// Summary
	pending := maxConteo - conn.Sync.LastConteoGL
	if pending < 0 {
		pending = 0
	}
	fmt.Printf("\n  Summary:\n")
	fmt.Printf("    Total GL records: %d\n", total)
	fmt.Printf("    Last synced CONTEO: %d\n", conn.Sync.LastConteoGL)
	fmt.Printf("    Pending records: %d\n", pending)

	return nil
}

// runWorker runs the sync loop for a single connection.
// It sets up independent tickers for GL sync and reference table sync.
func (o *Orchestrator) runWorker(ctx context.Context, conn config.Connection) {
	logger := o.logger.With("conn_id", conn.ID, "conn_name", conn.Name)
	logger.Info("starting sync worker",
		"gl_interval_min", conn.Sync.GLIntervalMinutes,
		"ref_interval_hrs", conn.Sync.ReferenceIntervalHours,
	)

	glInterval := time.Duration(conn.Sync.GLIntervalMinutes) * time.Minute
	refInterval := time.Duration(conn.Sync.ReferenceIntervalHours) * time.Hour

	glTicker := time.NewTicker(glInterval)
	refTicker := time.NewTicker(refInterval)
	defer glTicker.Stop()
	defer refTicker.Stop()

	// Run immediately on startup, then on ticker
	o.doGLSync(conn, logger)
	o.doReferenceSync(conn, logger)

	for {
		select {
		case <-ctx.Done():
			logger.Info("sync worker stopping")
			return
		case <-glTicker.C:
			o.doGLSync(conn, logger)
		case <-refTicker.C:
			o.doReferenceSync(conn, logger)
		}
	}
}

// syncOnce executes a single GL + reference sync cycle for a connection.
func (o *Orchestrator) syncOnce(conn config.Connection) error {
	logger := o.logger.With("conn_id", conn.ID, "conn_name", conn.Name)

	if err := o.doGLSync(conn, logger); err != nil {
		return fmt.Errorf("GL sync failed: %w", err)
	}

	if err := o.doReferenceSync(conn, logger); err != nil {
		return fmt.Errorf("reference sync failed: %w", err)
	}

	return nil
}

// doGLSync runs the incremental GL synchronization.
func (o *Orchestrator) doGLSync(conn config.Connection, logger *slog.Logger) error {
	logger.Info("starting GL sync cycle")

	fbClient := firebird.New(conn.Firebird.DSN(), logger)
	if err := fbClient.Connect(); err != nil {
		logger.Error("firebird connection failed", "error", err)
		return err
	}
	defer fbClient.Close()

	apiClient := api.NewClient(conn.Saicloud.APIURL, conn.Saicloud.AgentToken, logger)

	syncer := NewGLSync(o.cfg, fbClient, apiClient, logger)
	return syncer.Sync(conn)
}

// doReferenceSync runs the full sync for all reference tables.
func (o *Orchestrator) doReferenceSync(conn config.Connection, logger *slog.Logger) error {
	logger.Info("starting reference sync cycle")

	fbClient := firebird.New(conn.Firebird.DSN(), logger)
	if err := fbClient.Connect(); err != nil {
		logger.Error("firebird connection failed", "error", err)
		return err
	}
	defer fbClient.Close()

	apiClient := api.NewClient(conn.Saicloud.APIURL, conn.Saicloud.AgentToken, logger)

	syncer := NewReferenceSync(o.cfg, fbClient, apiClient, logger)
	return syncer.SyncAll(conn)
}
