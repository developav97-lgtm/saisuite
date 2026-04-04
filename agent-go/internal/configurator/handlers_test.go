package configurator

import (
	"bytes"
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/valmentech/saicloud-agent/internal/config"
)

func setupTest(t *testing.T) (*Handlers, *config.AgentConfig) {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	cfg := config.Default()
	if err := config.SaveToPath(cfg, path); err != nil {
		t.Fatalf("failed to save initial config: %v", err)
	}

	// Reload so filePath is set
	cfg, err := config.LoadFromPath(path)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))
	return NewHandlers(cfg, logger), cfg
}

func TestListConnections(t *testing.T) {
	h, _ := setupTest(t)

	req := httptest.NewRequest("GET", "/api/connections", nil)
	w := httptest.NewRecorder()

	h.ListConnections(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	var resp jsonResponse
	json.NewDecoder(w.Body).Decode(&resp)
	if !resp.Success {
		t.Error("expected success=true")
	}
}

func TestGetConnection(t *testing.T) {
	h, _ := setupTest(t)

	// Use the Go 1.22 mux pattern matching
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/connections/{id}", h.GetConnection)

	// Test existing connection
	req := httptest.NewRequest("GET", "/api/connections/conn_001", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	// Test nonexistent connection
	req = httptest.NewRequest("GET", "/api/connections/nonexistent", nil)
	w = httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}
}

func TestCreateConnection(t *testing.T) {
	h, _ := setupTest(t)

	newConn := config.Connection{
		ID:      "conn_new",
		Name:    "New Test Company",
		Enabled: true,
		Firebird: config.FirebirdConfig{
			Host:     "localhost",
			Port:     3050,
			Database: "C:/DATA/NEW.FDB",
			User:     "SYSDBA",
			Password: "masterkey",
		},
		Saicloud: config.SaicloudConfig{
			APIURL:     "https://api.saicloud.co",
			CompanyID:  "uuid-new",
			AgentToken: "token-new",
		},
		Sync: config.SyncConfig{
			GLIntervalMinutes:      10,
			ReferenceIntervalHours: 12,
			BatchSize:              1000,
		},
	}

	body, _ := json.Marshal(newConn)
	req := httptest.NewRequest("POST", "/api/connections", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateConnection(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("expected status 201, got %d; body: %s", w.Code, w.Body.String())
	}

	var resp jsonResponse
	json.NewDecoder(w.Body).Decode(&resp)
	if !resp.Success {
		t.Error("expected success=true")
	}
}

func TestCreateConnectionDuplicate(t *testing.T) {
	h, _ := setupTest(t)

	// Try to create with same ID as existing connection
	duplicate := config.Connection{
		ID:   "conn_001",
		Name: "Duplicate",
		Firebird: config.FirebirdConfig{
			Database: "C:/DATA/DUP.FDB",
		},
		Saicloud: config.SaicloudConfig{
			APIURL:     "https://api.test.co",
			CompanyID:  "uuid-dup",
			AgentToken: "tok",
		},
	}

	body, _ := json.Marshal(duplicate)
	req := httptest.NewRequest("POST", "/api/connections", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateConnection(w, req)

	if w.Code != http.StatusConflict {
		t.Errorf("expected status 409, got %d", w.Code)
	}
}

func TestCreateConnectionValidation(t *testing.T) {
	h, _ := setupTest(t)

	tests := []struct {
		name     string
		conn     config.Connection
		expected int
	}{
		{
			name:     "missing ID",
			conn:     config.Connection{Name: "Test"},
			expected: http.StatusBadRequest,
		},
		{
			name:     "missing name",
			conn:     config.Connection{ID: "test"},
			expected: http.StatusBadRequest,
		},
		{
			name: "missing database",
			conn: config.Connection{
				ID:   "test",
				Name: "Test",
			},
			expected: http.StatusBadRequest,
		},
		{
			name: "missing API URL",
			conn: config.Connection{
				ID:       "test",
				Name:     "Test",
				Firebird: config.FirebirdConfig{Database: "C:/test.fdb"},
			},
			expected: http.StatusBadRequest,
		},
		{
			name: "missing company ID",
			conn: config.Connection{
				ID:       "test",
				Name:     "Test",
				Firebird: config.FirebirdConfig{Database: "C:/test.fdb"},
				Saicloud: config.SaicloudConfig{APIURL: "https://api.test.co"},
			},
			expected: http.StatusBadRequest,
		},
		{
			name: "missing agent token",
			conn: config.Connection{
				ID:       "test",
				Name:     "Test",
				Firebird: config.FirebirdConfig{Database: "C:/test.fdb"},
				Saicloud: config.SaicloudConfig{APIURL: "https://api.test.co", CompanyID: "uuid"},
			},
			expected: http.StatusBadRequest,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			body, _ := json.Marshal(tc.conn)
			req := httptest.NewRequest("POST", "/api/connections", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			h.CreateConnection(w, req)

			if w.Code != tc.expected {
				t.Errorf("expected status %d, got %d; body: %s", tc.expected, w.Code, w.Body.String())
			}
		})
	}
}

func TestUpdateConnection(t *testing.T) {
	h, _ := setupTest(t)

	updated := config.Connection{
		ID:      "conn_001",
		Name:    "Updated Name",
		Enabled: true,
		Firebird: config.FirebirdConfig{
			Host:     "192.168.1.100",
			Port:     3050,
			Database: "C:/DATA/UPDATED.FDB",
			User:     "SYSDBA",
			Password: "newpass",
		},
		Saicloud: config.SaicloudConfig{
			APIURL:     "https://api.updated.co",
			CompanyID:  "uuid-updated",
			AgentToken: "token-updated",
		},
		Sync: config.SyncConfig{
			GLIntervalMinutes:      5,
			ReferenceIntervalHours: 6,
			BatchSize:              2000,
		},
	}

	mux := http.NewServeMux()
	mux.HandleFunc("PUT /api/connections/{id}", h.UpdateConnection)

	body, _ := json.Marshal(updated)
	req := httptest.NewRequest("PUT", "/api/connections/conn_001", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d; body: %s", w.Code, w.Body.String())
	}

	// Verify update took effect
	conn := h.cfg.FindConnection("conn_001")
	if conn.Name != "Updated Name" {
		t.Errorf("expected 'Updated Name', got '%s'", conn.Name)
	}
	if !conn.Enabled {
		t.Error("expected connection to be enabled")
	}
}

func TestUpdateConnectionNotFound(t *testing.T) {
	h, _ := setupTest(t)

	mux := http.NewServeMux()
	mux.HandleFunc("PUT /api/connections/{id}", h.UpdateConnection)

	body, _ := json.Marshal(config.Connection{ID: "nonexistent"})
	req := httptest.NewRequest("PUT", "/api/connections/nonexistent", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}
}

func TestDeleteConnection(t *testing.T) {
	h, cfg := setupTest(t)

	// Add a second connection to delete
	cfg.AddConnection(config.Connection{ID: "conn_to_delete", Name: "Delete Me"})

	mux := http.NewServeMux()
	mux.HandleFunc("DELETE /api/connections/{id}", h.DeleteConnection)

	req := httptest.NewRequest("DELETE", "/api/connections/conn_to_delete", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d; body: %s", w.Code, w.Body.String())
	}

	// Verify deletion
	if cfg.FindConnection("conn_to_delete") != nil {
		t.Error("connection should have been deleted")
	}
}

func TestDeleteConnectionNotFound(t *testing.T) {
	h, _ := setupTest(t)

	mux := http.NewServeMux()
	mux.HandleFunc("DELETE /api/connections/{id}", h.DeleteConnection)

	req := httptest.NewRequest("DELETE", "/api/connections/nonexistent", nil)
	w := httptest.NewRecorder()
	mux.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}
}

func TestGetStatus(t *testing.T) {
	h, cfg := setupTest(t)

	// Enable one connection
	conn := cfg.FindConnection("conn_001")
	conn.Enabled = true

	req := httptest.NewRequest("GET", "/api/status", nil)
	w := httptest.NewRecorder()

	h.GetStatus(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	var resp jsonResponse
	json.NewDecoder(w.Body).Decode(&resp)
	if !resp.Success {
		t.Error("expected success=true")
	}

	// Verify status data
	data, ok := resp.Data.(map[string]interface{})
	if !ok {
		t.Fatal("expected data to be a map")
	}

	if v, ok := data["total_connections"]; !ok || v.(float64) != 1 {
		t.Errorf("expected total_connections=1, got %v", data["total_connections"])
	}
	if v, ok := data["enabled_count"]; !ok || v.(float64) != 1 {
		t.Errorf("expected enabled_count=1, got %v", data["enabled_count"])
	}
}

func TestCreateConnectionDefaults(t *testing.T) {
	h, _ := setupTest(t)

	// Create with minimal required fields, relying on defaults
	conn := config.Connection{
		ID:   "conn_defaults",
		Name: "Defaults Test",
		Firebird: config.FirebirdConfig{
			Database: "C:/DATA/TEST.FDB",
		},
		Saicloud: config.SaicloudConfig{
			APIURL:     "https://api.test.co",
			CompanyID:  "uuid-test",
			AgentToken: "tok-test",
		},
	}

	body, _ := json.Marshal(conn)
	req := httptest.NewRequest("POST", "/api/connections", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateConnection(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("expected status 201, got %d; body: %s", w.Code, w.Body.String())
	}

	// Verify defaults were applied
	created := h.cfg.FindConnection("conn_defaults")
	if created == nil {
		t.Fatal("connection not found")
	}
	if created.Firebird.Host != "localhost" {
		t.Errorf("expected default host 'localhost', got '%s'", created.Firebird.Host)
	}
	if created.Firebird.Port != 3050 {
		t.Errorf("expected default port 3050, got %d", created.Firebird.Port)
	}
	if created.Firebird.User != "SYSDBA" {
		t.Errorf("expected default user 'SYSDBA', got '%s'", created.Firebird.User)
	}
	if created.Sync.GLIntervalMinutes != 15 {
		t.Errorf("expected default GL interval 15, got %d", created.Sync.GLIntervalMinutes)
	}
	if created.Sync.ReferenceIntervalHours != 24 {
		t.Errorf("expected default ref interval 24, got %d", created.Sync.ReferenceIntervalHours)
	}
	if created.Sync.BatchSize != 500 {
		t.Errorf("expected default batch size 500, got %d", created.Sync.BatchSize)
	}
}

func TestInvalidJSON(t *testing.T) {
	h, _ := setupTest(t)

	req := httptest.NewRequest("POST", "/api/connections", bytes.NewReader([]byte("not json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateConnection(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected status 400, got %d", w.Code)
	}
}
