// Package sync — Servidor HTTP para recibir actualizaciones desde SaiCloud (SaiCloud → Sai).
// Expone endpoints que Django llama cuando un CrmProducto es creado/actualizado.
package sync

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strings"

	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// SyncServer escucha requests entrantes de SaiCloud y escribe a Firebird.
// Autenticación: Bearer token (mismo AgentToken que se usa para outbound).
// Soporta múltiples conexiones: rutea por company_id al Firebird correcto.
type SyncServer struct {
	cfg    *config.AgentConfig
	logger *slog.Logger
}

// NewSyncServer crea un nuevo servidor de sync entrante.
func NewSyncServer(cfg *config.AgentConfig, logger *slog.Logger) *SyncServer {
	return &SyncServer{cfg: cfg, logger: logger}
}

// ListenAndServe inicia el servidor HTTP en el puerto configurado.
// Si SyncServerPort == 0, no inicia el servidor.
func (s *SyncServer) ListenAndServe() error {
	port := s.cfg.SyncServerPort
	if port == 0 {
		s.logger.Info("sync server desactivado (SyncServerPort=0)")
		return nil
	}

	mux := http.NewServeMux()
	mux.HandleFunc("POST /api/v1/sync/item", s.authMiddleware(s.handleItemUpsert))
	mux.HandleFunc("GET /api/v1/health", s.handleHealth)

	addr := fmt.Sprintf(":%d", port)
	s.logger.Info("sync server iniciado", "addr", addr)
	return http.ListenAndServe(addr, mux)
}

// validToken returns true if the token matches any enabled connection's AgentToken.
func (s *SyncServer) validToken(token string) bool {
	for _, conn := range s.cfg.Connections {
		if conn.Enabled && conn.Saicloud.AgentToken == token {
			return true
		}
	}
	return false
}

// authMiddleware valida el Bearer token en el header Authorization.
func (s *SyncServer) authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token == authHeader || !s.validToken(token) {
			http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

// handleHealth responde 200 OK para health checks.
func (s *SyncServer) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"ok"}`))
}

// ItemUpsertRequest es el payload que Django envía para crear/actualizar productos.
type ItemUpsertRequest struct {
	CompanyID string                `json:"company_id"`
	Items     []firebird.ItemRecord `json:"items"`
}

// findEnabledConn returns the enabled connection for the given company_id, or nil.
func (s *SyncServer) findEnabledConn(companyID string) *config.Connection {
	for i := range s.cfg.Connections {
		c := &s.cfg.Connections[i]
		if c.Enabled && c.Saicloud.CompanyID == companyID {
			return c
		}
	}
	return nil
}

// handleItemUpsert recibe productos de SaiCloud, abre Firebird para la empresa
// correspondiente y ejecuta el upsert.
func (s *SyncServer) handleItemUpsert(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20)) // max 1MB
	if err != nil {
		http.Error(w, `{"error":"cannot read body"}`, http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	var req ItemUpsertRequest
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, `{"error":"invalid JSON"}`, http.StatusBadRequest)
		return
	}

	if req.CompanyID == "" {
		http.Error(w, `{"error":"company_id required"}`, http.StatusBadRequest)
		return
	}
	if len(req.Items) == 0 {
		http.Error(w, `{"error":"items is empty"}`, http.StatusBadRequest)
		return
	}

	conn := s.findEnabledConn(req.CompanyID)
	if conn == nil {
		s.logger.Warn("sync item: company not configured", "company_id", req.CompanyID)
		http.Error(w, `{"error":"company not configured"}`, http.StatusNotFound)
		return
	}

	// Abre una conexión Firebird por petición (escrituras son poco frecuentes).
	fbClient := firebird.New(conn.Firebird.DSN(), s.logger)
	if err := fbClient.Connect(); err != nil {
		s.logger.Error("firebird connect failed", "error", err, "company_id", req.CompanyID)
		http.Error(w, `{"error":"firebird unavailable"}`, http.StatusServiceUnavailable)
		return
	}
	defer fbClient.Close()

	result, err := fbClient.UpsertItems(req.Items)
	if err != nil {
		s.logger.Error("item upsert failed", "error", err, "company_id", req.CompanyID)
		http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
		return
	}

	s.logger.Info("item upsert complete", "company_id", req.CompanyID, "upserted", result)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = fmt.Fprintf(w, `{"upserted":%d}`, result)
}
