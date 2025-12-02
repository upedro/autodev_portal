# 🔧 Troubleshooting Guide - Portal Web CNJ

## Problemas Comuns e Soluções

---

## 1. Docker Compose - Variáveis de Ambiente

### ❌ Erro
```
WARN[0000] The "AZURE_STORAGE_CONNECTION_STRING" variable is not set
```

### ✅ Solução

**Opção 1: Criar arquivo .env na raiz**
```bash
cat > .env << 'EOF'
JWT_SECRET_KEY=my-super-secret-jwt-key-2024
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=portal-documentos
EOF
```

**Opção 2: Usar script automático**
```bash
chmod +x QUICK_START.sh
./QUICK_START.sh
```

---

## 2. Backend não conecta no MongoDB

### ❌ Sintomas
- Backend crasha ao iniciar
- Erro: "Connection refused" ou "Cannot connect to MongoDB"

### ✅ Solução

**Verificar se MongoDB está rodando:**
```bash
docker-compose ps mongodb
```

**Ver logs do MongoDB:**
```bash
docker-compose logs mongodb
```

**Reiniciar MongoDB:**
```bash
docker-compose restart mongodb
docker-compose restart backend
```

---

## 3. Frontend não carrega

### ❌ Sintomas
- Página em branco
- Erro 404 ou Cannot GET /

### ✅ Solução

**Verificar se node_modules está instalado:**
```bash
docker-compose exec frontend ls -la /app/node_modules | head
```

**Rebuild frontend:**
```bash
docker-compose down frontend
docker-compose up -d --build frontend
```

**Ver logs:**
```bash
docker-compose logs -f frontend
```

---

## 4. API retorna 401 Unauthorized

### ❌ Sintomas
- Login funciona mas outras rotas retornam 401
- Token JWT inválido

### ✅ Solução

**Verificar token no localStorage:**
```javascript
// No browser console
localStorage.getItem('token')
```

**Fazer logout e login novamente:**
```bash
# Limpar localStorage no browser
localStorage.clear()
```

**Verificar JWT_SECRET_KEY:**
```bash
docker-compose exec backend env | grep JWT_SECRET_KEY
```

---

## 5. Upload de Excel falha

### ❌ Sintomas
- Erro ao fazer upload de planilha
- "Invalid Excel file format"

### ✅ Solução

**Verificar formato do arquivo:**
- Deve ser `.xlsx` ou `.xls`
- Pelo menos uma célula com CNJ válido

**Formato CNJ válido:**
```
0001234-56.2024.8.00.0000
```

**Testar CNJ manualmente:**
```bash
curl -X POST http://localhost:8000/api/solicitacoes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":"ID","servico":"buscar_documentos","cnjs":["0001234-56.2024.8.00.0000"]}'
```

---

## 6. Seed database falha

### ❌ Sintomas
- Script seed_database.py retorna erro
- Usuários não são criados

### ✅ Solução

**Verificar conexão MongoDB:**
```bash
docker-compose exec backend python -c "from pymongo import MongoClient; print(MongoClient('mongodb://mongodb:27017').server_info())"
```

**Limpar banco e tentar novamente:**
```bash
docker-compose exec mongodb mongosh portal_rpa --eval "db.dropDatabase()"
docker-compose exec backend python -m scripts.seed_database
```

---

## 7. Docker build muito lento

### ❌ Sintomas
- Build demora mais de 5 minutos
- Download de pacotes Python/NPM trava

### ✅ Solução

**Usar cache do Docker:**
```bash
docker-compose build
```

**Rebuild sem cache (último recurso):**
```bash
docker-compose build --no-cache
```

**Limpar containers antigos:**
```bash
docker system prune -a
```

---

## 8. Porta já em uso

### ❌ Sintomas
```
Error: Port 8000 is already in use
Error: Port 5173 is already in use
```

### ✅ Solução

**Verificar processos usando as portas:**
```bash
lsof -i :8000
lsof -i :5173
lsof -i :27017
```

**Matar processos:**
```bash
kill -9 $(lsof -t -i:8000)
kill -9 $(lsof -t -i:5173)
```

**Ou mudar portas no docker-compose.yml:**
```yaml
ports:
  - "8001:8000"  # Usar porta 8001 no host
```

---

## 9. Cannot read property 'data' of undefined

### ❌ Sintomas
- Erro no console do browser
- Requisições falham

### ✅ Solução

**Verificar se backend está rodando:**
```bash
curl http://localhost:8000/health
```

**Verificar URL da API:**
```bash
# No arquivo src/api/axiosInstance.ts
# Deve apontar para: http://localhost:8000/api
```

**Verificar CORS:**
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://localhost:8000/api/clientes -v
```

---

## 10. Azure Storage errors

### ❌ Sintomas
- Erro ao tentar fazer upload de documentos
- "Storage service unavailable"

### ✅ Solução Temporária (Dev)

**Deixar AZURE_STORAGE_CONNECTION_STRING vazio:**
```bash
# No .env
AZURE_STORAGE_CONNECTION_STRING=
```

**O sistema continuará funcionando, mas:**
- Downloads não funcionarão
- Apenas para desenvolvimento

**Solução Permanente:**
```bash
# Usar Azurite (Azure Storage Emulator)
docker run -p 10000:10000 mcr.microsoft.com/azure-storage/azurite azurite-blob --blobHost 0.0.0.0

# Ou configurar Azure Storage real
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

---

## 🚨 Emergency Reset

Se nada funcionar, reset completo:

```bash
# 1. Parar tudo
docker-compose down -v

# 2. Limpar Docker
docker system prune -af
docker volume prune -f

# 3. Limpar arquivos locais
rm -rf backend/__pycache__
rm -rf backend/**/__pycache__
rm -rf node_modules

# 4. Rebuild do zero
docker-compose build --no-cache

# 5. Subir novamente
docker-compose up -d

# 6. Seed
docker-compose exec backend python -m scripts.seed_database
```

---

## 📊 Verificação de Saúde do Sistema

**Script de verificação rápida:**

```bash
#!/bin/bash
echo "🏥 Health Check"
echo "==============="

echo -n "MongoDB: "
docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" --quiet && echo "✅" || echo "❌"

echo -n "Redis: "
docker-compose exec -T redis redis-cli ping | grep -q PONG && echo "✅" || echo "❌"

echo -n "Backend: "
curl -s http://localhost:8000/health | grep -q healthy && echo "✅" || echo "❌"

echo -n "Frontend: "
curl -s http://localhost:5173 > /dev/null && echo "✅" || echo "❌"
```

---

## 📞 Ainda com Problemas?

1. Verifique os logs:
```bash
docker-compose logs -f
```

2. Verifique as issues no GitHub

3. Entre em contato com o time

---

## 🎯 Checklist de Debug

- [ ] Arquivo `.env` existe na raiz?
- [ ] Arquivo `backend/.env` existe?
- [ ] Docker está rodando?
- [ ] Portas 8000, 5173, 27017 estão livres?
- [ ] MongoDB está saudável? (`docker-compose ps`)
- [ ] Logs não mostram erros? (`docker-compose logs`)
- [ ] Seed foi executado? (verifique usuários no MongoDB)
- [ ] Token JWT está válido?
- [ ] CORS está configurado corretamente?

---

**Última atualização:** 06/11/2025
