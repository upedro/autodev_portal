# Worker de Integração Portal → RPA

## Visão Geral

Este worker faz a ponte entre o Portal Web e o sistema RPA existente, convertendo solicitações do portal em tasks no formato do RPA.

## Arquitetura

```
Portal Web (Solicitacoes)
         ↓
[SolicitacaoToTaskConverter]
         ↓
    MongoDB tasks
         ↓
    RPA Existente
         ↓
[TaskStatusMonitor]
         ↓
Portal Web (Atualiza Status)
```

## Componentes

### 1. SolicitacaoToTaskConverter

**Função:** Escuta eventos `NOVA_SOLICITACAO` e cria tasks no formato RPA

**Fluxo:**
1. Escuta collection `eventos` com tipo `NOVA_SOLICITACAO`
2. Busca a solicitação no MongoDB
3. Para cada CNJ na solicitação:
   - Cria uma task na collection `tasks`
   - Formato: `{process_number, client_name, status: "pending"}`
4. Atualiza solicitação para status `EM_EXECUCAO`
5. Marca evento como processado

### 2. TaskStatusMonitor

**Função:** Monitora tasks do RPA e atualiza solicitações do portal

**Fluxo:**
1. Monitora collection `tasks` com `portal_metadata.source = "portal_web"`
2. Quando status de uma task muda:
   - Atualiza array `resultados` da solicitação
   - Incrementa contadores (`cnjs_processados`, `cnjs_sucesso`, `cnjs_erro`)
3. Quando todos CNJs processados:
   - Atualiza status geral da solicitação para `CONCLUIDO` ou `ERRO`

## Formato de Dados

### Task RPA (collection: tasks)
```json
{
  "_id": ObjectId("..."),
  "process_number": "0001234-56.2024.8.00.0000",
  "client_name": "agibank",
  "status": "pending",  // pending → processing → completed/failed
  "file_path": null,     // Preenchido quando completed
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "portal_metadata": {
    "solicitacao_id": "690dc9d4538b6f438726e053",
    "source": "portal_web",
    "created_by": "solicitacao_worker"
  }
}
```

### Solicitacao (collection: solicitacoes)
```json
{
  "_id": ObjectId("..."),
  "user_id": "...",
  "cliente_id": "...",
  "cnjs": ["0001234-56.2024.8.00.0000"],
  "status": "em_execucao",
  "total_cnjs": 1,
  "cnjs_processados": 0,
  "cnjs_sucesso": 0,
  "cnjs_erro": 0,
  "resultados": [],
  "rpa_task_ids": ["690cba42765b6cdf636afa11"],  // IDs das tasks criadas
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

## Mapeamento de Status

| RPA Task Status | Portal Solicitacao Status |
|----------------|---------------------------|
| pending | pendente |
| processing | em_execucao |
| completed | concluido |
| failed | erro |

## Como Executar

### Opção 1: Standalone

```bash
cd backend
source venv/bin/activate

# Executar worker
python -m workers.solicitacao_to_task_worker
```

### Opção 2: Como Serviço (systemd)

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/portal-rpa-worker.service
```

Conteúdo:
```ini
[Unit]
Description=Portal RPA Worker
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/portal-web/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m workers.solicitacao_to_task_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl enable portal-rpa-worker
sudo systemctl start portal-rpa-worker
sudo systemctl status portal-rpa-worker
```

### Opção 3: Docker

Adicionar ao `docker-compose.yml`:
```yaml
worker:
  build:
    context: ./backend
  command: python -m workers.solicitacao_to_task_worker
  environment:
    MONGODB_URI: mongodb://mongodb:27017
    # ... outras variáveis
  depends_on:
    - mongodb
```

## Logs

O worker registra todas as operações:

```
🤖 Starting Solicitacao to Task converter...
👀 Starting Task Status Monitor...
📋 Processing solicitacao 690dc9d4538b6f438726e053
✅ Created 1 RPA tasks for solicitacao 690dc9d4538b6f438726e053
📊 Updating solicitacao 690dc9d4538b6f438726e053 for CNJ 0001234-56.2024.8.00.0000: completed
✅ Solicitacao 690dc9d4538b6f438726e053 completed: concluido
```

## Verificação

### Verificar se worker está processando

```bash
# Ver eventos pendentes
python -c "
from database import db_manager
import asyncio

async def check():
    db = db_manager.db
    eventos = await db.eventos.count_documents({'processado': False})
    print(f'Eventos pendentes: {eventos}')

asyncio.run(check())
"

# Ver tasks criadas
python -c "
from database import db_manager
import asyncio

async def check():
    db = db_manager.db
    tasks = await db.tasks.find({'portal_metadata.source': 'portal_web'}).to_list(length=10)
    print(f'Tasks do portal: {len(tasks)}')
    for task in tasks:
        print(f'  - {task[\"process_number\"]}: {task[\"status\"]}')

asyncio.run(check())
"
```

## Integração com RPA Existente

O RPA deve:

1. **Buscar tasks pendentes:**
```python
tasks = db.tasks.find({"status": "pending"})
```

2. **Processar cada task:**
```python
# Atualizar para processing
db.tasks.update_one(
    {"_id": task_id},
    {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
)

# Buscar documentos...
# Upload para Azure...

# Marcar como completed
db.tasks.update_one(
    {"_id": task_id},
    {"$set": {
        "status": "completed",
        "file_path": "azure_blob_url",
        "updated_at": datetime.utcnow()
    }}
)
```

3. **O TaskStatusMonitor automaticamente atualizará a solicitação!**

## Troubleshooting

### Worker não processa eventos

Verifique:
```bash
# Worker rodando?
ps aux | grep solicitacao_to_task_worker

# Eventos na fila?
mongo --eval "db.eventos.find({processado: false}).count()"

# Logs
tail -f /tmp/worker.log  # ou onde estiver configurado
```

### Tasks não são criadas

Verifique:
- MongoDB conectado?
- Cliente existe na collection `clientes`?
- CNJs são válidos?

### Solicitações não atualizam

Verifique:
- TaskStatusMonitor rodando?
- Tasks têm `portal_metadata.source = "portal_web"`?
- Status das tasks está mudando?

## Próximos Passos

1. ✅ Worker de integração criado
2. ⏳ Adaptar RPA existente para processar tasks
3. ⏳ Configurar Azure Storage no RPA
4. ⏳ Testar fluxo E2E completo
