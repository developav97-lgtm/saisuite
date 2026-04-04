package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDefault(t *testing.T) {
	cfg := Default()

	if cfg.AgentVersion != "1.0.0" {
		t.Errorf("expected version 1.0.0, got %s", cfg.AgentVersion)
	}
	if cfg.ConfiguratorPort != 8765 {
		t.Errorf("expected port 8765, got %d", cfg.ConfiguratorPort)
	}
	if len(cfg.Connections) != 1 {
		t.Fatalf("expected 1 default connection, got %d", len(cfg.Connections))
	}
	if cfg.Connections[0].ID != "conn_001" {
		t.Errorf("expected conn_001, got %s", cfg.Connections[0].ID)
	}
	if cfg.Connections[0].Enabled {
		t.Error("default connection should be disabled")
	}
}

func TestLoadAndSave(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-config.json")

	// Create config
	cfg := Default()
	cfg.Connections = append(cfg.Connections, Connection{
		ID:      "conn_002",
		Name:    "Second Company",
		Enabled: true,
		Firebird: FirebirdConfig{
			Host:     "192.168.1.100",
			Port:     3050,
			Database: "C:/DATA/EMPRESA2.FDB",
			User:     "SYSDBA",
			Password: "secret",
		},
		Saicloud: SaicloudConfig{
			APIURL:     "https://api.saicloud.co",
			CompanyID:  "uuid-empresa-2",
			AgentToken: "token-2",
		},
		Sync: SyncConfig{
			GLIntervalMinutes:      10,
			ReferenceIntervalHours: 12,
			BatchSize:              1000,
			LastConteoGL:           50000,
		},
	})

	// Save
	if err := SaveToPath(cfg, path); err != nil {
		t.Fatalf("SaveToPath failed: %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(path); os.IsNotExist(err) {
		t.Fatal("config file was not created")
	}

	// Load back
	loaded, err := LoadFromPath(path)
	if err != nil {
		t.Fatalf("LoadFromPath failed: %v", err)
	}

	if len(loaded.Connections) != 2 {
		t.Fatalf("expected 2 connections, got %d", len(loaded.Connections))
	}

	// Verify second connection
	conn2 := loaded.FindConnection("conn_002")
	if conn2 == nil {
		t.Fatal("conn_002 not found")
	}
	if conn2.Name != "Second Company" {
		t.Errorf("expected 'Second Company', got '%s'", conn2.Name)
	}
	if !conn2.Enabled {
		t.Error("conn_002 should be enabled")
	}
	if conn2.Firebird.Host != "192.168.1.100" {
		t.Errorf("expected host 192.168.1.100, got %s", conn2.Firebird.Host)
	}
	if conn2.Sync.LastConteoGL != 50000 {
		t.Errorf("expected last_conteo_gl 50000, got %d", conn2.Sync.LastConteoGL)
	}
	if conn2.Sync.BatchSize != 1000 {
		t.Errorf("expected batch_size 1000, got %d", conn2.Sync.BatchSize)
	}
}

func TestLoadAppliesDefaults(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test-defaults.json")

	// Write a minimal config with missing sync defaults
	minimalJSON := `{
		"agent_version": "1.0.0",
		"configurator_port": 8765,
		"log_level": "debug",
		"connections": [{
			"id": "conn_minimal",
			"name": "Minimal",
			"enabled": true,
			"firebird": {
				"host": "localhost",
				"database": "C:/DATA/TEST.FDB",
				"user": "SYSDBA",
				"password": "pw"
			},
			"saicloud": {
				"api_url": "https://api.test.co",
				"company_id": "uuid-test",
				"agent_token": "tok"
			},
			"sync": {
				"last_conteo_gl": 100
			}
		}]
	}`

	if err := os.WriteFile(path, []byte(minimalJSON), 0644); err != nil {
		t.Fatalf("failed to write test config: %v", err)
	}

	cfg, err := LoadFromPath(path)
	if err != nil {
		t.Fatalf("LoadFromPath failed: %v", err)
	}

	conn := cfg.FindConnection("conn_minimal")
	if conn == nil {
		t.Fatal("conn_minimal not found")
	}

	// Defaults should be applied
	if conn.Sync.BatchSize != 500 {
		t.Errorf("expected default batch_size 500, got %d", conn.Sync.BatchSize)
	}
	if conn.Sync.GLIntervalMinutes != 15 {
		t.Errorf("expected default gl_interval 15, got %d", conn.Sync.GLIntervalMinutes)
	}
	if conn.Sync.ReferenceIntervalHours != 24 {
		t.Errorf("expected default ref_interval 24, got %d", conn.Sync.ReferenceIntervalHours)
	}
	if conn.Firebird.Port != 3050 {
		t.Errorf("expected default port 3050, got %d", conn.Firebird.Port)
	}
	// Explicit value should be preserved
	if conn.Sync.LastConteoGL != 100 {
		t.Errorf("expected last_conteo_gl 100, got %d", conn.Sync.LastConteoGL)
	}
}

func TestFindConnection(t *testing.T) {
	cfg := Default()

	found := cfg.FindConnection("conn_001")
	if found == nil {
		t.Fatal("expected to find conn_001")
	}

	notFound := cfg.FindConnection("nonexistent")
	if notFound != nil {
		t.Error("expected nil for nonexistent connection")
	}
}

func TestAddConnection(t *testing.T) {
	cfg := Default()

	newConn := Connection{
		ID:   "conn_new",
		Name: "New Connection",
	}

	if err := cfg.AddConnection(newConn); err != nil {
		t.Fatalf("AddConnection failed: %v", err)
	}

	if len(cfg.Connections) != 2 {
		t.Fatalf("expected 2 connections, got %d", len(cfg.Connections))
	}

	// Adding duplicate should fail
	if err := cfg.AddConnection(newConn); err == nil {
		t.Error("expected error when adding duplicate connection ID")
	}
}

func TestUpdateConnection(t *testing.T) {
	cfg := Default()

	updated := cfg.Connections[0]
	updated.Name = "Updated Name"
	updated.Enabled = true

	if err := cfg.UpdateConnection(updated); err != nil {
		t.Fatalf("UpdateConnection failed: %v", err)
	}

	conn := cfg.FindConnection("conn_001")
	if conn.Name != "Updated Name" {
		t.Errorf("expected 'Updated Name', got '%s'", conn.Name)
	}
	if !conn.Enabled {
		t.Error("expected connection to be enabled")
	}

	// Updating nonexistent should fail
	if err := cfg.UpdateConnection(Connection{ID: "nonexistent"}); err == nil {
		t.Error("expected error when updating nonexistent connection")
	}
}

func TestRemoveConnection(t *testing.T) {
	cfg := Default()
	cfg.AddConnection(Connection{ID: "conn_002", Name: "To Remove"})

	if err := cfg.RemoveConnection("conn_002"); err != nil {
		t.Fatalf("RemoveConnection failed: %v", err)
	}

	if len(cfg.Connections) != 1 {
		t.Errorf("expected 1 connection after removal, got %d", len(cfg.Connections))
	}

	// Removing nonexistent should fail
	if err := cfg.RemoveConnection("nonexistent"); err == nil {
		t.Error("expected error when removing nonexistent connection")
	}
}

func TestUpdateWatermark(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "watermark-test.json")

	cfg := Default()
	cfg.filePath = path

	// Save initial config
	if err := SaveToPath(cfg, path); err != nil {
		t.Fatalf("initial save failed: %v", err)
	}

	// Update watermark
	if err := cfg.UpdateWatermark("conn_001", 99999); err != nil {
		t.Fatalf("UpdateWatermark failed: %v", err)
	}

	// Verify in-memory
	conn := cfg.FindConnection("conn_001")
	if conn.Sync.LastConteoGL != 99999 {
		t.Errorf("expected watermark 99999, got %d", conn.Sync.LastConteoGL)
	}

	// Verify persisted
	reloaded, err := LoadFromPath(path)
	if err != nil {
		t.Fatalf("reload failed: %v", err)
	}
	rConn := reloaded.FindConnection("conn_001")
	if rConn.Sync.LastConteoGL != 99999 {
		t.Errorf("expected persisted watermark 99999, got %d", rConn.Sync.LastConteoGL)
	}

	// Nonexistent connection
	if err := cfg.UpdateWatermark("nonexistent", 1); err == nil {
		t.Error("expected error for nonexistent connection")
	}
}

func TestUpdateReferenceSyncTime(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "refsync-test.json")

	cfg := Default()
	cfg.filePath = path

	if err := SaveToPath(cfg, path); err != nil {
		t.Fatalf("initial save failed: %v", err)
	}

	tables := []string{"acct", "cust", "lista", "proyectos", "actividades"}
	for _, table := range tables {
		if err := cfg.UpdateReferenceSyncTime("conn_001", table); err != nil {
			t.Fatalf("UpdateReferenceSyncTime(%s) failed: %v", table, err)
		}
	}

	conn := cfg.FindConnection("conn_001")
	if conn.Sync.LastSyncAcct == nil {
		t.Error("LastSyncAcct should not be nil")
	}
	if conn.Sync.LastSyncCust == nil {
		t.Error("LastSyncCust should not be nil")
	}
	if conn.Sync.LastSyncLista == nil {
		t.Error("LastSyncLista should not be nil")
	}
	if conn.Sync.LastSyncProyectos == nil {
		t.Error("LastSyncProyectos should not be nil")
	}
	if conn.Sync.LastSyncActividades == nil {
		t.Error("LastSyncActividades should not be nil")
	}

	// Invalid table
	if err := cfg.UpdateReferenceSyncTime("conn_001", "invalid_table"); err == nil {
		t.Error("expected error for invalid table name")
	}

	// Nonexistent connection
	if err := cfg.UpdateReferenceSyncTime("nonexistent", "acct"); err == nil {
		t.Error("expected error for nonexistent connection")
	}
}

func TestEnabledConnections(t *testing.T) {
	cfg := Default()
	cfg.Connections[0].Enabled = false

	cfg.AddConnection(Connection{ID: "conn_002", Name: "Enabled One", Enabled: true})
	cfg.AddConnection(Connection{ID: "conn_003", Name: "Enabled Two", Enabled: true})
	cfg.AddConnection(Connection{ID: "conn_004", Name: "Disabled Two", Enabled: false})

	enabled := cfg.EnabledConnections()
	if len(enabled) != 2 {
		t.Errorf("expected 2 enabled connections, got %d", len(enabled))
	}
}

func TestFirebirdDSN(t *testing.T) {
	fc := FirebirdConfig{
		Host:     "localhost",
		Port:     3050,
		Database: "C:/SAIOPEN/DATOS/EMPRESA1.FDB",
		User:     "SYSDBA",
		Password: "masterkey",
	}

	expected := "SYSDBA:masterkey@localhost:3050/C:/SAIOPEN/DATOS/EMPRESA1.FDB"
	if dsn := fc.DSN(); dsn != expected {
		t.Errorf("expected DSN '%s', got '%s'", expected, dsn)
	}
}

func TestJSONSerialization(t *testing.T) {
	now := time.Now().UTC()
	cfg := &AgentConfig{
		AgentVersion:    "1.0.0",
		ConfiguratorPort: 8765,
		LogLevel:        "info",
		Connections: []Connection{
			{
				ID:      "conn_001",
				Name:    "Test Co",
				Enabled: true,
				Sync: SyncConfig{
					LastConteoGL:   12345,
					LastSyncAcct:   &now,
					BatchSize:      500,
				},
			},
		},
	}

	data, err := json.Marshal(cfg)
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	var decoded AgentConfig
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}

	if decoded.Connections[0].Sync.LastConteoGL != 12345 {
		t.Errorf("expected last_conteo_gl 12345 after roundtrip, got %d",
			decoded.Connections[0].Sync.LastConteoGL)
	}

	if decoded.Connections[0].Sync.LastSyncAcct == nil {
		t.Fatal("expected LastSyncAcct to survive roundtrip")
	}
}

func TestMultiConnectionConfig(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "multi-conn.json")

	cfg := &AgentConfig{
		AgentVersion:    "1.0.0",
		ConfiguratorPort: 8765,
		LogLevel:        "info",
		LogFile:         "",
		Connections: []Connection{
			{
				ID:      "ferreteria",
				Name:    "Ferreteria El Tornillo S.A.S",
				Enabled: true,
				Firebird: FirebirdConfig{
					Host:     "localhost",
					Port:     3050,
					Database: "C:/SAIOPEN/DATOS/FERRETERIA.FDB",
					User:     "SYSDBA",
					Password: "masterkey",
				},
				Saicloud: SaicloudConfig{
					APIURL:     "https://api.saicloud.co",
					CompanyID:  "uuid-ferreteria",
					AgentToken: "token-ferreteria",
				},
				Sync: SyncConfig{
					GLIntervalMinutes:      15,
					ReferenceIntervalHours: 24,
					BatchSize:              500,
					LastConteoGL:           100000,
				},
			},
			{
				ID:      "drogueria",
				Name:    "Drogueria Salud Total S.A.S",
				Enabled: true,
				Firebird: FirebirdConfig{
					Host:     "localhost",
					Port:     3050,
					Database: "C:/SAIOPEN/DATOS/DROGUERIA.FDB",
					User:     "SYSDBA",
					Password: "masterkey",
				},
				Saicloud: SaicloudConfig{
					APIURL:     "https://api.saicloud.co",
					CompanyID:  "uuid-drogueria",
					AgentToken: "token-drogueria",
				},
				Sync: SyncConfig{
					GLIntervalMinutes:      30,
					ReferenceIntervalHours: 48,
					BatchSize:              1000,
					LastConteoGL:           0,
				},
			},
			{
				ID:      "textiles",
				Name:    "Textiles Colombia Ltda",
				Enabled: false,
				Firebird: FirebirdConfig{
					Host:     "192.168.1.200",
					Port:     3050,
					Database: "D:/DATA/TEXTILES.FDB",
					User:     "SYSDBA",
					Password: "textilespass",
				},
				Saicloud: SaicloudConfig{
					APIURL:     "https://api.saicloud.co",
					CompanyID:  "uuid-textiles",
					AgentToken: "token-textiles",
				},
				Sync: SyncConfig{
					GLIntervalMinutes:      15,
					ReferenceIntervalHours: 24,
					BatchSize:              500,
					LastConteoGL:           50000,
				},
			},
		},
	}

	// Save
	if err := SaveToPath(cfg, path); err != nil {
		t.Fatalf("save failed: %v", err)
	}

	// Reload
	loaded, err := LoadFromPath(path)
	if err != nil {
		t.Fatalf("load failed: %v", err)
	}

	if len(loaded.Connections) != 3 {
		t.Fatalf("expected 3 connections, got %d", len(loaded.Connections))
	}

	// Only 2 should be enabled
	enabled := loaded.EnabledConnections()
	if len(enabled) != 2 {
		t.Errorf("expected 2 enabled, got %d", len(enabled))
	}

	// Verify each connection
	ferr := loaded.FindConnection("ferreteria")
	if ferr == nil || ferr.Sync.LastConteoGL != 100000 {
		t.Error("ferreteria connection data incorrect")
	}

	drog := loaded.FindConnection("drogueria")
	if drog == nil || drog.Sync.BatchSize != 1000 {
		t.Error("drogueria connection data incorrect")
	}

	text := loaded.FindConnection("textiles")
	if text == nil || text.Enabled {
		t.Error("textiles should exist and be disabled")
	}

	// Update watermarks independently
	loaded.filePath = path
	if err := loaded.UpdateWatermark("ferreteria", 100500); err != nil {
		t.Fatalf("watermark update failed: %v", err)
	}
	if err := loaded.UpdateWatermark("drogueria", 1000); err != nil {
		t.Fatalf("watermark update failed: %v", err)
	}

	// Verify independence
	f2 := loaded.FindConnection("ferreteria")
	d2 := loaded.FindConnection("drogueria")
	if f2.Sync.LastConteoGL != 100500 {
		t.Errorf("ferreteria watermark should be 100500, got %d", f2.Sync.LastConteoGL)
	}
	if d2.Sync.LastConteoGL != 1000 {
		t.Errorf("drogueria watermark should be 1000, got %d", d2.Sync.LastConteoGL)
	}
}
