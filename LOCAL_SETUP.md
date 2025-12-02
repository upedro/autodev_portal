# 🚀 Setup Local - Sem Docker

## Setup Rápido (MongoDB Atlas + Local Backend/Frontend)

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Redis (local)

---

## 1️⃣ Backend Setup

```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# O arquivo .env já está configurado com MongoDB Atlas!

# Popular banco de dados
python -m scripts.seed_database

# Iniciar servidor
uvicorn main:app --reload --port 8000
```

**Backend rodando em:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

---

## 2️⃣ Frontend Setup

```bash
# Em outro terminal, na raiz do portal-web
npm install

# Iniciar dev server
npm run dev
```

**Frontend rodando em:** http://localhost:5173

---

## 3️⃣ Redis (Necessário)

### Mac/Linux
```bash
# Instalar
brew install redis

# Iniciar
brew services start redis

# Ou rodar manualmente
redis-server
```

### Windows
```bash
# Baixar de: https://github.com/microsoftarchive/redis/releases
# Ou usar WSL2 com: sudo apt install redis-server
redis-server
```

### Docker (alternativa)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## ✅ Verificar Setup

```bash
# Redis rodando?
redis-cli ping
# Deve retornar: PONG

# Backend rodando?
curl http://localhost:8000/health
# Deve retornar: {"status":"healthy"}

# Frontend carregando?
curl -I http://localhost:5173
# Deve retornar: HTTP/1.1 200 OK
```

---

## 🎯 Login

**Credenciais:**
- Email: `admin@portal-rpa.com`
- Senha: `admin123`

ou

- Email: `test@portal-rpa.com`
- Senha: `test123`

---

## 🔧 Comandos Úteis

### Backend

```bash
# Ativar venv
source venv/bin/activate

# Rodar seeds novamente
python -m scripts.seed_database

# Ver coleções no MongoDB
python -c "from database import db_manager; import asyncio; print(asyncio.run(db_manager.db.list_collection_names()))"

# Criar índices
python -c "from database import db_manager; import asyncio; asyncio.run(db_manager.init_indexes())"

# Rodar servidor com auto-reload
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
# Instalar dependências
npm install

# Dev server
npm run dev

# Build para produção
npm run build

# Preview build
npm run preview
```

---

## 📊 Estrutura de Dados

### MongoDB Atlas Collections
- `usuarios` - Usuários do sistema
- `clientes` - Clientes/empresas
- `solicitacoes` - Solicitações de serviço
- `eventos` - Event store para workers

### Clientes Pré-cadastrados
- Agibank (codigo: agibank)
- Creditas (codigo: creditas)
- Cogna Educação (codigo: cogna)
- Cliente Demo (codigo: demo)

---

## 🐛 Troubleshooting

### Backend não conecta no MongoDB Atlas

**Erro:** `ServerSelectionTimeoutError`

**Solução:**
1. Verifique se sua conexão está permitida no MongoDB Atlas
2. Vá em: Database → Network Access
3. Adicione seu IP ou permita `0.0.0.0/0` (dev only!)

### Erro: Module not found

```bash
# Certifique-se que o venv está ativado
source venv/bin/activate

# Reinstale dependências
pip install -r requirements.txt
```

### Redis connection refused

```bash
# Iniciar Redis
brew services start redis

# Ou manualmente
redis-server
```

### Frontend - CORS error

Verifique que o backend está em `http://localhost:8000` e configurado no `axiosInstance.ts`

---

## 📝 Variáveis de Ambiente

### backend/.env (já configurado)
```env
MONGODB_URI=mongodb+srv://...  # MongoDB Atlas
MONGODB_DB_NAME=portal_rpa
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=my-super-secret-jwt-key-2024
```

---

## 🎓 Próximos Passos

1. ✅ Backend + Frontend rodando
2. ✅ Login funcionando
3. ✅ Criar solicitação via UI
4. ⏳ Implementar Worker RPA para processar CNJs

---

**Tempo estimado de setup:** 5-10 minutos
**MongoDB:** Remoto (Atlas) ✅
**Backend:** Local (Python) ✅
**Frontend:** Local (Node) ✅
**Redis:** Local ✅
