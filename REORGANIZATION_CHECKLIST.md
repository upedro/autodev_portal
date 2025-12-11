# 📋 Checklist de Reorganização - Portal AutoDev

## ✅ Pré-Execução

- [ ] Fazer commit de todas as alterações pendentes
- [ ] Verificar que não há containers rodando: `docker-compose down`
- [ ] Criar branch para reorganização: `git checkout -b refactor/project-structure`
- [ ] Ler este documento completamente antes de executar

---

## 🚀 Execução do Script

### Windows (PowerShell)
```powershell
# 1. Primeiro, execute em modo DRY RUN para visualizar mudanças
.\reorganize.ps1 -DryRun

# 2. Se tudo estiver OK, execute de verdade
.\reorganize.ps1

# 3. Sem backup (NÃO RECOMENDADO)
.\reorganize.ps1 -Backup:$false
```

### Linux/Mac (Bash)
```bash
# 1. Dar permissão de execução
chmod +x reorganize.sh

# 2. Dry run
./reorganize.sh --dry-run

# 3. Executar
./reorganize.sh

# 4. Sem backup
./reorganize.sh --no-backup
```

---

## 📝 Correções Obrigatórias Após Reorganização

### 1️⃣ **infra/docker-compose.yml** (CRÍTICO)

Atualize os `build.context` e `build.dockerfile`:

```yaml
services:
  frontend:
    build:
      context: ../src/frontend          # ANTES: ./frontend
      dockerfile: ../../infra/docker/Dockerfile.frontend  # ANTES: Dockerfile
    volumes:
      - ../src/frontend:/app            # ANTES: ./frontend:/app

  api:
    build:
      context: ../src/api               # ANTES: ./backend/api
      dockerfile: ../../infra/docker/Dockerfile.api  # ANTES: Dockerfile
    volumes:
      - ../src/api:/app                 # ANTES: ./backend/api:/app

  rpa-worker:
    build:
      context: ../src/rpa               # ANTES: ./backend/rpa
      dockerfile: ../../infra/docker/Dockerfile.rpa  # ANTES: Dockerfile
    volumes:
      - ../src/rpa:/app                 # ANTES: ./backend/rpa:/app

  rpa-beat:
    build:
      context: ../src/rpa               # ANTES: ./backend/rpa
      dockerfile: ../../infra/docker/Dockerfile.rpa  # ANTES: Dockerfile
```

**Status:** [ ] Corrigido

---

### 2️⃣ **infra/docker/Dockerfile.api** (CRÍTICO)

Nenhuma alteração necessária - o Dockerfile já usa caminhos relativos corretos:
```dockerfile
COPY requirements.txt .
COPY . .
```

**Status:** [ ] Verificado (sem alterações necessárias)

---

### 3️⃣ **infra/docker/Dockerfile.rpa** (CRÍTICO)

Nenhuma alteração necessária - o Dockerfile já usa caminhos relativos corretos:
```dockerfile
COPY requirements.txt .
COPY . .
```

**Status:** [ ] Verificado (sem alterações necessárias)

---

### 4️⃣ **infra/docker/Dockerfile.frontend** (CRÍTICO)

Nenhuma alteração necessária - o Dockerfile já usa caminhos relativos corretos:
```dockerfile
COPY package*.json ./
COPY . .
```

**Status:** [ ] Verificado (sem alterações necessárias)

---

### 5️⃣ **scripts/deploy.ps1** (CRÍTICO)

Atualize o caminho do docker-compose:

```powershell
# ANTES:
docker compose up -d frontend api rpa-worker rpa-beat redis

# DEPOIS:
docker compose -f infra/docker-compose.yml up -d frontend api rpa-worker rpa-beat redis
```

**Linhas a atualizar:**
- Linha ~72: `docker compose -f infra/docker-compose.yml up -d ...`
- Linha ~83: `docker compose -f infra/docker-compose.yml --profile with-mongodb up -d`
- Linha ~94: `docker compose -f infra/docker-compose.yml --profile with-mongodb --profile monitoring up -d`
- Linha ~106: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d`
- Linha ~112: `docker compose -f infra/docker-compose.yml --profile with-mongodb --profile monitoring down`
- Linha ~117: `docker compose -f infra/docker-compose.yml restart`
- Linha ~123-136: Todos os comandos de logs
- Linha ~140: `docker compose -f infra/docker-compose.yml --profile with-mongodb --profile monitoring down -v --remove-orphans`
- Linha ~147: `docker compose -f infra/docker-compose.yml build`
- Linha ~172: `docker compose -f infra/docker-compose.yml exec -T redis redis-cli ping`

**Status:** [ ] Corrigido

---

### 6️⃣ **CLAUDE.md** (IMPORTANTE)

Atualize os paths de exemplo:

```markdown
# ANTES:
cd backend/api && pip install -r requirements.txt
cd backend/rpa && pip install -r requirements.txt
python test_rpa_standalone_cogna.py

# DEPOIS:
cd src/api && pip install -r requirements.txt
cd src/rpa && pip install -r requirements.txt
python test_rpa_standalone_cogna.py  # (sem mudança, já estará em src/rpa)
```

**Atualize a seção Architecture:**
```markdown
autodev_portal/
├── src/                      # Código-fonte
│   ├── frontend/             # React + Vite + TypeScript + Tailwind
│   ├── api/                  # FastAPI Portal API (port 8001)
│   └── rpa/                  # Celery Workers - Selenium Automation
├── infra/                    # Infraestrutura
│   ├── docker/               # Dockerfiles
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── docs/                     # Documentação
└── scripts/                  # Scripts de automação
```

**Status:** [ ] Corrigido

---

### 7️⃣ **README.md** (IMPORTANTE)

Atualize a seção de arquitetura e comandos:

```markdown
## Comandos

```powershell
# Desenvolvimento
.\scripts\deploy.ps1 dev          # Frontend + API + RPA + Redis
.\scripts\deploy.ps1 dev-mongo    # + MongoDB local
.\scripts\deploy.ps1 dev-full     # + Flower (monitoramento)

# Sem Docker
cd src/frontend && npm install && npm run dev
cd src/api && uvicorn main:app --reload --port 8001
cd src/rpa && celery -A portal_worker worker --loglevel=info --pool=solo
```
```

**Status:** [ ] Corrigido

---

### 8️⃣ **src/api/main.py** (VERIFICAR)

Verifique se há imports relativos ou referências a caminhos absolutos. Provavelmente não precisa alteração.

**Status:** [ ] Verificado

---

### 9️⃣ **src/rpa/portal_worker.py** (VERIFICAR)

Verifique se há imports relativos ou referências a caminhos absolutos. Provavelmente não precisa alteração.

**Status:** [ ] Verificado

---

### 🔟 **src/frontend/package.json** (VERIFICAR)

Verifique se há scripts com referências a paths absolutos. Provavelmente não precisa alteração.

**Status:** [ ] Verificado

---

## 🧪 Testes Pós-Reorganização

Execute os seguintes testes na ordem:

### 1. Teste de Build
```powershell
cd infra
docker-compose build --no-cache
```
**Status:** [ ] Passou

### 2. Teste de Inicialização
```powershell
cd ..
.\scripts\deploy.ps1 dev
```
**Status:** [ ] Passou

### 3. Teste de Saúde
```powershell
.\scripts\deploy.ps1 health
```
**Status:** [ ] Passou

### 4. Teste Frontend
- [ ] Acesse http://localhost:5173
- [ ] Verifique se a página carrega
- [ ] Teste o login

### 5. Teste API
- [ ] Acesse http://localhost:8001/docs
- [ ] Verifique se a documentação carrega
- [ ] Teste um endpoint

### 6. Teste RPA
```powershell
docker-compose -f infra/docker-compose.yml logs rpa-worker
```
- [ ] Verifique se não há erros de import
- [ ] Verifique se o Celery iniciou corretamente

---

## 🗑️ Arquivos para Deletar (Após Confirmação)

### Duplicados/Obsoletos
- [ ] `backend/rpa/_del_docker-compose.yml`
- [ ] `backend/api/` (diretório vazio)
- [ ] `backend/rpa/` (diretório vazio)
- [ ] `backend/` (diretório vazio)
- [ ] `frontend/` (diretório vazio, exceto se houver configs raiz)

### Documentação Archive (revisar antes de deletar)
- [ ] `docs/archive/_del_IMPLEMENTACAO_CONCLUIDA.md`
- [ ] `docs/archive/_del_PLANO_INTEGRACAO_RPA.md`
- [ ] `docs/archive/_del_MELHORIAS_TESTE.md`
- [ ] `docs/archive/_del_START_TESTE.md`
- [ ] `docs/archive/_del_TESTE_STANDALONE.md`
- [ ] `docs/archive/_del_COMO_TESTAR_SUPERSIM_GED.md`
- [ ] `docs/archive/_del_README_API_INTEGRATION.md`
- [ ] `docs/archive/_del_README_TESTES_GED.md`
- [ ] `docs/archive/_del_CLAUDE_RPA.md`

**⚠️ IMPORTANTE:** Não delete nada até confirmar que:
1. Todos os testes passaram
2. Você revisou o conteúdo dos arquivos _del_
3. Nenhuma informação importante será perdida

---

## 📦 Comandos de Limpeza Final

Após confirmar que tudo funciona:

```powershell
# 1. Deletar diretórios vazios
Remove-Item backend/api -Force -ErrorAction SilentlyContinue
Remove-Item backend/rpa -Force -ErrorAction SilentlyContinue
Remove-Item backend -Force -ErrorAction SilentlyContinue
Remove-Item frontend -Force -ErrorAction SilentlyContinue

# 2. Deletar arquivos marcados com _del_
Get-ChildItem -Recurse -Filter "_del_*" | Remove-Item -Force

# 3. Commitar mudanças
git add .
git commit -m "refactor: reorganize project structure following clean architecture"
git push origin refactor/project-structure

# 4. Criar PR
gh pr create --title "Reorganização da estrutura do projeto" --body "Aplicando Clean Architecture e 12-Factor App"
```

---

## 🆘 Rollback (Em caso de problemas)

Se algo der errado:

```powershell
# 1. Restaurar do backup
$BACKUP_DIR = "backup_YYYYMMDD_HHMMSS"  # Use o timestamp do seu backup
Copy-Item "$BACKUP_DIR/*" . -Recurse -Force

# 2. Ou reverter pelo Git
git reset --hard HEAD
git clean -fd

# 3. Ou voltar para branch anterior
git checkout main
```

---

## ✅ Checklist Final

- [ ] Todos os testes passaram
- [ ] Documentação atualizada (README.md, CLAUDE.md)
- [ ] Build funciona corretamente
- [ ] Aplicação roda sem erros
- [ ] Arquivos _del_ revisados e deletados
- [ ] Diretórios vazios removidos
- [ ] Commit realizado
- [ ] PR criado (se aplicável)
- [ ] Backup pode ser deletado (após 1 semana)

---

## 📞 Suporte

Em caso de dúvidas ou problemas:
1. Verifique os logs: `.\scripts\deploy.ps1 logs`
2. Revise este checklist
3. Consulte o backup criado
4. Peça ajuda ao Tech Lead

**Data de Reorganização:** _____________
**Executado por:** _____________
**Tempo total:** _____________
