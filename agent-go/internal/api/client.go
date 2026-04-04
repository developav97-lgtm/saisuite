// Package api provides an HTTP client for communicating with the Saicloud Django API.
// It handles authentication via JWT bearer token, payload serialization, retry logic,
// and structured error reporting.
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"
)

// Client is the HTTP client for the Saicloud API.
type Client struct {
	baseURL    string
	token      string
	httpClient *http.Client
	logger     *slog.Logger
}

// GLRecord is the API contract representation of a single GL record.
// Monetary values are always strings ("1500000.00"), never floats.
type GLRecord struct {
	Conteo             int64   `json:"conteo"`
	Fecha              string  `json:"fecha"`
	DueDate            string  `json:"duedate"`
	Invc               string  `json:"invc"`
	TerceroID          string  `json:"tercero_id"`
	TerceroNombre      string  `json:"tercero_nombre"`
	Auxiliar           float64 `json:"auxiliar"`
	AuxiliarNombre     string  `json:"auxiliar_nombre"`
	TituloCodigo       int     `json:"titulo_codigo"`
	TituloNombre       string  `json:"titulo_nombre"`
	GrupoCodigo        int     `json:"grupo_codigo"`
	GrupoNombre        string  `json:"grupo_nombre"`
	CuentaCodigo       int     `json:"cuenta_codigo"`
	CuentaNombre       string  `json:"cuenta_nombre"`
	SubcuentaCodigo    int     `json:"subcuenta_codigo"`
	SubcuentaNombre    string  `json:"subcuenta_nombre"`
	Debito             string  `json:"debito"`
	Credito            string  `json:"credito"`
	Tipo               string  `json:"tipo"`
	Batch              int     `json:"batch"`
	Descripcion        string  `json:"descripcion"`
	Periodo            string  `json:"periodo"`
	DepartamentoCodigo *int    `json:"departamento_codigo"`
	DepartamentoNombre string  `json:"departamento_nombre"`
	CentroCostoCodigo  *int    `json:"centro_costo_codigo"`
	CentroCostoNombre  string  `json:"centro_costo_nombre"`
	ProyectoCodigo     *string `json:"proyecto_codigo"`
	ProyectoNombre     string  `json:"proyecto_nombre"`
	ActividadCodigo    *string `json:"actividad_codigo"`
	ActividadNombre    string  `json:"actividad_nombre"`
}

// GLBatchPayload is the top-level payload for a GL batch sync.
type GLBatchPayload struct {
	Type      string      `json:"type"`
	CompanyID string      `json:"company_id"`
	ConnID    string      `json:"conn_id"`
	Timestamp string      `json:"timestamp"`
	Data      GLBatchData `json:"data"`
}

// GLBatchData contains the GL records and metadata for a batch.
type GLBatchData struct {
	Records    []GLRecord `json:"records"`
	LastConteo int64      `json:"last_conteo"`
	BatchCount int        `json:"batch_count"`
}

// ReferencePayload is the top-level payload for reference table syncs.
type ReferencePayload struct {
	Type      string        `json:"type"`
	CompanyID string        `json:"company_id"`
	ConnID    string        `json:"conn_id"`
	Timestamp string        `json:"timestamp"`
	Data      ReferenceData `json:"data"`
}

// ReferenceData contains the reference records and count.
type ReferenceData struct {
	Records    interface{} `json:"records"`
	TotalCount int         `json:"total_count"`
}

// APIError represents an error response from the Saicloud API.
type APIError struct {
	StatusCode int
	Body       string
	URL        string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("API error %d from %s: %s", e.StatusCode, e.URL, e.Body)
}

// NewClient creates a new Saicloud API client.
func NewClient(baseURL string, token string, logger *slog.Logger) *Client {
	return &Client{
		baseURL: baseURL,
		token:   token,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		logger: logger,
	}
}

// HealthCheck verifies the API is reachable by hitting the health endpoint.
func (c *Client) HealthCheck() error {
	url := c.baseURL + "/api/v1/health/"
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	c.setHeaders(req)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("health check request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return &APIError{
			StatusCode: resp.StatusCode,
			Body:       string(body),
			URL:        url,
		}
	}

	return nil
}

// PostGLBatch sends a batch of GL records to the Saicloud API.
// Endpoint: POST /api/v1/contabilidad/sync/gl-batch/
func (c *Client) PostGLBatch(payload GLBatchPayload) error {
	url := c.baseURL + "/api/v1/contabilidad/sync/gl-batch/"
	return c.postJSON(url, payload)
}

// PostReference sends a full reference table sync to the Saicloud API.
// The table parameter determines the endpoint:
//   - acct  -> /api/v1/contabilidad/sync/acct/
//   - cust  -> /api/v1/contabilidad/sync/cust/
//   - lista -> /api/v1/contabilidad/sync/lista/
//   - proyectos -> /api/v1/contabilidad/sync/proyectos/
//   - actividades -> /api/v1/contabilidad/sync/actividades/
func (c *Client) PostReference(table string, payload ReferencePayload) error {
	url := fmt.Sprintf("%s/api/v1/contabilidad/sync/%s/", c.baseURL, table)
	return c.postJSON(url, payload)
}

// postJSON serializes the payload as JSON and POSTs it to the given URL.
// It includes retry logic with exponential backoff for transient failures.
func (c *Client) postJSON(url string, payload interface{}) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	c.logger.Debug("POST request",
		"url", url,
		"payload_size_bytes", len(data),
	)

	maxRetries := 3
	var lastErr error

	for attempt := 1; attempt <= maxRetries; attempt++ {
		req, err := http.NewRequest("POST", url, bytes.NewReader(data))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}

		c.setHeaders(req)
		req.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("request failed (attempt %d/%d): %w", attempt, maxRetries, err)
			c.logger.Warn("request failed, retrying",
				"url", url,
				"attempt", attempt,
				"error", err,
			)
			time.Sleep(time.Duration(attempt*attempt) * time.Second)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		// Success
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			c.logger.Debug("POST successful",
				"url", url,
				"status", resp.StatusCode,
				"response_size_bytes", len(body),
			)
			return nil
		}

		// Non-retryable client errors (4xx)
		if resp.StatusCode >= 400 && resp.StatusCode < 500 {
			return &APIError{
				StatusCode: resp.StatusCode,
				Body:       string(body),
				URL:        url,
			}
		}

		// Retryable server errors (5xx)
		lastErr = &APIError{
			StatusCode: resp.StatusCode,
			Body:       string(body),
			URL:        url,
		}
		c.logger.Warn("server error, retrying",
			"url", url,
			"status", resp.StatusCode,
			"attempt", attempt,
		)
		time.Sleep(time.Duration(attempt*attempt) * time.Second)
	}

	return fmt.Errorf("all %d retries exhausted: %w", maxRetries, lastErr)
}

// setHeaders adds the authorization and common headers to a request.
func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("User-Agent", "SaicloudAgent/1.0")
	req.Header.Set("Accept", "application/json")
}
