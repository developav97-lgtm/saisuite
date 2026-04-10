// Package config manages the agent configuration file (saicloud-agent.json).
// It handles reading, writing, and updating watermarks for multi-connection sync state.
package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// SQSConfig holds the AWS SQS configuration for the agent transport layer.
// When Transport is "sqs", the agent sends data to SQS instead of posting
// directly to the Django API. The Django backend consumes from SQS.
type SQSConfig struct {
	AccessKeyID     string `json:"access_key_id"`
	SecretAccessKey string `json:"secret_access_key"`
	Region          string `json:"region"`
	QueueURL        string `json:"queue_url"`
}

// AgentConfig is the root configuration for the Saicloud Agent.
type AgentConfig struct {
	AgentVersion     string       `json:"agent_version"`
	ConfiguratorPort int          `json:"configurator_port"`
	LogLevel         string       `json:"log_level"`
	LogFile          string       `json:"log_file"`
	// Transport selects the delivery mechanism: "http" (default) or "sqs".
	// Use "sqs" when the agent runs on-premise and needs reliable async delivery.
	Transport        string       `json:"transport"`
	SQS              SQSConfig    `json:"sqs"`
	Connections      []Connection `json:"connections"`

	mu       sync.RWMutex `json:"-"`
	filePath string       `json:"-"`
}

// Connection represents a single Firebird-to-Saicloud sync connection.
type Connection struct {
	ID       string         `json:"id"`
	Name     string         `json:"name"`
	Enabled  bool           `json:"enabled"`
	Firebird FirebirdConfig `json:"firebird"`
	Saicloud SaicloudConfig `json:"saicloud"`
	Sync     SyncConfig     `json:"sync"`
}

// FirebirdConfig holds the Firebird database connection parameters.
type FirebirdConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Database string `json:"database"`
	User     string `json:"user"`
	Password string `json:"password"`
}

// DSN returns the Firebird connection string in the format expected by firebirdsql.
// Format: user:password@host:port/path/to/database.fdb
func (fc *FirebirdConfig) DSN() string {
	return fmt.Sprintf("%s:%s@%s:%d/%s",
		fc.User, fc.Password, fc.Host, fc.Port, fc.Database)
}

// SaicloudConfig holds the Saicloud API connection parameters.
type SaicloudConfig struct {
	APIURL     string `json:"api_url"`
	CompanyID  string `json:"company_id"`
	AgentToken string `json:"agent_token"`
}

// SyncConfig holds the sync scheduling and watermark state for a connection.
type SyncConfig struct {
	GLIntervalMinutes      int        `json:"gl_interval_minutes"`
	ReferenceIntervalHours int        `json:"reference_interval_hours"`
	BatchSize              int        `json:"batch_size"`
	LastConteoGL           int64      `json:"last_conteo_gl"`
	LastVersionCust        int64      `json:"last_version_cust"`
	LastSyncAcct           *time.Time `json:"last_sync_acct"`
	LastSyncCust           *time.Time `json:"last_sync_cust"`
	LastSyncLista          *time.Time `json:"last_sync_lista"`
	LastSyncProyectos      *time.Time `json:"last_sync_proyectos"`
	LastSyncActividades    *time.Time `json:"last_sync_actividades"`
	LastSyncTipdoc         *time.Time `json:"last_sync_tipdoc"`
}

// configFileName is the name of the configuration file placed next to the binary.
const configFileName = "saicloud-agent.json"

// configFilePath returns the absolute path to the config file,
// located in the same directory as the running executable.
func configFilePath() (string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("cannot determine executable path: %w", err)
	}
	dir := filepath.Dir(exe)
	return filepath.Join(dir, configFileName), nil
}

// Default returns a default AgentConfig with one sample connection.
func Default() *AgentConfig {
	return &AgentConfig{
		AgentVersion:     "1.0.0",
		ConfiguratorPort: 8765,
		LogLevel:         "info",
		LogFile:          "C:/SaicloudAgent/logs/agent.log",
		Transport:        "http",
		SQS: SQSConfig{
			Region:   "us-east-1",
			QueueURL: "https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod",
		},
		Connections: []Connection{
			{
				ID:      "conn_001",
				Name:    "Empresa Principal S.A.S",
				Enabled: false,
				Firebird: FirebirdConfig{
					Host:     "localhost",
					Port:     3050,
					Database: "C:/SAIOPEN/DATOS/EMPRESA1.FDB",
					User:     "SYSDBA",
					Password: "masterkey",
				},
				Saicloud: SaicloudConfig{
					APIURL:     "https://api.saicloud.co",
					CompanyID:  "uuid-empresa-1",
					AgentToken: "jwt-token-agente",
				},
				Sync: SyncConfig{
					GLIntervalMinutes:      15,
					ReferenceIntervalHours: 24,
					BatchSize:              500,
					LastConteoGL:           0,
				},
			},
		},
	}
}

// Load reads the configuration file from disk.
// It looks for saicloud-agent.json next to the executable.
func Load() (*AgentConfig, error) {
	fp, err := configFilePath()
	if err != nil {
		return nil, err
	}
	return LoadFromPath(fp)
}

// LoadFromPath reads a configuration file from the given path.
func LoadFromPath(path string) (*AgentConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("cannot read config file %s: %w", path, err)
	}

	var cfg AgentConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("cannot parse config file %s: %w", path, err)
	}

	cfg.filePath = path

	// Apply defaults for missing values
	for i := range cfg.Connections {
		if cfg.Connections[i].Sync.BatchSize == 0 {
			cfg.Connections[i].Sync.BatchSize = 500
		}
		if cfg.Connections[i].Sync.GLIntervalMinutes == 0 {
			cfg.Connections[i].Sync.GLIntervalMinutes = 15
		}
		if cfg.Connections[i].Sync.ReferenceIntervalHours == 0 {
			cfg.Connections[i].Sync.ReferenceIntervalHours = 24
		}
		if cfg.Connections[i].Firebird.Port == 0 {
			cfg.Connections[i].Firebird.Port = 3050
		}
	}

	return &cfg, nil
}

// Save writes the configuration to the file it was loaded from, or to the
// default location next to the executable.
func Save(cfg *AgentConfig) error {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()

	fp := cfg.filePath
	if fp == "" {
		var err error
		fp, err = configFilePath()
		if err != nil {
			return err
		}
		cfg.filePath = fp
	}

	return saveToPath(cfg, fp)
}

// SaveToPath writes the configuration to the specified path.
func SaveToPath(cfg *AgentConfig, path string) error {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()
	return saveToPath(cfg, path)
}

func saveToPath(cfg *AgentConfig, path string) error {
	// Ensure parent directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("cannot create config directory %s: %w", dir, err)
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return fmt.Errorf("cannot marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("cannot write config file %s: %w", path, err)
	}

	return nil
}

// FindConnection returns the connection with the given ID, or nil if not found.
func (cfg *AgentConfig) FindConnection(id string) *Connection {
	cfg.mu.RLock()
	defer cfg.mu.RUnlock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == id {
			return &cfg.Connections[i]
		}
	}
	return nil
}

// AddConnection adds a new connection to the configuration.
// Returns an error if a connection with the same ID already exists.
func (cfg *AgentConfig) AddConnection(conn Connection) error {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()
	for _, c := range cfg.Connections {
		if c.ID == conn.ID {
			return fmt.Errorf("connection with ID '%s' already exists", conn.ID)
		}
	}
	cfg.Connections = append(cfg.Connections, conn)
	return nil
}

// UpdateConnection replaces the connection with the given ID.
// Returns an error if the connection is not found.
func (cfg *AgentConfig) UpdateConnection(conn Connection) error {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == conn.ID {
			cfg.Connections[i] = conn
			return nil
		}
	}
	return fmt.Errorf("connection '%s' not found", conn.ID)
}

// RemoveConnection removes the connection with the given ID.
// Returns an error if the connection is not found.
func (cfg *AgentConfig) RemoveConnection(id string) error {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == id {
			cfg.Connections = append(cfg.Connections[:i], cfg.Connections[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("connection '%s' not found", id)
}

// UpdateCustVersion updates the last_version_cust watermark for a connection and persists the config.
func (cfg *AgentConfig) UpdateCustVersion(connID string, lastVersion int64) error {
	cfg.mu.Lock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == connID {
			cfg.Connections[i].Sync.LastVersionCust = lastVersion
			cfg.mu.Unlock()
			return Save(cfg)
		}
	}
	cfg.mu.Unlock()
	return fmt.Errorf("connection '%s' not found", connID)
}

// UpdateWatermark updates the last_conteo_gl watermark for a connection and persists the config.
func (cfg *AgentConfig) UpdateWatermark(connID string, lastConteo int64) error {
	cfg.mu.Lock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == connID {
			cfg.Connections[i].Sync.LastConteoGL = lastConteo
			cfg.mu.Unlock()
			return Save(cfg)
		}
	}
	cfg.mu.Unlock()
	return fmt.Errorf("connection '%s' not found", connID)
}

// UpdateReferenceSyncTime updates the last sync timestamp for a reference table
// and persists the config.
func (cfg *AgentConfig) UpdateReferenceSyncTime(connID string, table string) error {
	now := time.Now().UTC()
	cfg.mu.Lock()
	for i := range cfg.Connections {
		if cfg.Connections[i].ID == connID {
			switch table {
			case "acct":
				cfg.Connections[i].Sync.LastSyncAcct = &now
			case "cust":
				cfg.Connections[i].Sync.LastSyncCust = &now
			case "lista":
				cfg.Connections[i].Sync.LastSyncLista = &now
			case "proyectos":
				cfg.Connections[i].Sync.LastSyncProyectos = &now
			case "actividades":
				cfg.Connections[i].Sync.LastSyncActividades = &now
			case "tipdoc":
				cfg.Connections[i].Sync.LastSyncTipdoc = &now
			default:
				cfg.mu.Unlock()
				return fmt.Errorf("unknown reference table: %s", table)
			}
			cfg.mu.Unlock()
			return Save(cfg)
		}
	}
	cfg.mu.Unlock()
	return fmt.Errorf("connection '%s' not found", connID)
}

// EnabledConnections returns only the connections that are enabled.
func (cfg *AgentConfig) EnabledConnections() []Connection {
	cfg.mu.RLock()
	defer cfg.mu.RUnlock()
	var enabled []Connection
	for _, c := range cfg.Connections {
		if c.Enabled {
			enabled = append(enabled, c)
		}
	}
	return enabled
}
