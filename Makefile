# Variables
VENV_DIR := .venv
ACTIVATE := $(VENV_DIR)/bin/activate
WHATSAPP_MCP_DIR := whatsapp-mcp

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make docker-compose-up   - Run all services using Docker Compose"
	@echo "  make docker-compose-down - Stop all services"
	@echo "  make docker-compose-logs - View logs from all services"


# Docker Compose commands
.PHONY: docker-compose-up
docker-compose-up:
	docker-compose up --rebuild webhook whatsapp-auth whatsapp-mcp

.PHONY: docker-compose-down
docker-compose-down:
	docker-compose down

.PHONY: docker-compose-logs
docker-compose-logs:
	docker-compose logs -f
