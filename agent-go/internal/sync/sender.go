package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/valmentech/saicloud-agent/internal/api"
	"github.com/valmentech/saicloud-agent/internal/sqs"
)

// Sender abstracts the delivery mechanism so that GL and reference sync
// can send data via HTTP (api.Client) or SQS (sqs.Publisher) transparently.
type Sender interface {
	PostGLBatch(payload api.GLBatchPayload) error
	PostReference(table string, payload api.ReferencePayload) error
}

// ── HTTP sender (wraps api.Client) ───────────────────────────────────────────

// httpSender delegates directly to the existing api.Client methods.
type httpSender struct {
	client *api.Client
}

func newHTTPSender(client *api.Client) Sender {
	return &httpSender{client: client}
}

func (s *httpSender) PostGLBatch(payload api.GLBatchPayload) error {
	return s.client.PostGLBatch(payload)
}

func (s *httpSender) PostReference(table string, payload api.ReferencePayload) error {
	return s.client.PostReference(table, payload)
}

// ── SQS sender (wraps sqs.Publisher) ─────────────────────────────────────────

// sqsSender wraps the SQS publisher, serializing API payloads as SQS messages.
// The Django consumer reads from the queue and processes the same JSON structure.
type sqsSender struct {
	pub    *sqs.Publisher
	logger *slog.Logger
}

func newSQSSender(pub *sqs.Publisher, logger *slog.Logger) Sender {
	return &sqsSender{pub: pub, logger: logger}
}

func (s *sqsSender) PostGLBatch(payload api.GLBatchPayload) error {
	data, err := json.Marshal(payload.Data)
	if err != nil {
		return fmt.Errorf("sqsSender: marshal GL data: %w", err)
	}

	var rawData interface{}
	if err := json.Unmarshal(data, &rawData); err != nil {
		return fmt.Errorf("sqsSender: unmarshal GL data: %w", err)
	}

	msg := sqs.Message{
		Type:      payload.Type,
		CompanyID: payload.CompanyID,
		ConnID:    payload.ConnID,
		Timestamp: payload.Timestamp,
		Data:      rawData,
	}
	return s.pub.Publish(context.Background(), msg)
}

func (s *sqsSender) PostReference(table string, payload api.ReferencePayload) error {
	msg := sqs.Message{
		Type:      payload.Type,
		CompanyID: payload.CompanyID,
		ConnID:    payload.ConnID,
		Timestamp: payload.Timestamp,
		Data:      payload.Data,
	}
	return s.pub.Publish(context.Background(), msg)
}
