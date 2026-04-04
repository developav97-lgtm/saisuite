// Package sqs provides an AWS SQS publisher for future use.
// The current MVP uses direct HTTP POST to the Django API, but this package
// is included as a structure for when the system scales to use SQS as the
// message transport layer between the Go agent and Django.
package sqs

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	sqsTypes "github.com/aws/aws-sdk-go-v2/service/sqs/types"
)

// Publisher sends messages to an AWS SQS queue.
type Publisher struct {
	client   *sqs.Client
	queueURL string
	logger   *slog.Logger
}

// Message represents a message to be published to SQS.
type Message struct {
	Type      string      `json:"type"`
	CompanyID string      `json:"company_id"`
	ConnID    string      `json:"conn_id"`
	Timestamp string      `json:"timestamp"`
	Data      interface{} `json:"data"`
}

// NewPublisher creates a new SQS publisher.
// This is a placeholder for future SQS integration.
func NewPublisher(client *sqs.Client, queueURL string, logger *slog.Logger) *Publisher {
	return &Publisher{
		client:   client,
		queueURL: queueURL,
		logger:   logger,
	}
}

// Publish sends a message to the SQS queue.
// The message is serialized to JSON before sending.
func (p *Publisher) Publish(ctx context.Context, msg Message) error {
	data, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("failed to marshal SQS message: %w", err)
	}

	body := string(data)

	input := &sqs.SendMessageInput{
		QueueUrl:    aws.String(p.queueURL),
		MessageBody: aws.String(body),
		MessageAttributes: map[string]sqsTypes.MessageAttributeValue{
			"MessageType": {
				DataType:    aws.String("String"),
				StringValue: aws.String(msg.Type),
			},
			"CompanyID": {
				DataType:    aws.String("String"),
				StringValue: aws.String(msg.CompanyID),
			},
		},
	}

	result, err := p.client.SendMessage(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to send SQS message: %w", err)
	}

	p.logger.Info("SQS message sent",
		"message_id", *result.MessageId,
		"type", msg.Type,
		"company_id", msg.CompanyID,
	)

	return nil
}
