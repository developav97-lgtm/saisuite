// Package main is the CLI entry point for the Saicloud Agent.
// It provides subcommands for configuring, running, and managing the sync service.
package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"strings"

	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/configurator"
	"github.com/valmentech/saicloud-agent/internal/sync"
	"github.com/valmentech/saicloud-agent/internal/winsvc"
)

const version = "1.0.4"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	cmd := strings.ToLower(os.Args[1])

	switch cmd {
	case "config":
		runConfig()
	case "serve":
		runServe()
	case "install":
		runInstall()
	case "uninstall":
		runUninstall()
	case "status":
		runStatus()
	case "test":
		runTest()
	case "version":
		fmt.Printf("saicloud-agent v%s\n", version)
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n\n", cmd)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Printf(`Saicloud Agent v%s
Sync Saiopen (Firebird) data to Saicloud (Django/PostgreSQL)

Usage:
  agent.exe <command> [options]

Commands:
  config      Open the web configurator at http://localhost:8765
  serve       Start the sync service (production mode)
  install     Register as a Windows Service
  uninstall   Remove the Windows Service
  status      Show status of all connections
  test        Test a specific connection
  version     Show agent version
  help        Show this help message

Test Options:
  --id <conn_id>   Connection ID to test (e.g., conn_001)

Examples:
  agent.exe config
  agent.exe serve
  agent.exe test --id conn_001
  agent.exe install
`, version)
}

func setupLogger(cfg *config.AgentConfig) *slog.Logger {
	level := slog.LevelInfo
	switch strings.ToLower(cfg.LogLevel) {
	case "debug":
		level = slog.LevelDebug
	case "warn", "warning":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	}

	opts := &slog.HandlerOptions{Level: level}

	// Try to open log file; fall back to stderr
	var handler slog.Handler
	if cfg.LogFile != "" {
		f, err := os.OpenFile(cfg.LogFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: cannot open log file %s: %v (using stderr)\n", cfg.LogFile, err)
			handler = slog.NewJSONHandler(os.Stderr, opts)
		} else {
			handler = slog.NewJSONHandler(f, opts)
		}
	} else {
		handler = slog.NewJSONHandler(os.Stderr, opts)
	}

	return slog.New(handler)
}

func runConfig() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading config: %v\n", err)
		fmt.Println("Creating default configuration...")
		cfg = config.Default()
		if saveErr := config.Save(cfg); saveErr != nil {
			fmt.Fprintf(os.Stderr, "Error saving default config: %v\n", saveErr)
			os.Exit(1)
		}
	}

	logger := setupLogger(cfg)
	logger.Info("starting web configurator", "port", cfg.ConfiguratorPort)

	fmt.Printf("Opening configurator at http://localhost:%d\n", cfg.ConfiguratorPort)
	srv := configurator.New(cfg, logger)
	if err := srv.ListenAndServe(); err != nil {
		logger.Error("configurator server error", "error", err)
		os.Exit(1)
	}
}

func runServe() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading config: %v\n", err)
		os.Exit(1)
	}

	logger := setupLogger(cfg)
	logger.Info("starting saicloud agent", "version", version)

	orch := sync.NewOrchestrator(cfg, logger)

	// RunAsService reports Running to Windows SCM before any sync work begins.
	// The context is cancelled by SCM on Stop/Shutdown, enabling graceful shutdown.
	if err := winsvc.RunAsService(func(ctx context.Context) { orch.RunWithContext(ctx) }); err != nil {
		logger.Error("service error", "error", err)
		os.Exit(1)
	}
}

func runInstall() {
	if err := winsvc.Install(); err != nil {
		fmt.Fprintf(os.Stderr, "Error installing service: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Saicloud Agent installed as Windows Service successfully.")
}

func runUninstall() {
	if err := winsvc.Uninstall(); err != nil {
		fmt.Fprintf(os.Stderr, "Error uninstalling service: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Saicloud Agent Windows Service removed successfully.")
}

func runStatus() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading config: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Saicloud Agent v%s\n", cfg.AgentVersion)
	fmt.Printf("Log Level: %s\n", cfg.LogLevel)
	fmt.Printf("Log File: %s\n", cfg.LogFile)
	fmt.Printf("Configurator Port: %d\n", cfg.ConfiguratorPort)
	fmt.Printf("\nConnections (%d):\n", len(cfg.Connections))
	fmt.Println(strings.Repeat("-", 80))

	for _, conn := range cfg.Connections {
		status := "DISABLED"
		if conn.Enabled {
			status = "ENABLED"
		}
		fmt.Printf("  [%s] %s (%s)\n", status, conn.Name, conn.ID)
		fmt.Printf("    Firebird: %s:%d %s\n", conn.Firebird.Host, conn.Firebird.Port, conn.Firebird.Database)
		fmt.Printf("    Saicloud: %s (company: %s)\n", conn.Saicloud.APIURL, conn.Saicloud.CompanyID)
		fmt.Printf("    GL Interval: %d min | Ref Interval: %d hrs | Batch Size: %d\n",
			conn.Sync.GLIntervalMinutes, conn.Sync.ReferenceIntervalHours, conn.Sync.BatchSize)
		fmt.Printf("    Last CONTEO GL: %d\n", conn.Sync.LastConteoGL)

		lastAcct := "never"
		if conn.Sync.LastSyncAcct != nil {
			lastAcct = conn.Sync.LastSyncAcct.Format("2006-01-02 15:04:05")
		}
		lastCust := "never"
		if conn.Sync.LastSyncCust != nil {
			lastCust = conn.Sync.LastSyncCust.Format("2006-01-02 15:04:05")
		}
		lastLista := "never"
		if conn.Sync.LastSyncLista != nil {
			lastLista = conn.Sync.LastSyncLista.Format("2006-01-02 15:04:05")
		}
		fmt.Printf("    Last Sync ACCT: %s | CUST: %s | LISTA: %s\n", lastAcct, lastCust, lastLista)
		fmt.Println()
	}
}

func runTest() {
	connID := ""
	for i, arg := range os.Args {
		if arg == "--id" && i+1 < len(os.Args) {
			connID = os.Args[i+1]
			break
		}
	}

	if connID == "" {
		fmt.Fprintln(os.Stderr, "Error: --id <conn_id> is required")
		fmt.Fprintln(os.Stderr, "Usage: agent.exe test --id conn_001")
		os.Exit(1)
	}

	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading config: %v\n", err)
		os.Exit(1)
	}

	logger := setupLogger(cfg)

	conn := cfg.FindConnection(connID)
	if conn == nil {
		fmt.Fprintf(os.Stderr, "Error: connection '%s' not found\n", connID)
		os.Exit(1)
	}

	fmt.Printf("Testing connection: %s (%s)\n", conn.Name, conn.ID)
	fmt.Println(strings.Repeat("-", 50))

	orch := sync.NewOrchestrator(cfg, logger)
	if err := orch.TestConnection(conn); err != nil {
		fmt.Fprintf(os.Stderr, "Connection test FAILED: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Connection test PASSED.")
}
