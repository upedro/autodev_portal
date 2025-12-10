# Portal AutoDev

Sistema completo de automacao para download de documentos juridicos de sistemas brasileiros (eLaw COGNA, BCLegal Loft, Lexxy SuperSim) com portal web para solicitacoes e acompanhamento.

## Arquitetura

```
portal-autodev-app/
├── frontend/              # React + Vite + TypeScript
│   ├── src/
│   │   ├── api/          # Cliente Axios
│   │   ├── pages/        # Paginas (Login, Dashboard, etc)
│   │   ├── components/   # Componentes React
│   │   └── store/        # Zustand state
│   └── Dockerfile
│
├── backend/
│   ├── api/              # FastAPI - Portal API
│   │   ├── routers/      # Endpoints (auth, clientes, solicitacoes, rpa)
│   │   ├── models/       # Pydantic models
│   │   ├── workers/      # Event system
│   │   └── Dockerfile
│   │
│   └── rpa/              # Celery Workers - Automacao
│       ├── sistemas/     # RPAs (elaw, bclegal, lexxy, advwin)
│       ├── portal_worker.py
│       └── Dockerfile
│
├── docker/               # Configs Docker
├── scripts/              # Scripts de deploy
└── docker-compose.yml    # Orquestracao
```

## Quick Start

```powershell
# 1. Clone o repositorio
git clone <repo-url>
cd portal-autodev-app

# 2. Configure o ambiente
cp .env.example .env
notepad .env  # Edite com suas credenciais

# 3. Inicie
.\scripts\deploy.ps1 dev

# 4. Acesse
# Frontend: http://localhost:5173
# API:      http://localhost:8001
# API Docs: http://localhost:8001/docs
```

## Comandos

```powershell
# Desenvolvimento
.\scripts\deploy.ps1 dev          # Frontend + API + RPA + Redis
.\scripts\deploy.ps1 dev-mongo    # + MongoDB local
.\scripts\deploy.ps1 dev-full     # + Flower (monitoramento)

# Gerenciamento
.\scripts\deploy.ps1 stop         # Para tudo
.\scripts\deploy.ps1 restart      # Reinicia
.\scripts\deploy.ps1 clean        # Remove containers e volumes
.\scripts\deploy.ps1 build        # Reconstroi imagens

# Logs
.\scripts\deploy.ps1 logs         # Todos
.\scripts\deploy.ps1 logs-api     # Apenas API
.\scripts\deploy.ps1 logs-rpa     # Apenas RPA workers
.\scripts\deploy.ps1 logs-frontend # Apenas Frontend

# Saude
.\scripts\deploy.ps1 health       # Verifica servicos
```

## Servicos

| Servico | Porta | Descricao |
|---------|-------|-----------|
| Frontend | 5173 | React/Vite |
| API | 8001 | FastAPI Portal |
| RPA Worker | - | Celery + Selenium |
| RPA Beat | - | Agendador (5 min) |
| Redis | 6379 | Message broker |
| MongoDB | 27017 | Banco (opcional) |
| Flower | 5555 | Monitoramento (opcional) |

## Fluxo de Funcionamento

```
Usuario (Frontend)
    │
    ├─► Login/Cadastro
    │
    ├─► Criar Solicitacao
    │   (Upload Excel com CNJs)
    │
    ▼
API (FastAPI)
    │
    ├─► Cria Solicitacao no MongoDB
    ├─► Cria Evento NOVA_SOLICITACAO
    │
    ▼
Event Worker
    │
    ├─► Detecta evento
    ├─► Cria Tasks para cada CNJ
    │
    ▼
RPA Worker (Celery)
    │
    ├─► Busca tasks pendentes
    ├─► Executa Selenium (COGNA/Loft/SuperSim)
    ├─► Baixa documentos
    ├─► Upload Azure/Local
    ├─► Atualiza status
    │
    ▼
Usuario (Frontend)
    │
    └─► Acompanha progresso
        └─► Download dos documentos
```

## Clientes Suportados

| Cliente | Sistema | RPA |
|---------|---------|-----|
| COGNA | eLaw COGNA | `sistemas/elaw/cogna.py` |
| Mercantil | eLaw Mercantil | `sistemas/elaw/cogna.py` |
| Loft | BCLegal | `sistemas/bclegal/loft.py` |
| SuperSim | Lexxy | `sistemas/lexxy/supersim.py` |

## Configuracao

### Variaveis de Ambiente

```env
# MongoDB
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=portal_autodev

# JWT
JWT_SECRET_KEY=sua-chave-secreta

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=...

# Credenciais RPA
ELAW_USERNAME=...
ELAW_PASSWORD=...
BCLEGAL_USER=...
BCLEGAL_PASSWORD=...
LEXXY_USER=...
LEXXY_PASSWORD=...
```

## Desenvolvimento

### Rodar sem Docker

```bash
# Frontend
cd frontend
npm install
npm run dev

# API
cd backend/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# RPA Worker
cd backend/rpa
pip install -r requirements.txt
celery -A portal_worker worker --loglevel=info --pool=solo

# RPA Beat
celery -A portal_worker beat --loglevel=info
```

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Radix-UI
- Zustand
- Axios

### Backend API
- FastAPI
- MongoDB (Motor async)
- JWT Authentication
- Pydantic

### RPA
- Celery
- Selenium
- Chrome Headless
- Azure Blob Storage

## Licenca

Privado e confidencial.
