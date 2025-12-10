# 🚀 Início Rápido - Teste Completo

## Para executar o teste agora, siga estes passos:

### 1️⃣ Instalar Dependências (Se ainda não fez)
```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env
copy .env.example .env

# Editar .env e adicionar credenciais do Azure (se tiver)
# Caso contrário, usar armazenamento local (já configurado)
```

### 3️⃣ Iniciar Redis (Se ainda não está rodando)
```bash
# Via Docker (Recomendado)
docker run -d -p 6379:6379 --name redis-fluxlaw redis:latest

# Verificar
docker exec redis-fluxlaw redis-cli ping
# Deve retornar: PONG
```

### 4️⃣ Abrir 2 Terminais

**Terminal 1 - Iniciar API:**
```bash
cd d:\Files\Auryn\autodev\rpa-fluxlaw
python main.py
```

Aguarde até ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Iniciar Worker:**
```bash
cd d:\Files\Auryn\autodev\rpa-fluxlaw
celery -A worker worker --beat --loglevel=info --pool=solo
```

Aguarde até ver:
```
[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/Beat] Scheduler: Sending due task check-pending-tasks-every-10-minutes
```

### 5️⃣ Executar Teste (Em um 3º terminal)
```bash
cd d:\Files\Auryn\autodev\rpa-fluxlaw
python test_flow.py
```

---

## 📋 O que o teste fará:

1. ✅ Verificar se API está rodando
2. ✅ Verificar se planilha `example_processos.csv` existe
3. ✅ Fazer upload da planilha para cliente `teste_cogna`
4. ✅ Criar 10 tarefas no MongoDB (status: pending)
5. ✅ Disparar processamento manual (não espera 10 minutos)
6. ✅ Worker processa as tarefas:
   - Abre Chrome
   - Faz login no eLaw COGNA
   - Busca cada processo
   - Baixa documento
   - Renomeia e move para `temp_downloads/`
   - Faz upload para `downloads/teste_cogna/`
   - Atualiza MongoDB (status: completed)
7. ✅ Monitora e exibe progresso
8. ✅ Exibe resultado final

---

## 🎯 Resultado Esperado

### No terminal do teste:
```
======================================================================
  RESULTADO DO TESTE
======================================================================
✅ TESTE CONCLUÍDO COM SUCESSO! 🎉
ℹ️  Todas as 10 tarefas foram processadas
ℹ️  Verifique os arquivos em: downloads/teste_cogna/
```

### Arquivos criados:
```
downloads/
└── teste_cogna/
    ├── 12345-2024.pdf
    ├── 67890-2024.pdf
    ├── 13579-2024.pdf
    ├── 24680-2024.pdf
    ├── 11111-2024.pdf
    ├── 22222-2024.pdf
    ├── 33333-2024.pdf
    ├── 44444-2024.pdf
    ├── 55555-2024.pdf
    └── 66666-2024.pdf
```

### No MongoDB:
- 10 documentos na collection `tasks`
- Todos com `status: "completed"`
- Todos com `file_path` preenchido

---

## 🔧 Se algo der errado:

### Erro: "API não está rodando"
- Certifique-se de que o Terminal 1 está executando `python main.py`
- Verifique http://localhost:8000

### Erro: "Worker não conecta ao Redis"
- Certifique-se de que Redis está rodando: `redis-cli ping`
- Se não estiver, execute: `docker run -d -p 6379:6379 redis:latest`

### Erro: "Falha no login do eLaw"
- Verifique as credenciais no `.env`
- Verifique se o site eLaw está acessível
- Veja os logs do Worker para detalhes

### Tarefas ficam "processing" para sempre
- Verifique os logs do Worker (Terminal 2)
- Procure por erros (ERROR, FAILED)
- Verifique se Chrome está instalado

---

## 📊 Monitorar Progresso

### Via Logs do Worker (Terminal 2)
Você verá em tempo real:
```
[INFO] Iniciando download para processo 12345-2024
[INFO] Criando driver Chrome local...
[INFO] Entrando no sistema eLaw...
[INFO] Fazendo login...
[INFO] Login realizado com sucesso
[INFO] Download concluído
[INFO] Arquivo salvo: temp_downloads/inicial_processo_123452024.pdf
[INFO] Upload para storage concluído
```

### Via API (Durante o teste)
Em outro terminal:
```bash
# Ver tarefas em processamento
curl "http://localhost:8000/tasks/?status_filter=processing"

# Ver tarefas concluídas
curl "http://localhost:8000/tasks/?status_filter=completed"

# Ver uma tarefa específica
curl http://localhost:8000/tasks/status/12345-2024
```

---

## ⚡ Teste Rápido (Sem RPA real)

Se quiser apenas testar a integração (sem executar o RPA real), você pode:

1. Comentar a chamada do RPA em `worker.py`:
```python
# Comentar esta linha:
# local_file_path = download_document(process_number, client_name)

# Adicionar esta linha (criar arquivo fake):
local_file_path = os.path.join("temp_downloads", f"{client_name}_{process_number}.pdf")
open(local_file_path, 'w').write("teste")
```

2. Executar o teste normalmente

Isso criará arquivos fake e testará todo o resto (upload, storage, MongoDB).

---

## 📞 Ajuda

Consulte o [GUIA_TESTES.md](GUIA_TESTES.md) para:
- Troubleshooting detalhado
- Testes manuais passo a passo
- Monitoramento com Flower
- Testes de performance

---

## ✅ Checklist Antes de Iniciar

- [ ] Redis instalado e rodando
- [ ] Python 3.9+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Google Chrome instalado
- [ ] MongoDB acessível (Atlas)
- [ ] Arquivo `.env` configurado
- [ ] Planilha `example_processos.csv` existe
- [ ] 2 terminais abertos (API + Worker)

**Pronto! Execute `python test_flow.py` e veja a mágica acontecer! ✨**
