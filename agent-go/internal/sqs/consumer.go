// Package sqs — Consumer (poller) para la cola de entrada Cloud→Sai.
// El agente lee mensajes que Django publica (item_upsert, etc.) y los procesa.
package sqs

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

// InboundMessage es el envelope de cada mensaje Cloud→Sai.
// Comparte la misma estructura que el Message outbound para consistencia.
type InboundMessage struct {
	Type      string          `json:"type"`
	CompanyID string          `json:"company_id"`
	ConnID    string          `json:"conn_id"`
	Timestamp string          `json:"timestamp"`
	Data      json.RawMessage `json:"data"`
}

// MessageHandler procesa un mensaje entrante y retorna error si debe reintentarse.
type MessageHandler func(msg InboundMessage) error

// Consumer hace long-polling de una cola SQS y despacha mensajes al handler.
type Consumer struct {
	client   *sqs.Client
	queueURL string
	logger   *slog.Logger
}

// NewConsumer crea un Consumer con las mismas credenciales que el Publisher.
func NewConsumer(accessKeyID, secretAccessKey, region, queueURL string, logger *slog.Logger) *Consumer {
	staticProvider := aws.CredentialsProviderFunc(func(_ context.Context) (aws.Credentials, error) {
		return aws.Credentials{
			AccessKeyID:     accessKeyID,
			SecretAccessKey: secretAccessKey,
			Source:          "SaicloudAgentConfig",
		}, nil
	})

	cfg := aws.Config{
		Region:      region,
		Credentials: staticProvider,
	}

	client := sqs.NewFromConfig(cfg)
	return &Consumer{
		client:   client,
		queueURL: queueURL,
		logger:   logger,
	}
}

// Run inicia el bucle de polling. Bloquea hasta que ctx es cancelado.
func (c *Consumer) Run(ctx context.Context, handler MessageHandler) {
	c.logger.Info("inbound SQS consumer started", "queue", c.queueURL)
	for {
		select {
		case <-ctx.Done():
			c.logger.Info("inbound SQS consumer stopped")
			return
		default:
		}

		if err := c.pollOnce(ctx, handler); err != nil {
			c.logger.Error("inbound SQS poll error", "error", err)
		}
	}
}

// pollOnce lee un batch de mensajes, los procesa y elimina los exitosos.
func (c *Consumer) pollOnce(ctx context.Context, handler MessageHandler) error {
	resp, err := c.client.ReceiveMessage(ctx, &sqs.ReceiveMessageInput{
		QueueUrl:            aws.String(c.queueURL),
		MaxNumberOfMessages: 10,
		WaitTimeSeconds:     20, // long-polling
		VisibilityTimeout:   120,
	})
	if err != nil {
		return fmt.Errorf("ReceiveMessage failed: %w", err)
	}

	for _, msg := range resp.Messages {
		body := aws.ToString(msg.Body)

		var inbound InboundMessage
		if err := json.Unmarshal([]byte(body), &inbound); err != nil {
			c.logger.Error("inbound msg invalid JSON — discarding", "error", err)
			c.deleteMessage(ctx, msg.ReceiptHandle)
			continue
		}

		procErr := handler(inbound)
		switch {
		case procErr == nil:
			// Éxito: borrar de la cola
			c.deleteMessage(ctx, msg.ReceiptHandle)
			c.logger.Info("inbound msg processed",
				"type", inbound.Type, "company_id", inbound.CompanyID)

		case procErr == ErrNotOwner:
			// El mensaje es para otra empresa: devolver a la cola inmediatamente
			// para que el agente correcto lo consuma sin esperar el visibility timeout.
			c.releaseMessage(ctx, msg.ReceiptHandle)
			c.logger.Debug("inbound msg not ours — released",
				"company_id", inbound.CompanyID)

		default:
			// Error real: dejar en cola, SQS lo reencola al vencer el timeout
			c.logger.Error("inbound msg processing failed — leaving for retry",
				"type", inbound.Type, "company_id", inbound.CompanyID, "error", procErr)
		}
	}
	return nil
}

// ErrNotOwner indica que el mensaje es para otro agente (distinta empresa).
// El consumer devuelve el mensaje a la cola inmediatamente (VisibilityTimeout=0).
var ErrNotOwner = fmt.Errorf("message not owned by this agent")

func (c *Consumer) deleteMessage(ctx context.Context, receiptHandle *string) {
	_, err := c.client.DeleteMessage(ctx, &sqs.DeleteMessageInput{
		QueueUrl:      aws.String(c.queueURL),
		ReceiptHandle: receiptHandle,
	})
	if err != nil {
		c.logger.Warn("failed to delete inbound SQS message", "error", err)
	}
}

// releaseMessage devuelve el mensaje a la cola con VisibilityTimeout=0
// para que otro agente pueda consumirlo de inmediato.
func (c *Consumer) releaseMessage(ctx context.Context, receiptHandle *string) {
	_, err := c.client.ChangeMessageVisibility(ctx, &sqs.ChangeMessageVisibilityInput{
		QueueUrl:          aws.String(c.queueURL),
		ReceiptHandle:     receiptHandle,
		VisibilityTimeout: 0,
	})
	if err != nil {
		c.logger.Warn("failed to release inbound SQS message", "error", err)
	}
}
