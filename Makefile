DOCKER_IMAGE = latex-builder
UV = uv
CLI = $(UV) run cvrepo

REPO_ROOT = $(shell pwd)
PRINCIPAL_DIR = $(REPO_ROOT)/templates/cv/principal
BUILD_OUTPUT_DIR = $(REPO_ROOT)/runs/render
PRINCIPAL_OUTPUT = principal_main.pdf
OFFER ?= data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md
DOC_LANG ?= fr
KIND ?= both
ARCHIVE ?= 0
ARCHIVE_FLAG = $(if $(filter 1 true yes,$(ARCHIVE)),--archive,)
CONTAINER_SRC = /app/src
CONTAINER_OUT = /app/output
LATEX_CMD = latexmk -pdf
LATEX_FLAGS = -interaction=nonstopmode -synctex=1 -file-line-error
DOCKER_RUN_MAIN = docker run --rm -v "$(PRINCIPAL_DIR):$(CONTAINER_SRC)" -v "$(BUILD_OUTPUT_DIR):$(CONTAINER_OUT)" -w "$(CONTAINER_SRC)" $(DOCKER_IMAGE)

# Docker Compose
COMPOSE = docker-compose

.PHONY: help uv-sync build-image build generate build_principal archive validate index-archive clean clobber shell docker-build docker-up docker-down docker-logs docker-ps docker-test docker-shell monitor-db monitor-data db-init db-init-postgres db-mirror-postgres

uv-sync:
	$(UV) sync

build-image:
	docker build -t $(DOCKER_IMAGE) .

build: generate

generate:
	$(CLI) generate $(OFFER) --language $(DOC_LANG) --kind $(KIND) --output-dir runs/render $(ARCHIVE_FLAG)

build_principal:
	@echo "Compiling principal document from templates/cv/principal/main.tex"
	mkdir -p $(BUILD_OUTPUT_DIR)
	rm -f $(BUILD_OUTPUT_DIR)/main.aux $(BUILD_OUTPUT_DIR)/main.log $(BUILD_OUTPUT_DIR)/main.out $(BUILD_OUTPUT_DIR)/main.pdf $(BUILD_OUTPUT_DIR)/main.fdb_latexmk $(BUILD_OUTPUT_DIR)/main.fls $(BUILD_OUTPUT_DIR)/main.synctex.gz $(BUILD_OUTPUT_DIR)/main.toc $(BUILD_OUTPUT_DIR)/$(PRINCIPAL_OUTPUT)
	@docker image inspect $(DOCKER_IMAGE) >/dev/null 2>&1 || $(MAKE) build-image
	$(DOCKER_RUN_MAIN) $(LATEX_CMD) $(LATEX_FLAGS) -output-directory=$(CONTAINER_OUT) main.tex
	@if [ -f $(BUILD_OUTPUT_DIR)/main.pdf ]; then mv -f $(BUILD_OUTPUT_DIR)/main.pdf $(BUILD_OUTPUT_DIR)/$(PRINCIPAL_OUTPUT); fi
	@echo "Principal PDF written to $(BUILD_OUTPUT_DIR)/$(PRINCIPAL_OUTPUT)"

archive:
	$(CLI) archive --source-dir runs/render --archive-root runs/archive
	$(CLI) index-archive --archive-root runs/archive

validate:
	$(CLI) validate --offers-root data/offers

index-archive:
	$(CLI) index-archive --archive-root runs/archive

# ============================================================================
# DOCKER & SERVICES
# ============================================================================

help:
	@echo "Latex Tool Generator - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make uv-sync              - Sync Python dependencies"
	@echo "  make build-image          - Build legacy Docker image"
	@echo "  make build                - Generate CV/letter (legacy CLI)"
	@echo "  make generate OFFER=path  - Generate from offer"
	@echo ""
	@echo "Docker Compose (Modern):"
	@echo "  make docker-build         - Build all Docker images"
	@echo "  make docker-up            - Start all services"
	@echo "  make docker-down          - Stop all services"
	@echo "  make docker-ps            - Show running services"
	@echo "  make docker-logs          - Follow all service logs"
	@echo "  make docker-shell         - Open shell in api container"
	@echo "  make docker-test          - Run tests in Docker"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitor-db           - Monitor SQLite database"
	@echo "  make monitor-data         - Monitor data/ directory"
	@echo "  make db-init              - Initialize SQLite schema"
	@echo "  make db-init-postgres     - Initialize PostgreSQL mirror schema"
	@echo "  make db-mirror-postgres   - Mirror SQLite into PostgreSQL"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean                - Clean temporary files"
	@echo "  make clobber              - Full cleanup (including caches)"

docker-build:
	@echo "Building all Docker images..."
	$(COMPOSE) build

docker-up:
	@echo "Starting all services..."
	cp -n .env.example .env || true
	$(COMPOSE) up -d
	@echo ""
	@echo "Services started:"
	@echo "  API:      http://localhost:8000 (docs: http://localhost:8000/docs)"
	@echo "  App:      http://localhost:8501"
	@echo ""
	@$(COMPOSE) ps

docker-down:
	@echo "Stopping all services..."
	$(COMPOSE) down

docker-ps:
	$(COMPOSE) ps

docker-logs:
	$(COMPOSE) logs -f

docker-logs-api:
	$(COMPOSE) logs -f api

docker-logs-app:
	$(COMPOSE) logs -f app

docker-logs-runner:
	$(COMPOSE) logs -f runner

docker-shell:
	$(COMPOSE) exec api bash

docker-test:
	@echo "Running tests in Docker..."
	$(COMPOSE) run --rm api pytest tests/ -v

docker-clean:
	@echo "Cleaning Docker resources..."
	$(COMPOSE) down -v
	docker system prune -f

# ============================================================================
# MONITORING
# ============================================================================

monitor-db:
	@bash scripts/monitor_db.sh

monitor-data:
	@bash scripts/monitor_data.sh

monitor-all:
	@bash scripts/monitor_db.sh
	@echo ""
	@bash scripts/monitor_data.sh

db-init:
	@bash scripts/init_db.sh

db-init-postgres:
	@bash scripts/init_postgres_db.sh

db-mirror-postgres:
	@bash scripts/mirror_sqlite_to_postgres.sh

clean:
	@echo "Cleaning principal LaTeX auxiliary files"
	$(DOCKER_RUN_MAIN) latexmk -c -output-directory=$(CONTAINER_OUT)
	find runs/render -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.synctex.gz' -o -name '*.toc' \) -delete

clobber:
	@echo "Removing generated principal LaTeX files"
	$(DOCKER_RUN_MAIN) latexmk -C -output-directory=$(CONTAINER_OUT)
	find runs/render -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.synctex.gz' -o -name '*.toc' \) -delete

shell:
	docker run -it --rm -v "$(PRINCIPAL_DIR):$(CONTAINER_SRC)" -v "$(BUILD_OUTPUT_DIR):$(CONTAINER_OUT)" -w "$(CONTAINER_SRC)" $(DOCKER_IMAGE) bash
