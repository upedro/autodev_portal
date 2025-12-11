# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portal AutoDev is a document automation system for downloading legal documents from Brazilian legal systems (eLaw COGNA, BCLegal Loft, Lexxy SuperSim) and uploading them to ADVWin GED. It consists of a React frontend portal, a FastAPI backend API, and Celery-based RPA workers with Selenium automation.

## Common Commands

### Docker-based Development (Recommended)

```powershell
.\scripts\deploy.ps1 dev          # Start Frontend + API + RPA + Redis
.\scripts\deploy.ps1 dev-mongo    # Include local MongoDB
.\scripts\deploy.ps1 dev-full     # All services + Flower monitoring
.\scripts\deploy.ps1 stop         # Stop all containers
.\scripts\deploy.ps1 logs-api     # View API logs
.\scripts\deploy.ps1 logs-rpa     # View RPA worker logs
.\scripts\deploy.ps1 health       # Check service health
```

### Running Without Docker

```bash
# Frontend (port 5173)
cd frontend && npm install && npm run dev

# API (port 8001)
cd backend/api && pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# RPA Worker (requires Redis running)
cd backend/rpa && pip install -r requirements.txt
celery -A portal_worker worker --loglevel=info --pool=solo

# RPA Beat Scheduler
celery -A portal_worker beat --loglevel=info
```

### RPA Testing

```bash
# Standalone tests (no infrastructure required)
cd backend/rpa
python test_rpa_standalone_cogna.py
python test_rpa_standalone_loft.py
python test_rpa_standalone_lexxy.py

# Integration tests (requires Celery/MongoDB/Redis)
python test_cogna_to_ged.py
python test_loft_to_ged.py
python test_supersim_to_ged.py
```

## Architecture

```
autodev_portal/
├── frontend/                 # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── api/             # Axios client (auth, clientes, solicitacoes, documentos)
│   │   ├── pages/           # Login, Dashboard, SolicitarServico, Acompanhamento
│   │   ├── components/      # UI components + Radix-UI primitives
│   │   └── store/           # Zustand state management (useAuthStore)
│
├── backend/
│   ├── api/                 # FastAPI Portal API (port 8001)
│   │   ├── routers/         # auth, clientes, solicitacoes, documentos, rpa
│   │   ├── workers/         # Event system, Azure storage, solicitacao-to-task worker
│   │   └── main.py          # FastAPI app entry point
│   │
│   └── rpa/                 # Celery Workers - Selenium Automation
│       ├── sistemas/        # RPA modules per legal system
│       │   ├── elaw/cogna.py      # eLaw COGNA (ElawCOGNA class)
│       │   ├── bclegal/loft.py    # BCLegal Loft (BCLegal class with SSO)
│       │   ├── lexxy/supersim.py  # Lexxy SuperSim (LexxySuperSim class)
│       │   └── advwin/            # ADVWin GED integration (API, classifier, helper)
│       ├── portal_worker.py # Celery app for portal integration
│       ├── worker.py        # Core Celery tasks with retry logic
│       ├── database.py      # MongoDB TaskRepository pattern
│       ├── cloud_storage.py # Azure Blob or Local filesystem storage
│       └── rpa_logic.py     # RPA orchestration, Selenium driver management
│
└── docker-compose.yml       # Unified orchestration
```

## Processing Flow

1. User creates Solicitacao via Frontend (uploads Excel with CNJ numbers)
2. Portal API creates Solicitacao in MongoDB, emits NOVA_SOLICITACAO event
3. Event Worker detects event, creates Task records for each CNJ
4. RPA Beat scheduler triggers `check_pending_tasks()` every 5 minutes
5. RPA Worker executes Selenium automation: login -> search -> download all documents -> rename
6. Documents uploaded to Azure Blob Storage or local filesystem
7. Task status updated to completed/failed in MongoDB

## Key Patterns

### TaskRepository (database.py)
All MongoDB operations use repository pattern:
```python
TaskRepository.create_task(process_number, client_name)
TaskRepository.update_task_status(task_id, TaskStatus.COMPLETED)
```

### Document Metadata Structure
```python
{
    "numero_linha": int,           # Table line number
    "nome_arquivo_original": str,  # Original filename
    "tipo_documento": str,         # Document type (inicial, subsidio, etc)
    "nome_arquivo_final": str,     # Renamed filename
    "blob_url": str                # Storage URL
}
```

### Configuration
- Backend uses Pydantic BaseSettings loading from `.env` files
- Frontend uses Vite env vars (`VITE_API_URL`)

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React/Vite dev server |
| API | 8001 | FastAPI Portal API |
| Redis | 6379 | Celery message broker |
| MongoDB | 27017 | Database (optional local) |
| Flower | 5555 | Celery monitoring (optional) |

## Supported Clients/Systems

| Client | System | RPA Module |
|--------|--------|------------|
| COGNA | eLaw COGNA | `sistemas/elaw/cogna.py` |
| Mercantil | eLaw Mercantil | `sistemas/elaw/cogna.py` |
| Loft | BCLegal | `sistemas/bclegal/loft.py` |
| SuperSim | Lexxy | `sistemas/lexxy/supersim.py` |

## Windows-Specific Notes

- Celery requires `--pool=solo` flag on Windows
- Use PowerShell scripts in `scripts/` directory
- Redis can be run via Docker: `docker run -d -p 6379:6379 redis:latest`
