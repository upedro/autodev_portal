# Portal de Automação RPA - Backend

Backend FastAPI para o Portal de Automação RPA.

## Estrutura do Projeto

```
backend/
├── main.py              # Ponto de entrada da aplicação FastAPI
├── routers/            # Rotas da API
│   ├── auth.py        # Autenticação
│   ├── clientes.py    # Clientes
│   ├── solicitacoes.py # Solicitações
│   └── documentos.py  # Documentos
├── models/             # Modelos Pydantic
├── workers/            # Workers Celery
├── config/             # Configurações
│   └── settings.py    # Settings usando Pydantic
└── requirements.txt   # Dependências Python
```

## Configuração

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do diretório `backend/` com as seguintes variáveis:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=portal_rpa

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Storage (escolha um)
# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=portal-rpa-documents

# OU Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your-azure-connection-string
AZURE_STORAGE_CONTAINER=portal-rpa-documents

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Execução

### Modo Desenvolvimento

```bash
# Usando o script
./run.sh dev

# Ou diretamente com Uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Produção

```bash
# Usando o script
./run.sh prod

# Ou diretamente com Gunicorn
gunicorn backend.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

## Endpoints

A API estará disponível em `http://localhost:8000`

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/auth/login` - Login
- `GET /api/clientes` - Listar clientes
- `GET /api/solicitacoes` - Listar solicitações
- `POST /api/solicitacoes` - Criar solicitação
- `GET /api/solicitacoes/{id}` - Obter solicitação
- `GET /api/documentos/{solicitacao_id}` - Obter documentos

## Documentação

A documentação interativa da API (Swagger) estará disponível em:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

