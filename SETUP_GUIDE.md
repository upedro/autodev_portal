# Guia de Setup Rápido - Portal Web CNJ

## 🚀 Setup Completo em 5 Minutos

### Pré-requisitos Instalados?
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ Docker & Docker Compose

---

## Opção 1: Docker (Recomendado - Mais Rápido)

```bash
# 1. Clone e entre no diretório
cd portal-web

# 2. Crie arquivo .env para o backend
cat > backend/.env << 'EOF'
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB_NAME=portal_rpa
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=my-super-secret-key-change-in-production
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
AZURE_STORAGE_CONTAINER=portal-documentos
EOF

# 3. Subir todos os serviços
docker-compose up -d

# 4. Aguardar serviços iniciarem (30s)
sleep 30

# 5. Popular banco de dados
docker-compose exec backend python -m scripts.seed_database

# 6. Verificar que tudo está rodando
docker-compose ps

# ✅ Pronto! Acesse:
# - Frontend: http://localhost:5173
# - API: http://localhost:8000/docs
# - MongoDB: localhost:27017
```

---

## Opção 2: Setup Local (Desenvolvimento)

### Backend

```bash
cd backend

# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar .env
cp .env.example .env
# Edite o .env com suas configurações

# 4. Iniciar MongoDB e Redis localmente
# MongoDB: brew services start mongodb-community (Mac)
# Redis: brew services start redis (Mac)

# 5. Popular banco de dados
python -m scripts.seed_database

# 6. Iniciar servidor
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
# Em outro terminal, na raiz do portal-web
npm install

# Iniciar dev server
npm run dev
```

---

## 🎯 Credenciais de Teste

Após popular o banco, use:

```
Email: admin@portal-rpa.com
Senha: admin123
```

ou

```
Email: test@portal-rpa.com
Senha: test123
```

---

## 📡 Endpoints Disponíveis

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# MongoDB Connection
docker-compose exec backend python -c "from database import db_manager; print('MongoDB OK')"
```

---

## 🧪 Testando a API

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@portal-rpa.com","senha":"admin123"}'
```

Copie o `access_token` retornado.

### 2. Listar Clientes
```bash
curl -X GET http://localhost:8000/api/clientes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Criar Solicitação
```bash
curl -X POST http://localhost:8000/api/solicitacoes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "CLIENTE_ID_AQUI",
    "servico": "buscar_documentos",
    "cnjs": ["0001234-56.2024.8.00.0000"]
  }'
```

---

## 🔧 Comandos Úteis

### Docker

```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend

# Parar todos os serviços
docker-compose down

# Limpar tudo (incluindo volumes)
docker-compose down -v

# Rebuild após mudanças no código
docker-compose up -d --build
```

### Backend

```bash
# Rodar seeds novamente
python -m scripts.seed_database

# Ver collections no MongoDB
python -c "from database import db_manager; import asyncio; asyncio.run(db_manager.db.list_collection_names())"

# Criar índices manualmente
python -c "from database import db_manager; import asyncio; asyncio.run(db_manager.init_indexes())"
```

---

## 🐛 Troubleshooting

### Backend não conecta no MongoDB

```bash
# Verificar se MongoDB está rodando
docker-compose ps mongodb

# Verificar logs do MongoDB
docker-compose logs mongodb
```

### Frontend não conecta na API

1. Verifique se o backend está rodando: http://localhost:8000/health
2. Verifique o arquivo `.env` do frontend (se existir)
3. No código, `axiosInstance.ts` deve apontar para `http://localhost:8000/api`

### Erro 401 Unauthorized

- Token expirou (24h de validade)
- Faça login novamente

---

## 📝 Estrutura de Dados

### Clientes Disponíveis (após seed)
- Agibank (codigo: agibank)
- Creditas (codigo: creditas)
- Cogna Educação (codigo: cogna)
- Cliente Demo (codigo: demo)

### Status de Solicitações
- `pendente` - Aguardando processamento
- `em_execucao` - Sendo processado
- `concluido` - Concluído com sucesso
- `erro` - Erro no processamento
- `documentos_nao_encontrados` - Sem documentos

---

## 🎓 Próximos Passos

1. ✅ Backend funcionando? Teste no Swagger
2. ✅ Frontend funcionando? Faça login
3. ⏳ Implemente o Worker RPA para processar CNJs
4. ⏳ Configure Azure Storage real (ou use Azurite)
5. ⏳ Deploy em produção

---

## 📚 Documentação Completa

Veja `README.md` para documentação detalhada da arquitetura e APIs.
