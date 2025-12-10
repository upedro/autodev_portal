# =============================================================================
# RPA FluxLaw - Makefile
# Comandos simplificados para desenvolvimento e deploy
# =============================================================================

.PHONY: help build up down logs restart clean test dev prod

# Default target
help:
	@echo "============================================="
	@echo "  RPA FluxLaw - Comandos Disponíveis"
	@echo "============================================="
	@echo ""
	@echo "  DESENVOLVIMENTO:"
	@echo "    make dev          - Inicia ambiente de desenvolvimento"
	@echo "    make dev-mongo    - Inicia com MongoDB local"
	@echo "    make dev-monitor  - Inicia com Flower (monitoramento)"
	@echo ""
	@echo "  PRODUÇÃO:"
	@echo "    make prod         - Inicia ambiente de produção"
	@echo "    make prod-full    - Produção + MongoDB + Flower"
	@echo ""
	@echo "  GERENCIAMENTO:"
	@echo "    make build        - Constrói as imagens Docker"
	@echo "    make up           - Inicia os containers"
	@echo "    make down         - Para os containers"
	@echo "    make restart      - Reinicia os containers"
	@echo "    make logs         - Mostra logs de todos os serviços"
	@echo "    make logs-api     - Mostra logs da API"
	@echo "    make logs-worker  - Mostra logs do Worker"
	@echo ""
	@echo "  MANUTENÇÃO:"
	@echo "    make clean        - Remove containers e volumes"
	@echo "    make prune        - Limpa imagens não utilizadas"
	@echo "    make shell-api    - Acessa shell da API"
	@echo "    make shell-worker - Acessa shell do Worker"
	@echo ""
	@echo "  TESTES:"
	@echo "    make test         - Executa testes"
	@echo "    make health       - Verifica saúde dos serviços"
	@echo ""

# -----------------------------------------------------------------------------
# Build
# -----------------------------------------------------------------------------
build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
dev:
	docker compose up -d api worker beat redis
	@echo ""
	@echo "✅ Ambiente de desenvolvimento iniciado!"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo ""

dev-mongo:
	docker compose --profile with-mongodb up -d
	@echo ""
	@echo "✅ Ambiente com MongoDB local iniciado!"
	@echo "   API: http://localhost:8000"
	@echo "   MongoDB: localhost:27017"
	@echo ""

dev-monitor:
	docker compose --profile monitoring up -d
	@echo ""
	@echo "✅ Ambiente com monitoramento iniciado!"
	@echo "   API: http://localhost:8000"
	@echo "   Flower: http://localhost:5555"
	@echo ""

dev-full:
	docker compose --profile with-mongodb --profile monitoring up -d
	@echo ""
	@echo "✅ Ambiente completo iniciado!"
	@echo "   API: http://localhost:8000"
	@echo "   MongoDB: localhost:27017"
	@echo "   Flower: http://localhost:5555"
	@echo ""

# -----------------------------------------------------------------------------
# Production
# -----------------------------------------------------------------------------
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d api worker beat redis
	@echo ""
	@echo "✅ Ambiente de produção iniciado!"
	@echo ""

prod-full:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile with-mongodb --profile monitoring up -d
	@echo ""
	@echo "✅ Ambiente de produção completo iniciado!"
	@echo ""

# -----------------------------------------------------------------------------
# Container Management
# -----------------------------------------------------------------------------
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

stop:
	docker compose stop

# -----------------------------------------------------------------------------
# Logs
# -----------------------------------------------------------------------------
logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

logs-beat:
	docker compose logs -f beat

# -----------------------------------------------------------------------------
# Shell Access
# -----------------------------------------------------------------------------
shell-api:
	docker compose exec api /bin/bash

shell-worker:
	docker compose exec worker /bin/bash

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean:
	docker compose down -v --remove-orphans
	@echo "✅ Containers e volumes removidos"

prune:
	docker system prune -f
	docker image prune -f
	@echo "✅ Imagens não utilizadas removidas"

clean-all: clean prune
	@echo "✅ Limpeza completa realizada"

# -----------------------------------------------------------------------------
# Testing & Health
# -----------------------------------------------------------------------------
test:
	docker compose exec api python -m pytest -v

health:
	@echo "Verificando saúde dos serviços..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API não respondeu"
	@docker compose exec redis redis-cli ping || echo "❌ Redis não respondeu"
	@echo "✅ Verificação concluída"

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
mongo-shell:
	docker compose exec mongodb mongosh -u admin -p admin123

# -----------------------------------------------------------------------------
# Scaling
# -----------------------------------------------------------------------------
scale-workers:
	docker compose up -d --scale worker=$(n)
	@echo "✅ Workers escalados para $(n) instâncias"
