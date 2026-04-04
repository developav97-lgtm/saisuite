// Package configurator provides a web-based UI for managing the Saicloud Agent
// configuration. It serves a single-page application on a local port and exposes
// REST endpoints for CRUD operations on connections and connection testing.
package configurator

import (
	"embed"
	"fmt"
	"io/fs"
	"log/slog"
	"net/http"
	"os/exec"
	"runtime"

	"github.com/valmentech/saicloud-agent/internal/config"
)

//go:embed static/*
var staticFiles embed.FS

// Server is the web configurator HTTP server.
type Server struct {
	cfg    *config.AgentConfig
	logger *slog.Logger
	port   int
}

// New creates a new configurator server.
func New(cfg *config.AgentConfig, logger *slog.Logger) *Server {
	return &Server{
		cfg:    cfg,
		logger: logger,
		port:   cfg.ConfiguratorPort,
	}
}

// ListenAndServe starts the HTTP server and opens the browser.
func (s *Server) ListenAndServe() error {
	mux := http.NewServeMux()

	// API routes
	h := NewHandlers(s.cfg, s.logger)
	mux.HandleFunc("GET /api/connections", h.ListConnections)
	mux.HandleFunc("POST /api/connections", h.CreateConnection)
	mux.HandleFunc("GET /api/connections/{id}", h.GetConnection)
	mux.HandleFunc("PUT /api/connections/{id}", h.UpdateConnection)
	mux.HandleFunc("DELETE /api/connections/{id}", h.DeleteConnection)
	mux.HandleFunc("POST /api/connections/{id}/test", h.TestConnection)
	mux.HandleFunc("GET /api/status", h.GetStatus)

	// Static files
	staticFS, err := fs.Sub(staticFiles, "static")
	if err != nil {
		return fmt.Errorf("failed to create static file sub-filesystem: %w", err)
	}
	mux.Handle("/", http.FileServer(http.FS(staticFS)))

	addr := fmt.Sprintf(":%d", s.port)
	s.logger.Info("starting configurator", "addr", addr)

	// Open browser automatically
	go openBrowser(fmt.Sprintf("http://localhost:%d", s.port))

	return http.ListenAndServe(addr, mux)
}

// openBrowser opens the default browser with the given URL.
func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("cmd", "/c", "start", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	_ = cmd.Start()
}
