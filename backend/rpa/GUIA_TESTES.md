# Guia Completo de Testes - RPA FluxLaw

## 📋 Pré-requisitos

### 1. Dependências Instaladas
```bash
pip install -r requirements.txt
```

### 2. Redis Rodando
```bash
# Windows (Docker)
docker run -d -p 6379:6379 redis:latest

# Verificar se está rodando
redis-cli ping
# Deve retornar: PONG
```

### 3. MongoDB Acessível
- A string de conexão já está configurada em `settings.py`
- Teste a conexão: `python -c "from database import MongoDB; MongoDB.connect(); print('OK')"`

### 4. Chrome Instalado
- O Selenium precisa do Google Chrome instalado
- O webdriver-manager baixa automaticamente o ChromeDriver

---

## 🚀 Teste Completo Automatizado

### Usando o Script de Teste

O script `test_flow.py` executa todo o fluxo automaticamente:

```bash
python test_flow.py
```

**O que o script faz:**
1. ✅ Verifica se API está rodando
2. ✅ Verifica se planilha existe
3. ✅ Faz upload da planilha
4. ✅ Lista tarefas pendentes
5. ✅ Dispara processamento
6. ✅ Aguarda e monitora conclusão
7. ✅ Exibe resultado final

**Saída esperada:**
```
======================================================================
  TESTE COMPLETO DO FLUXO RPA
======================================================================
Data/Hora: 2025-11-06 14:30:00

[PASSO 1] Verificando se a API está rodando
✅ API está rodando

[PASSO 2] Verificando se planilha existe: example_processos.csv
✅ Planilha encontrada: example_processos.csv

[PASSO 3] Fazendo upload da planilha para cliente 'teste_cogna'
✅ Upload realizado com sucesso!
ℹ️  Tarefas criadas: 10
ℹ️  Cliente: teste_cogna

[PASSO 4] Listando tarefas pendentes
✅ Encontradas 10 tarefas pendentes:
  • 12345-2024 (teste_cogna)
  • 67890-2024 (teste_cogna)
  ...

[PASSO 5] Disparando processamento manual
✅ Processamento disparado!

[PASSO 6] Aguardando processamento das tarefas
  • 12345-2024: processing
  • 12345-2024: completed
✅ Tarefa 12345-2024 concluída!
  ℹ️  Arquivo: downloads/teste_cogna/12345-2024.pdf
  ...

======================================================================
  RESULTADO DO TESTE
======================================================================
✅ TESTE CONCLUÍDO COM SUCESSO! 🎉
```

---

## 🔧 Teste Manual Passo a Passo

### PASSO 1: Iniciar Serviços

**Terminal 1 - API:**
```bash
python main.py
```

**Terminal 2 - Worker + Beat:**
```bash
celery -A worker worker --beat --loglevel=info --pool=solo
```

**Verificar se estão rodando:**
- API: http://localhost:8000
- Worker: Deve mostrar logs de conexão com Redis

---

### PASSO 2: Upload da Planilha

**Via cURL:**
```bash
curl -X POST "http://localhost:8000/tasks/upload/teste_cogna" \
  -F "file=@example_processos.csv"
```

**Via Python:**
```python
import requests

with open('example_processos.csv', 'rb') as f:
    files = {'file': ('example_processos.csv', f, 'text/csv')}
    response = requests.post(
        'http://localhost:8000/tasks/upload/teste_cogna',
        files=files
    )
    print(response.json())
```

**Via Swagger UI:**
1. Acesse http://localhost:8000/docs
2. Expanda `POST /tasks/upload/{client_name}`
3. Clique em "Try it out"
4. Digite `teste_cogna` em `client_name`
5. Selecione `example_processos.csv`
6. Clique em "Execute"

**Resposta esperada:**
```json
{
  "message": "Tarefas criadas com sucesso",
  "tasks_created": 10,
  "client_name": "teste_cogna"
}
```

---

### PASSO 3: Verificar Tarefas no MongoDB

**Via API:**
```bash
# Listar todas as tarefas
curl http://localhost:8000/tasks/

# Listar apenas pendentes
curl "http://localhost:8000/tasks/?status_filter=pending"
```

**Via Python:**
```python
import requests

response = requests.get('http://localhost:8000/tasks/', params={'status_filter': 'pending'})
tarefas = response.json()
print(f"Tarefas pendentes: {tarefas['count']}")
```

**Via MongoDB Compass (GUI):**
1. Conecte-se ao MongoDB
2. Database: `projeto_fluxlaw`
3. Collection: `tasks`
4. Filtro: `{ "status": "pending" }`

---

### PASSO 4: Disparar Processamento

**Opção A: Aguardar Celery Beat (10 minutos)**
- Espere 10 minutos
- O Celery Beat automaticamente verifica tarefas pendentes

**Opção B: Disparar Manualmente (Recomendado para testes)**
```bash
# Via cURL
curl -X POST http://localhost:8000/tasks/process-pending

# Via Python
import requests
response = requests.post('http://localhost:8000/tasks/process-pending')
print(response.json())
```

**Resposta esperada:**
```json
{
  "message": "Processamento de tarefas pendentes disparado",
  "task_id": "abc-123-def",
  "info": "As tarefas serão processadas pelo worker em alguns segundos"
}
```

---

### PASSO 5: Monitorar Processamento

**Acompanhar logs do Worker:**
```
[2025-11-06 14:30:15,123: INFO/MainProcess] Task worker.check_pending_tasks[...] received
[2025-11-06 14:30:15,234: INFO/MainProcess] Task worker.process_task[...] received
[2025-11-06 14:30:16,345: INFO/ForkPoolWorker] Iniciando download para processo 12345-2024
[2025-11-06 14:30:17,456: INFO/ForkPoolWorker] Criando driver Chrome local...
[2025-11-06 14:30:20,567: INFO/ForkPoolWorker] Entrando no sistema eLaw...
[2025-11-06 14:30:22,678: INFO/ForkPoolWorker] Fazendo login...
[2025-11-06 14:30:25,789: INFO/ForkPoolWorker] Login realizado com sucesso
[2025-11-06 14:30:30,890: INFO/ForkPoolWorker] Download concluído
[2025-11-06 14:30:32,001: INFO/ForkPoolWorker] Arquivo salvo: temp_downloads/inicial_processo_123452024.pdf
[2025-11-06 14:30:33,112: INFO/ForkPoolWorker] Upload para storage concluído
[2025-11-06 14:30:33,223: INFO/ForkPoolWorker] Task worker.process_task[...] succeeded
```

**Verificar status via API:**
```bash
# Por número de processo
curl http://localhost:8000/tasks/status/12345-2024

# Todas em processamento
curl "http://localhost:8000/tasks/?status_filter=processing"

# Todas concluídas
curl "http://localhost:8000/tasks/?status_filter=completed"
```

---

### PASSO 6: Verificar Resultado

**Verificar arquivos baixados:**
```bash
# Windows
dir downloads\teste_cogna\

# Linux/Mac
ls -la downloads/teste_cogna/
```

**Estrutura esperada:**
```
downloads/
└── teste_cogna/
    ├── 12345-2024.pdf
    ├── 67890-2024.pdf
    ├── 13579-2024.pdf
    └── ...
```

**Verificar no MongoDB:**
```bash
# Via API
curl http://localhost:8000/tasks/status/12345-2024
```

**Resposta esperada:**
```json
{
  "process_number": "12345-2024",
  "status": "completed",
  "file_path": "downloads/teste_cogna/12345-2024.pdf",
  "updated_at": "2025-11-06T14:30:33.223000"
}
```

---

## 🐛 Troubleshooting

### Problema: API não inicia

**Erro:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solução:**
```bash
pip install -r requirements.txt
```

---

### Problema: Worker não conecta ao Redis

**Erro:**
```
[ERROR/MainProcess] consumer: Cannot connect to redis://localhost:6379/0
```

**Solução:**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Se não estiver, inicie
docker run -d -p 6379:6379 redis:latest
```

---

### Problema: MongoDB não conecta

**Erro:**
```
pymongo.errors.ServerSelectionTimeoutError
```

**Solução:**
1. Verificar string de conexão em `settings.py`
2. Verificar se seu IP está na whitelist do MongoDB Atlas
3. Testar conexão: `python -c "from database import MongoDB; MongoDB.connect()"`

---

### Problema: Selenium não encontra Chrome

**Erro:**
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solução:**
1. Instalar Google Chrome
2. O `webdriver-manager` deve baixar automaticamente o driver

---

### Problema: Login do eLaw falha

**Erro:**
```
AuthenticationException: Falha no login do sistema eLaw
```

**Solução:**
1. Verificar credenciais no `.env`:
   ```env
   ELAW_USERNAME=seu_usuario
   ELAW_PASSWORD=sua_senha
   ```
2. Verificar se o site eLaw está acessível
3. Verificar logs para detalhes

---

### Problema: Tarefas ficam em "processing" para sempre

**Causas possíveis:**
1. Worker não está rodando
2. Erro no RPA (verificar logs)
3. Chrome não abre (verificar se Chrome está instalado)

**Solução:**
```bash
# Verificar se worker está rodando
# Deve aparecer nos logs do terminal

# Verificar logs de erro
# Procurar por "ERROR" ou "FAILED" nos logs

# Reprocessar tarefas falhadas manualmente
curl -X POST http://localhost:8000/tasks/process-pending
```

---

## 📊 Monitoramento com Flower

### Instalar Flower
```bash
pip install flower
```

### Iniciar Flower
```bash
celery -A worker flower
```

### Acessar Dashboard
http://localhost:5555

**Recursos:**
- Ver tarefas em tempo real
- Monitorar workers
- Ver estatísticas
- Reprocessar tarefas falhadas

---

## ✅ Checklist de Teste Completo

- [ ] Redis rodando
- [ ] MongoDB acessível
- [ ] Dependências instaladas
- [ ] API iniciada (Terminal 1)
- [ ] Worker iniciado (Terminal 2)
- [ ] Upload de planilha realizado
- [ ] Tarefas criadas no MongoDB (status: pending)
- [ ] Processamento disparado
- [ ] Tarefas processadas (status: completed)
- [ ] Arquivos salvos em `downloads/cliente/`
- [ ] MongoDB atualizado com file_path

---

## 🎯 Teste de Performance

### Testar com 100 processos

1. Criar planilha com 100 processos:
```python
import pandas as pd

processos = [f"{i:05d}-2024" for i in range(1, 101)]
df = pd.DataFrame({'process_number': processos})
df.to_csv('test_100.csv', index=False)
```

2. Fazer upload:
```bash
curl -X POST "http://localhost:8000/tasks/upload/performance_test" \
  -F "file=@test_100.csv"
```

3. Monitorar tempo de processamento

---

## 📝 Logs Importantes

### Logs do Worker
- Localização: Terminal onde executou `celery -A worker`
- Importante: Todas as etapas do RPA são logadas

### Logs da API
- Localização: Terminal onde executou `python main.py`
- Importante: Requests HTTP e erros da API

### Logs do MongoDB
- Via MongoDB Compass ou Atlas
- Verificar documentos criados/atualizados

---

## 🔍 Verificações Rápidas

### API está rodando?
```bash
curl http://localhost:8000/health
```

### Worker está rodando?
Verificar terminal - deve mostrar:
```
[INFO/MainProcess] Connected to redis://localhost:6379/0
```

### Tarefas foram criadas?
```bash
curl "http://localhost:8000/tasks/?status_filter=pending"
```

### Arquivos foram baixados?
```bash
ls -la downloads/teste_cogna/
```

---

## 💡 Dicas

1. **Use o script automatizado** (`python test_flow.py`) para testes rápidos
2. **Monitore os logs** do Worker para ver o progresso em tempo real
3. **Use Flower** para visualização gráfica do processamento
4. **Teste primeiro com poucos processos** (5-10) antes de testar em massa
5. **Verifique sempre os logs** em caso de erro

---

## 📚 Recursos Adicionais

- [README.md](README.md) - Documentação geral
- [PLANO_INTEGRACAO_RPA.md](PLANO_INTEGRACAO_RPA.md) - Detalhes técnicos
- [IMPLEMENTACAO_CONCLUIDA.md](IMPLEMENTACAO_CONCLUIDA.md) - Resumo da implementação
- API Docs: http://localhost:8000/docs (quando API estiver rodando)
