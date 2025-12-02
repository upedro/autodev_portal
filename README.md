# Portal Web CNJ - Sistema de Solicitação de Serviços RPA

Sistema web para solicitação e acompanhamento de serviços automatizados de busca de documentos jurídicos via processos CNJ.

Baseado no design: https://www.figma.com/design/bbHLv6BSRzq6yWgO96urMl/Solicita%C3%A7%C3%A3o-de-Servi%C3%A7os-CNJ

## 📋 Visão Geral

O Portal Web CNJ permite que advogados e departamentos jurídicos solicitem serviços automatizados (RPA) para buscar documentos em portais de clientes, gerenciar solicitações e fazer download dos documentos processados.

### Características Principais

- ✅ Autenticação JWT com hash bcrypt
- ✅ CRUD completo de solicitações
- ✅ Upload de planilhas Excel com CNJs
- ✅ Sistema de eventos event-driven com MongoDB
- ✅ Armazenamento de documentos no Azure Blob Storage
- ✅ URLs temporárias (SAS) para download seguro
- ✅ API REST documentada com Swagger
- ✅ Suporte a múltiplos clientes
- ✅ Validação de números CNJ

## 🏗️ Arquitetura

```
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│       FastAPI Backend           │
├─────────────────────────────────┤
│  • Auth (JWT)                   │
│  • Clientes API                 │
│  • Solicitações CRUD            │
│  • Documentos (SAS URLs)        │
│  • Event Publisher              │
└──────┬──────────────────┬───────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│   MongoDB   │    │Azure Storage│
│  (Events)   │    │ (Documents) │
└─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ RPA Workers │
│  (Selenium) │
└─────────────┘
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Redis 7+
- Azure Storage Account (ou emulador Azurite para dev)

### 1. Backend Setup

```bash
cd backend

# Instalar dependências
pip install -r requirements.txt

# Copiar e configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Popular banco de dados com dados iniciais
python -m scripts.seed_database

# Iniciar servidor de desenvolvimento
uvicorn main:app --reload --port 8000
```

API estará disponível em: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs

### 2. Frontend Setup

```bash
# Na raiz do portal-web
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

Frontend estará disponível em: http://localhost:5173

### 3. Docker Compose (Recomendado)

```bash
# Subir todos os serviços
docker-compose up -d

# Popular banco de dados
docker-compose exec backend python -m scripts.seed_database

# Ver logs
docker-compose logs -f
```

## 📁 Estrutura do Projeto

```
portal-web/
├── backend/
│   ├── config/
│   │   └── settings.py          # Configurações (Pydantic Settings)
│   ├── models/
│   │   ├── status.py            # Enums de status
│   │   ├── usuario.py           # Model de usuário
│   │   ├── cliente.py           # Model de cliente
│   │   └── solicitacao.py       # Model de solicitação
│   ├── routers/
│   │   ├── auth.py              # Login/Register
│   │   ├── clientes.py          # CRUD de clientes
│   │   ├── solicitacoes.py      # CRUD de solicitações + upload Excel
│   │   └── documentos.py        # Geração de SAS URLs
│   ├── utils/
│   │   ├── auth.py              # JWT + bcrypt
│   │   └── excel_parser.py      # Parser de planilhas
│   ├── workers/
│   │   ├── azure_storage.py     # Handler Azure Blob Storage
│   │   └── event_system.py      # Sistema de eventos
│   ├── scripts/
│   │   └── seed_database.py     # Script de população inicial
│   ├── database.py              # Conexão MongoDB (Motor)
│   ├── main.py                  # Entry point FastAPI
│   ├── requirements.txt
│   └── Dockerfile
├── src/                         # Frontend React
├── docker-compose.yml
└── README.md
```

## 📡 API Endpoints

### Autenticação

- `POST /api/auth/login` - Login com email/senha
- `POST /api/auth/register` - Registro de novo usuário

### Clientes

- `GET /api/clientes` - Listar clientes ativos
- `GET /api/clientes/{id}` - Detalhes de um cliente

### Solicitações

- `GET /api/solicitacoes` - Listar solicitações do usuário
- `GET /api/solicitacoes/{id}` - Detalhes de uma solicitação
- `POST /api/solicitacoes` - Criar nova solicitação (JSON com CNJs)
- `POST /api/solicitacoes/upload` - Criar solicitação via upload Excel

### Documentos

- `GET /api/documentos/{solicitacao_id}` - URLs de download (SAS tokens)
- `GET /api/documentos/{solicitacao_id}/{cnj}` - URLs para CNJ específico

## 🎯 Dados de Teste

Após executar o seed, você terá:

### Usuários

- **Email:** admin@portal-rpa.com | **Senha:** admin123
- **Email:** test@portal-rpa.com | **Senha:** test123

### Clientes

- Agibank
- Creditas
- Cogna Educação
- Cliente Demo

## 🛣️ Roadmap

### Fase 1 - MVP Backend (✅ Concluída)

- ✅ Backend API completo
- ✅ Autenticação JWT
- ✅ CRUD de solicitações
- ✅ Upload de Excel
- ✅ Integração Azure Storage
- ✅ Sistema de eventos

### Fase 2 - Frontend (⏳ Em Andamento)

- ⏳ Telas React (Login, Dashboard, Solicitar, Acompanhamento)
- ⏳ State management com Zustand
- ⏳ Componentes de UI

### Fase 3 - Worker RPA (⏳ Próximo)

- ⏳ Worker genérico multi-cliente
- ⏳ Integração com sistema de eventos
- ⏳ Processamento de CNJs

## 📄 Licença

Proprietary - Todos os direitos reservados

## 👥 Time

- **Backend Lead:** Pedro Marques
- **RPA Lead:** Luana
