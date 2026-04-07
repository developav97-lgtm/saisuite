// Package sqs provides an AWS SQS publisher for the Saicloud Agent.
// When the agent is configured with transport="sqs", all GL and reference
// payloads are sent to SQS instead of being POSTed directly to the Django API.
// The Django backend consumes from the queue asynchronously.
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
// The structure mirrors the HTTP payload so the Django consumer
// can process both transports with the same handler.
type Message struct {
	Type      string      `json:"type"`
	CompanyID string      `json:"company_id"`
	ConnID    string      `json:"conn_id"`
	Timestamp string      `json:"timestamp"`
	Data      interface{} `json:"data"`
}

// New creates a Publisher using explicit AWS credentials.
// This is the primary constructor — it does not read environment variables
// or the shared credentials file; all values come from the agent config.
func New(accessKeyID, secretAccessKey, region, queueURL string, logger *slog.Logger) *Publisher {
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

	return &Publisher{
		client:   client,
		queueURL: queueURL,
		logger:   logger,
	}
}

// NewPublisher creates a Publisher from an already-constructed SQS client.
// Kept for backwards compatibility and testing.
func NewPublisher(client *sqs.Client, queueURL string, logger *slog.Logger) *Publisher {
	return &Publisher{
		client:   client,
		queueURL: queueURL,
		logger:   logger,
	}
}

// Ping verifies that the SQS queue is reachable and the credentials are valid
// by calling GetQueueAttributes. Returns nil on success.
func (p *Publisher) Ping(ctx context.Context) error {
	_, err := p.client.GetQueueAttributes(ctx, &sqs.GetQueueAttributesInput{
		QueueUrl:       aws.String(p.queueURL),
		AttributeNames: []sqsTypes.QueueAttributeName{sqsTypes.QueueAttributeNameApproximateNumberOfMessages},
	})
	if err != nil {
		return fmt.Errorf("SQS queue unreachable: %w", err)
	}
	return nil
}

// Publish sends a message to the SQS queue.
// The message is serialized to JSON before sending.
// MessageAttributes carry the type and company_id for server-side filtering.
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
		"conn_id", msg.ConnID,
	)

	return nil
}
