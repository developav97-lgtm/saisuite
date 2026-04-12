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
	PostOEBatch(payload api.OEBatchPayload) error
	PostOEDetBatch(payload api.OEBatchPayload) error
	PostCARPROBatch(payload api.OEBatchPayload) error
	PostITEMACTBatch(payload api.OEBatchPayload) error
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

func (s *httpSender) PostOEBatch(payload api.OEBatchPayload) error {
	return s.client.PostOEBatch(payload)
}

func (s *httpSender) PostOEDetBatch(payload api.OEBatchPayload) error {
	return s.client.PostOEDetBatch(payload)
}

func (s *httpSender) PostCARPROBatch(payload api.OEBatchPayload) error {
	return s.client.PostCARPROBatch(payload)
}

func (s *httpSender) PostITEMACTBatch(payload api.OEBatchPayload) error {
	return s.client.PostITEMACTBatch(payload)
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

func (s *sqsSender) postTransactional(payload api.OEBatchPayload) error {
	data, err := json.Marshal(payload.Data)
	if err != nil {
		return fmt.Errorf("sqsSender: marshal transactional data: %w", err)
	}
	var rawData interface{}
	if err := json.Unmarshal(data, &rawData); err != nil {
		return fmt.Errorf("sqsSender: unmarshal transactional data: %w", err)
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

func (s *sqsSender) PostOEBatch(payload api.OEBatchPayload) error {
	return s.postTransactional(payload)
}

func (s *sqsSender) PostOEDetBatch(payload api.OEBatchPayload) error {
	return s.postTransactional(payload)
}

func (s *sqsSender) PostCARPROBatch(payload api.OEBatchPayload) error {
	return s.postTransactional(payload)
}

func (s *sqsSender) PostITEMACTBatch(payload api.OEBatchPayload) error {
	return s.postTransactional(payload)
}
