# Multi-stage build for cross-compiling the Saicloud Agent for Windows.
# Build: docker build -t saicloud-agent-builder .
# Extract: docker run --rm -v $(pwd)/dist:/dist saicloud-agent-builder

FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git

WORKDIR /app

# Copy dependency files first for layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Cross-compile for Windows AMD64
ENV CGO_ENABLED=0
ENV GOOS=windows
ENV GOARCH=amd64

RUN go build -ldflags="-s -w" -o /out/agent.exe ./cmd/agent/

# Extract stage: copies binary to a volume mount
FROM alpine:3.19

COPY --from=builder /out/agent.exe /dist/agent.exe

# When run with -v ./dist:/dist, the binary will be available on the host
CMD ["cp", "/dist/agent.exe", "/out/agent.exe"]
