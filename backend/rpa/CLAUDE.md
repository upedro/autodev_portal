# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RPA FluxLaw is a Robotic Process Automation system for downloading legal documents from Brazilian legal systems (eLaw COGNA, BCLegal Loft, Lexxy SuperSim) and uploading them to ADVWin GED. It uses FastAPI + Celery + MongoDB architecture with async task processing.

## Common Commands

### Running the Application

```bash
# Terminal 1: Start API
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery Worker (Windows requires --pool=solo)
celery -A worker worker --loglevel=info --pool=solo

# Terminal 3: Start Celery Beat (or combine with worker)
celery -A worker beat --loglevel=info
# Combined: celery -A worker worker --beat --loglevel=info --pool=solo
```

### Testing

```bash
# Standalone RPA tests (no infrastructure required)
python test_rpa_standalone_cogna.py
python test_rpa_standalone_loft.py
python test_rpa_standalone_lexxy.py

# Full integration tests (requires Celery/MongoDB/Redis)
python test_cogna_to_ged.py
python test_loft_to_ged.py
python test_supersim_to_ged.py

# API/flow tests
python test_flow.py
python test_advwin_api.py
```

### Installation

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Architecture

### Core Components

- **main.py** - FastAPI application with REST endpoints for task management
- **worker.py** - Celery tasks with retry logic (max 3 retries, 30min timeout)
- **models.py** - Pydantic models for Task, DocumentInfo, TaskStatus enum
- **database.py** - MongoDB repository pattern (TaskRepository class)
- **cloud_storage.py** - Storage abstraction (Azure Blob or Local filesystem)
- **rpa_logic.py** - RPA orchestration entry point, Selenium driver management

### RPA Systems (sistemas/)

Each system is a standalone Selenium automation module:

- **sistemas/elaw/cogna.py** - ElawCOGNA class for eLaw COGNA system
- **sistemas/bclegal/loft.py** - BCLegal class with SSO authentication
- **sistemas/lexxy/supersim.py** - LexxySuperSim class for Lexxy system
- **sistemas/advwin/** - ADVWin integration (advwin_api.py, document_classifier.py, ged_helper.py)

### Processing Flow

1. User uploads Excel/CSV via `POST /tasks/upload/{client_name}`
2. FastAPI creates pending tasks in MongoDB
3. Celery Beat (every 10 min) triggers `check_pending_tasks()`
4. Worker executes RPA: login → search → download all documents → rename files
5. Documents uploaded to Azure/Local storage
6. Task status updated to completed/failed in MongoDB

### Key API Endpoints

- `POST /tasks/upload/{client_name}` - Upload spreadsheet with process numbers
- `GET /tasks/{task_id}` - Get task details
- `GET /tasks/status/{process_number}` - Get task by process number
- `GET /tasks/` - List tasks (optional: status_filter, limit)
- `GET /health` - Health check

## Key Patterns

### Repository Pattern
All database operations go through `TaskRepository` in database.py:
```python
TaskRepository.create_task(process_number, client_name)
TaskRepository.update_task_status(task_id, TaskStatus.COMPLETED)
```

### Document Metadata Structure
Downloaded documents tracked with standardized metadata:
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
Uses Pydantic BaseSettings in settings.py, loads from .env file.

## Technology Stack

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Task Queue**: Celery, Redis
- **Database**: MongoDB (Atlas)
- **Storage**: Azure Blob Storage or Local filesystem
- **RPA**: Selenium, webdriver-manager
- **Data Processing**: Pandas, openpyxl
