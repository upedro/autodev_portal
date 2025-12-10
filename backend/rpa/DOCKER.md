# Docker - RPA FluxLaw

Guia completo para executar o RPA FluxLaw com Docker.

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado
- Arquivo `.env` configurado (copie de `.env.docker`)

## Quick Start

```powershell
# 1. Copie o arquivo de ambiente
cp .env.docker .env

# 2. Edite o .env com suas credenciais
notepad .env

# 3. Inicie o ambiente
.\scripts\deploy.ps1 dev

# 4. Acesse a API
# http://localhost:8000/docs
```

## Arquitetura dos Containers

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Network                        │
├─────────────┬─────────────┬─────────────┬─────────────┬─────┤
│    API      │   Worker    │    Beat     │   Redis     │ ... │
│  (FastAPI)  │  (Celery)   │  (Celery)   │  (Broker)   │     │
│  :8000      │             │             │  :6379      │     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘
                                │
                    ┌───────────┴───────────┐
                    │   MongoDB Atlas       │
                    │   (Externo)           │
                    └───────────────────────┘
```

## Comandos Disponíveis

### Usando PowerShell (Windows)

```powershell
# Desenvolvimento
.\scripts\deploy.ps1 dev          # Inicia API + Worker + Beat + Redis
.\scripts\deploy.ps1 dev-mongo    # + MongoDB local
.\scripts\deploy.ps1 dev-monitor  # + Flower (monitoramento)
.\scripts\deploy.ps1 dev-full     # Tudo junto

# Produção
.\scripts\deploy.ps1 prod         # Modo produção
.\scripts\deploy.ps1 prod-full    # Produção completa

# Gerenciamento
.\scripts\deploy.ps1 build        # Constrói imagens
.\scripts\deploy.ps1 stop         # Para containers
.\scripts\deploy.ps1 restart      # Reinicia
.\scripts\deploy.ps1 logs         # Ver logs
.\scripts\deploy.ps1 clean        # Remove tudo
.\scripts\deploy.ps1 health       # Verifica saúde
```

### Usando Make (Linux/Mac)

```bash
make dev          # Desenvolvimento
make prod         # Produção
make logs         # Ver logs
make clean        # Limpar
make help         # Ver todos os comandos
```

### Usando Docker Compose Diretamente

```bash
# Desenvolvimento básico
docker compose up -d api worker beat redis

# Com MongoDB local
docker compose --profile with-mongodb up -d

# Com monitoramento (Flower)
docker compose --profile monitoring up -d

# Produção
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Parar
docker compose down

# Ver logs
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f worker
```

## Configuração

### Variáveis de Ambiente

Copie `.env.docker` para `.env` e configure:

```env
# MongoDB - Use Atlas (recomendado) ou local
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/...

# Credenciais dos sistemas
ELAW_USERNAME=seu_usuario
ELAW_PASSWORD=sua_senha
BCLEGAL_USER=seu_usuario
BCLEGAL_PASSWORD=sua_senha
LEXXY_USER=seu_usuario
LEXXY_PASSWORD=sua_senha

# Storage
USE_LOCAL_STORAGE=true  # ou false para Azure
AZURE_STORAGE_CONNECTION_STRING=...  # se usar Azure
```

### Usando MongoDB Local vs Atlas

**MongoDB Atlas (Recomendado para Produção):**
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
```

**MongoDB Local (Desenvolvimento):**
```powershell
# Inicia com MongoDB local
.\scripts\deploy.ps1 dev-mongo
```
```env
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/projeto_fluxlaw?authSource=admin
```

## Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| API | 8000 | FastAPI REST API |
| Redis | 6379 | Message broker Celery |
| MongoDB | 27017 | Banco de dados (opcional) |
| Flower | 5555 | Monitoramento Celery (opcional) |

## URLs

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower**: http://localhost:5555 (se ativado)

## Volumes

| Volume | Descrição |
|--------|-----------|
| `downloads_data` | Documentos baixados |
| `logs_data` | Logs da aplicação |
| `redis_data` | Persistência do Redis |
| `mongodb_data` | Dados do MongoDB (se local) |
| `beat_data` | Schedule do Celery Beat |

## Escalando Workers

Para processar mais tarefas simultaneamente:

```bash
# Escalar para 4 workers
docker compose up -d --scale worker=4
```

## Logs e Debugging

```bash
# Todos os logs
docker compose logs -f

# Logs específicos
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f beat

# Últimas 100 linhas
docker compose logs --tail=100 worker

# Acessar shell do container
docker compose exec api /bin/bash
docker compose exec worker /bin/bash
```

## Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker compose logs api

# Verificar status
docker compose ps

# Reconstruir imagem
docker compose build --no-cache api
```

### Worker não processa tarefas

1. Verifique se o Redis está rodando:
```bash
docker compose exec redis redis-cli ping
# Deve retornar: PONG
```

2. Verifique os logs do worker:
```bash
docker compose logs -f worker
```

3. Force o processamento:
```bash
curl -X POST http://localhost:8000/tasks/process-pending
```

### Erro de conexão com MongoDB

1. Verifique a URL no `.env`
2. Se usar Atlas, verifique se o IP está na whitelist
3. Se usar local, verifique se o container está rodando:
```bash
docker compose --profile with-mongodb ps
```

### Chrome/Selenium falha no Worker

O Dockerfile já inclui Chrome e ChromeDriver. Se houver problemas:

```bash
# Verificar se Chrome está instalado
docker compose exec worker google-chrome --version

# Ver logs detalhados
docker compose logs -f worker
```

## Deploy em Produção

### 1. Preparar o servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Clonar projeto
git clone <repo> /opt/rpa-fluxlaw
cd /opt/rpa-fluxlaw
```

### 2. Configurar ambiente

```bash
# Copiar e editar configurações
cp .env.docker .env
nano .env
```

### 3. Iniciar em produção

```bash
# Build e start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 4. Configurar como serviço (systemd)

```bash
# /etc/systemd/system/rpa-fluxlaw.service
[Unit]
Description=RPA FluxLaw
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rpa-fluxlaw
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar serviço
sudo systemctl enable rpa-fluxlaw
sudo systemctl start rpa-fluxlaw
```

## Backup

### Backup dos downloads

```bash
# Copiar volume de downloads
docker run --rm -v rpa-fluxlaw_downloads_data:/data -v $(pwd):/backup alpine tar czf /backup/downloads-backup.tar.gz /data
```

### Backup do MongoDB (se local)

```bash
# Dump do banco
docker compose exec mongodb mongodump --out /dump
docker cp rpa-mongodb:/dump ./mongodb-backup
```
