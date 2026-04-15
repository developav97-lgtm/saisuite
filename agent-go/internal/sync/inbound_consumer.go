// Package sync — Consumidor de la cola SQS de entrada (Cloud → Sai).
// Lee mensajes que Django publica y los escribe en Firebird.
//
// Tipos de mensaje soportados:
//   - item_upsert   → escribe en ITEM (productos)
//   - cust_upsert   → escribe en CUST (terceros) [futuro]
//   - proyecto_upsert → escribe en tabla proyectos [futuro]
package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	sqspkg "github.com/valmentech/saicloud-agent/internal/sqs"

	"github.com/valmentech/saicloud-agent/internal/config"
	"github.com/valmentech/saicloud-agent/internal/firebird"
)

// InboundSyncConsumer despacha mensajes SQS entrantes a los escritores de Firebird.
type InboundSyncConsumer struct {
	cfg    *config.AgentConfig
	logger *slog.Logger
}

// NewInboundSyncConsumer crea el consumidor de la cola de entrada.
func NewInboundSyncConsumer(cfg *config.AgentConfig, logger *slog.Logger) *InboundSyncConsumer {
	return &InboundSyncConsumer{cfg: cfg, logger: logger}
}

// Run arranca el polling. Bloquea hasta que ctx es cancelado.
// Solo debe llamarse si Transport=="sqs" y InboundQueueURL != "".
func (c *InboundSyncConsumer) Run(ctx context.Context) {
	sqsCfg := c.cfg.SQS
	consumer := sqspkg.NewConsumer(
		sqsCfg.AccessKeyID,
		sqsCfg.SecretAccessKey,
		sqsCfg.Region,
		sqsCfg.InboundQueueURL,
		c.logger,
	)
	consumer.Run(ctx, c.dispatch)
}

// findEnabledConn devuelve la conexión habilitada para el company_id dado.
func (c *InboundSyncConsumer) findEnabledConn(companyID string) *config.Connection {
	for i := range c.cfg.Connections {
		conn := &c.cfg.Connections[i]
		if conn.Enabled && conn.Saicloud.CompanyID == companyID {
			return conn
		}
	}
	return nil
}

// openFirebird abre una conexión Firebird para la conexión dada.
// El caller es responsable de llamar Close().
func (c *InboundSyncConsumer) openFirebird(conn *config.Connection) (*firebird.Client, error) {
	fb := firebird.New(conn.Firebird.DSN(), c.logger)
	if err := fb.Connect(); err != nil {
		return nil, fmt.Errorf("firebird connect failed: %w", err)
	}
	return fb, nil
}

// dispatch recibe un InboundMessage y lo procesa según su tipo.
func (c *InboundSyncConsumer) dispatch(msg sqspkg.InboundMessage) error {
	conn := c.findEnabledConn(msg.CompanyID)
	if conn == nil {
		// Este mensaje es para otra empresa. ErrNotOwner hace que el consumer
		// devuelva el mensaje a la cola (ChangeMessageVisibility=0) sin borrarlo.
		return sqspkg.ErrNotOwner
	}

	switch msg.Type {
	case "item_upsert":
		return c.handleItemUpsert(conn, msg.Data)
	default:
		c.logger.Warn("inbound msg: unknown type — discarding",
			"type", msg.Type, "company_id", msg.CompanyID)
		return nil // descartar sin reintentar
	}
}

// itemUpsertData es la estructura del campo "data" en mensajes item_upsert.
type itemUpsertData struct {
	Records []firebird.ItemRecord `json:"records"`
}

// handleItemUpsert deserializa los registros y los escribe en Firebird ITEM.
func (c *InboundSyncConsumer) handleItemUpsert(conn *config.Connection, raw json.RawMessage) error {
	var data itemUpsertData
	if err := json.Unmarshal(raw, &data); err != nil {
		return fmt.Errorf("item_upsert: invalid data: %w", err)
	}
	if len(data.Records) == 0 {
		return nil
	}

	fb, err := c.openFirebird(conn)
	if err != nil {
		return err
	}
	defer fb.Close()

	n, err := fb.UpsertItems(data.Records)
	if err != nil {
		return fmt.Errorf("item_upsert: firebird write failed: %w", err)
	}

	c.logger.Info("item_upsert complete",
		"company_id", conn.Saicloud.CompanyID,
		"upserted", n,
	)
	return nil
}
