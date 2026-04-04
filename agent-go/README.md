# Saicloud Agent

Go agent that synchronizes Saiopen (Firebird 2.5 ERP) accounting data to Saicloud (Django/PostgreSQL).

## Architecture

The agent runs on Windows PCs where Saiopen is installed. It connects to the local Firebird database, extracts GL (General Ledger) movements and reference tables (chart of accounts, third parties, departments, cost centers, projects, activities), and sends them to the Saicloud API via HTTP POST.

Key design decisions:
- **Incremental GL sync** using the `CONTEO` autoincrement PK as a watermark
- **Full reference sync** for small tables (ACCT, CUST, LISTA, PROYECTOS, ACTIVIDADES)
- **Multi-connection support** for sister companies sharing the same server
- **Independent goroutines** per connection so failures are isolated
- **Watermark persistence** after each successful batch POST

## Requirements

- Go 1.22+
- Access to a Firebird 2.5 database (Saiopen)
- Saicloud API credentials (JWT token)

## Building

### Local build (current OS)

```bash
go build -o agent ./cmd/agent/
```

### Cross-compile for Windows

```bash
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o agent.exe ./cmd/agent/
```

### Docker build (cross-compile from Linux)

```bash
docker build -t saicloud-agent-builder .
docker run --rm -v $(pwd)/dist:/out saicloud-agent-builder
```

## Configuration

The agent reads `saicloud-agent.json` from the same directory as the binary. Use the web configurator to manage connections:

```bash
agent.exe config
```

This opens a browser at `http://localhost:8765` where you can:
- Add, edit, and remove database connections
- Test Firebird and API connectivity
- View sync status and pending record counts

### Configuration file structure

```json
{
  "agent_version": "1.0.0",
  "configurator_port": 8765,
  "log_level": "info",
  "log_file": "C:/SaicloudAgent/logs/agent.log",
  "connections": [
    {
      "id": "conn_001",
      "name": "Empresa Principal S.A.S",
      "enabled": true,
      "firebird": {
        "host": "localhost",
        "port": 3050,
        "database": "C:/SAIOPEN/DATOS/EMPRESA1.FDB",
        "user": "SYSDBA",
        "password": "masterkey"
      },
      "saicloud": {
        "api_url": "https://api.saicloud.co",
        "company_id": "uuid-empresa-1",
        "agent_token": "jwt-token-agente"
      },
      "sync": {
        "gl_interval_minutes": 15,
        "reference_interval_hours": 24,
        "batch_size": 500,
        "last_conteo_gl": 0
      }
    }
  ]
}
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `agent.exe config` | Open the web configurator at http://localhost:8765 |
| `agent.exe serve` | Start the sync service (production mode) |
| `agent.exe install` | Register as a Windows Service |
| `agent.exe uninstall` | Remove the Windows Service |
| `agent.exe status` | Show status of all connections |
| `agent.exe test --id conn_001` | Test a specific connection |
| `agent.exe version` | Show agent version |

## Installation on Client PC

1. Copy `agent.exe` and `saicloud-agent.json` to `C:\SaicloudAgent\`
2. Create the logs directory: `mkdir C:\SaicloudAgent\logs`
3. Run `agent.exe config` to configure connections
4. Test each connection: `agent.exe test --id conn_001`
5. Install as Windows Service: `agent.exe install`
6. The service starts automatically on Windows boot

## Sync Process

### GL (General Ledger) - Incremental

1. Read `last_conteo_gl` from the connection config (watermark)
2. Query Firebird: `SELECT ... FROM GL WHERE CONTEO > ? ORDER BY CONTEO ASC ROWS 1 TO ?`
3. POST batch to Saicloud API: `/api/v1/contabilidad/sync/gl-batch/`
4. On success, update watermark to the last CONTEO in the batch
5. Repeat until no more records
6. Sleep for `gl_interval_minutes`, then repeat

### Reference Tables - Full Sync

Every `reference_interval_hours`, the agent performs a full sync of:
- **ACCT** (chart of accounts) -> `/api/v1/contabilidad/sync/acct/`
- **CUST** (third parties) -> `/api/v1/contabilidad/sync/cust/`
- **LISTA** (departments/cost centers) -> `/api/v1/contabilidad/sync/lista/`
- **PROYECTOS** (projects) -> `/api/v1/contabilidad/sync/proyectos/`
- **ACTIVIDADES** (activities) -> `/api/v1/contabilidad/sync/actividades/`

## Project Structure

```
agent-go/
  cmd/agent/main.go              CLI entry point
  internal/
    config/config.go              Configuration management
    firebird/client.go            Firebird database client
    sync/orchestrator.go          Multi-connection sync coordinator
    sync/gl_sync.go               Incremental GL sync
    sync/reference_sync.go        Full reference table sync
    api/client.go                 Saicloud HTTP API client
    sqs/publisher.go              AWS SQS publisher (future use)
    configurator/server.go        Web configurator server
    configurator/handlers.go      REST API for connection CRUD
    configurator/static/          Web UI (HTML/CSS/JS)
    winsvc/service.go             Windows Service management
```

## Troubleshooting

### Agent cannot connect to Firebird
- Verify the Firebird service is running: `services.msc` -> Firebird Server
- Check the database path is correct and the `.fdb` file exists
- Default credentials: SYSDBA / masterkey
- Firebird port 3050 must not be blocked by firewall

### Agent cannot reach Saicloud API
- Verify internet connectivity
- Check the API URL is correct (include https://)
- Verify the agent token is valid and not expired
- Check if a proxy is required and configure system proxy settings

### Service fails to start
- Check the log file at the configured `log_file` path
- Ensure the log directory exists
- Run `agent.exe serve` manually to see error output
- Verify the config file is valid JSON

## Dependencies

- [nakagami/firebirdsql](https://github.com/nakagami/firebirdsql) - Native Go Firebird driver
- [aws/aws-sdk-go-v2](https://github.com/aws/aws-sdk-go-v2) - AWS SDK for SQS (future)
- [golang.org/x/sys](https://pkg.go.dev/golang.org/x/sys) - Windows Service API
