# ⚡ START HERE - Portal Web CNJ

## 🚀 Início Rápido (2 minutos)

### Opção 1: Script Automático (Recomendado)

```bash
chmod +x QUICK_START.sh
./QUICK_START.sh
```

Aguarde ~2 minutos e acesse:
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

**Login:**
- Email: `admin@portal-rpa.com`
- Senha: `admin123`

---

### Opção 2: Passo a Passo Manual

```bash
# 1. Criar .env (se não existir)
cat > .env << 'EOF'
JWT_SECRET_KEY=my-super-secret-jwt-key-2024
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=portal-documentos
EOF

# 2. Subir containers
docker-compose up -d

# 3. Aguardar 30 segundos
sleep 30

# 4. Popular banco
docker-compose exec backend python -m scripts.seed_database
```

---

## ✅ Verificar se Funcionou

```bash
# Backend respondendo?
curl http://localhost:8000/health

# Frontend carregando?
curl -I http://localhost:5173

# MongoDB funcionando?
docker-compose ps mongodb
```

---

## 🎯 Próximos Passos

### 1. Testar API (Swagger)

Acesse: http://localhost:8000/docs

1. Clique em `/api/auth/login`
2. Try it out
3. Execute com:
   ```json
   {
     "email": "admin@portal-rpa.com",
     "senha": "admin123"
   }
   ```
4. Copie o `access_token`
5. Clique em "Authorize" (cadeado no topo)
6. Cole o token
7. Teste outros endpoints!

### 2. Testar Frontend

Acesse: http://localhost:5173

1. Faça login
2. Vá em "Solicitar Serviço"
3. Escolha um cliente
4. Adicione CNJs ou faça upload de Excel
5. Envie a solicitação

### 3. Ver Logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas frontend
docker-compose logs -f frontend
```

---

## ⚠️ Problemas?

Veja: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**Reset completo:**
```bash
docker-compose down -v
docker-compose up -d --build
docker-compose exec backend python -m scripts.seed_database
```

---

## 📚 Documentação Completa

- **Arquitetura & APIs:** [README.md](./README.md)
- **Setup Detalhado:** [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **Progresso:** [PROGRESS.md](./PROGRESS.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## 🎨 Features Disponíveis

- ✅ Login/Registro de usuários
- ✅ Listar clientes disponíveis
- ✅ Criar solicitação (JSON ou Excel)
- ✅ Listar solicitações
- ✅ Ver detalhes de solicitação
- ⏳ Download de documentos (precisa Worker RPA)

---

## 🔑 Dados de Teste

### Usuários
- admin@portal-rpa.com / admin123
- test@portal-rpa.com / test123

### Clientes Cadastrados
- Agibank
- Creditas
- Cogna Educação
- Cliente Demo

### CNJs Válidos para Teste
```
0001234-56.2024.8.00.0000
0005678-90.2023.8.26.0200
4000312-69.2025.8.26.0441
```

---

## 🎯 Testar Fluxo Completo

1. **Login** → Use credenciais de teste
2. **Dashboard** → Veja solicitações recentes
3. **Solicitar** → Crie nova solicitação
4. **Acompanhamento** → Veja status em tempo real
5. **Download** → (quando Worker RPA estiver pronto)

---

**Tempo estimado:** 2-5 minutos
**Última atualização:** 06/11/2025
