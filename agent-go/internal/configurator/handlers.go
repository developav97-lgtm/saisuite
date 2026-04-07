package configurator

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
	sqspkg "github.com/valmentech/saicloud-agent/internal/sqs"
)

// Handlers implements the REST API handlers for the configurator.
type Handlers struct {
	cfg    *config.AgentConfig
	logger *slog.Logger
}

// NewHandlers creates a new set of REST handlers.
func NewHandlers(cfg *config.AgentConfig, logger *slog.Logger) *Handlers {
	return &Handlers{
		cfg:    cfg,
		logger: logger,
	}
}

// jsonResponse is a helper to write JSON responses.
type jsonResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func writeJSON(w http.ResponseWriter, status int, resp jsonResponse) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(resp)
}

// ListConnections returns all configured connections.
// GET /api/connections
func (h *Handlers) ListConnections(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
		Data:    h.cfg.Connections,
	})
}

// GetConnection returns a single connection by ID.
// GET /api/connections/{id}
func (h *Handlers) GetConnection(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	conn := h.cfg.FindConnection(id)
	if conn == nil {
		writeJSON(w, http.StatusNotFound, jsonResponse{
			Error: fmt.Sprintf("connection '%s' not found", id),
		})
		return
	}

	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
		Data:    conn,
	})
}

// CreateConnection adds a new connection to the configuration.
// POST /api/connections
func (h *Handlers) CreateConnection(w http.ResponseWriter, r *http.Request) {
	var conn config.Connection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: fmt.Sprintf("invalid JSON: %v", err),
		})
		return
	}

	// Validate required fields
	if conn.ID == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "connection ID is required",
		})
		return
	}
	if conn.Name == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "connection name is required",
		})
		return
	}
	if conn.Firebird.Database == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "firebird database path is required",
		})
		return
	}
	if conn.Saicloud.APIURL == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "saicloud API URL is required",
		})
		return
	}
	if conn.Saicloud.CompanyID == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "saicloud company ID is required",
		})
		return
	}
	if conn.Saicloud.AgentToken == "" {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: "saicloud agent token is required",
		})
		return
	}

	// Apply defaults
	if conn.Firebird.Host == "" {
		conn.Firebird.Host = "localhost"
	}
	if conn.Firebird.Port == 0 {
		conn.Firebird.Port = 3050
	}
	if conn.Firebird.User == "" {
		conn.Firebird.User = "SYSDBA"
	}
	if conn.Firebird.Password == "" {
		conn.Firebird.Password = "masterkey"
	}
	if conn.Sync.GLIntervalMinutes == 0 {
		conn.Sync.GLIntervalMinutes = 15
	}
	if conn.Sync.ReferenceIntervalHours == 0 {
		conn.Sync.ReferenceIntervalHours = 24
	}
	if conn.Sync.BatchSize == 0 {
		conn.Sync.BatchSize = 500
	}

	if err := h.cfg.AddConnection(conn); err != nil {
		writeJSON(w, http.StatusConflict, jsonResponse{
			Error: err.Error(),
		})
		return
	}

	if err := config.Save(h.cfg); err != nil {
		writeJSON(w, http.StatusInternalServerError, jsonResponse{
			Error: fmt.Sprintf("failed to save config: %v", err),
		})
		return
	}

	h.logger.Info("connection created", "conn_id", conn.ID, "conn_name", conn.Name)
	writeJSON(w, http.StatusCreated, jsonResponse{
		Success: true,
		Data:    conn,
	})
}

// UpdateConnection updates an existing connection.
// PUT /api/connections/{id}
func (h *Handlers) UpdateConnection(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")

	var conn config.Connection
	if err := json.NewDecoder(r.Body).Decode(&conn); err != nil {
		writeJSON(w, http.StatusBadRequest, jsonResponse{
			Error: fmt.Sprintf("invalid JSON: %v", err),
		})
		return
	}

	// Ensure the path ID matches the body ID
	conn.ID = id

	if err := h.cfg.UpdateConnection(conn); err != nil {
		writeJSON(w, http.StatusNotFound, jsonResponse{
			Error: err.Error(),
		})
		return
	}

	if err := config.Save(h.cfg); err != nil {
		writeJSON(w, http.StatusInternalServerError, jsonResponse{
			Error: fmt.Sprintf("failed to save config: %v", err),
		})
		return
	}

	h.logger.Info("connection updated", "conn_id", conn.ID)
	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
		Data:    conn,
	})
}

// DeleteConnection removes a connection from the configuration.
// DELETE /api/connections/{id}
func (h *Handlers) DeleteConnection(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")

	if err := h.cfg.RemoveConnection(id); err != nil {
		writeJSON(w, http.StatusNotFound, jsonResponse{
			Error: err.Error(),
		})
		return
	}

	if err := config.Save(h.cfg); err != nil {
		writeJSON(w, http.StatusInternalServerError, jsonResponse{
			Error: fmt.Sprintf("failed to save config: %v", err),
		})
		return
	}

	h.logger.Info("connection deleted", "conn_id", id)
	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
	})
}

// TestConnectionResult contains the results of testing a connection.
type TestConnectionResult struct {
	FirebirdOK   bool   `json:"firebird_ok"`
	FirebirdMsg  string `json:"firebird_msg"`
	SaicloudOK   bool   `json:"saicloud_ok"`
	SaicloudMsg  string `json:"saicloud_msg"`
	GLCount      int64  `json:"gl_count"`
	MaxConteo    int64  `json:"max_conteo"`
	PendingCount int64  `json:"pending_count"`
}

// TestConnection tests both the Firebird and Saicloud connections.
// POST /api/connections/{id}/test
func (h *Handlers) TestConnection(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	conn := h.cfg.FindConnection(id)
	if conn == nil {
		writeJSON(w, http.StatusNotFound, jsonResponse{
			Error: fmt.Sprintf("connection '%s' not found", id),
		})
		return
	}

	result := TestConnectionResult{}

	// Test Firebird
	fbClient := firebird.New(conn.Firebird.DSN(), h.logger)
	if err := fbClient.Connect(); err != nil {
		result.FirebirdOK = false
		result.FirebirdMsg = fmt.Sprintf("Connection failed: %v", err)
	} else {
		defer fbClient.Close()
		total, maxConteo, err := fbClient.CountGL()
		if err != nil {
			result.FirebirdOK = false
			result.FirebirdMsg = fmt.Sprintf("GL query failed: %v", err)
		} else {
			result.FirebirdOK = true
			result.FirebirdMsg = "Connection successful"
			result.GLCount = total
			result.MaxConteo = maxConteo
			pending := maxConteo - conn.Sync.LastConteoGL
			if pending < 0 {
				pending = 0
			}
			result.PendingCount = pending
		}
	}

	// Test Saicloud connection (SQS or HTTP depending on transport)
	if h.cfg.Transport == "sqs" {
		sqsCfg := h.cfg.SQS
		pub := sqspkg.New(sqsCfg.AccessKeyID, sqsCfg.SecretAccessKey, sqsCfg.Region, sqsCfg.QueueURL, h.logger)
		if err := pub.Ping(r.Context()); err != nil {
			result.SaicloudOK = false
			result.SaicloudMsg = fmt.Sprintf("SQS check failed: %v", err)
		} else {
			result.SaicloudOK = true
			result.SaicloudMsg = fmt.Sprintf("SQS queue reachable (%s)", sqsCfg.QueueURL)
		}
	} else {
		apiClient := api.NewClient(conn.Saicloud.APIURL, conn.Saicloud.AgentToken, h.logger)
		if err := apiClient.HealthCheck(); err != nil {
			result.SaicloudOK = false
			result.SaicloudMsg = fmt.Sprintf("API check failed: %v", err)
		} else {
			result.SaicloudOK = true
			result.SaicloudMsg = "API connection successful"
		}
	}

	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
		Data:    result,
	})
}

// StatusInfo contains the overall agent status.
type StatusInfo struct {
	Version          string `json:"version"`
	LogLevel         string `json:"log_level"`
	TotalConnections int    `json:"total_connections"`
	EnabledCount     int    `json:"enabled_count"`
}

// GetStatus returns the overall agent status.
// GET /api/status
func (h *Handlers) GetStatus(w http.ResponseWriter, r *http.Request) {
	enabled := h.cfg.EnabledConnections()
	writeJSON(w, http.StatusOK, jsonResponse{
		Success: true,
		Data: StatusInfo{
			Version:          h.cfg.AgentVersion,
			LogLevel:         h.cfg.LogLevel,
			TotalConnections: len(h.cfg.Connections),
			EnabledCount:     len(enabled),
		},
	})
}
