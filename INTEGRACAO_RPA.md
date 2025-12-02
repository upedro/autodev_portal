# 🔗 Guia de Integração Portal Web ↔ RPA

## Visão Geral

Este guia explica como integrar o Portal Web com o sistema RPA existente usando a tabela `tasks` do MongoDB.

---

## 🏗️ Arquitetura de Integração

```
┌─────────────────┐
│  Portal Web     │
│  (Solicitações) │
└────────┬────────┘
         │ Cria evento
         ▼
┌─────────────────┐
│ Worker Bridge   │ ← solicitacao_to_task_worker.py
│ (Conversor)     │
└────────┬────────┘
         │ Cria tasks
         ▼
┌─────────────────┐
│  MongoDB tasks  │ ← Tabela existente do RPA
│  (RPA Format)   │
└────────┬────────┘
         │ Processa
         ▼
┌─────────────────┐
│  RPA System     │ ← Sistema existente
│  (Selenium)     │
└────────┬────────┘
         │ Atualiza status
         ▼
┌─────────────────┐
│ Worker Monitor  │ ← Parte do solicitacao_to_task_worker.py
│ (Status Sync)   │
└────────┬────────┘
         │ Atualiza resultados
         ▼
┌─────────────────┐
│  Portal Web     │
│  (Atualizado)   │
└─────────────────┘
```

---

## 📋 Formato de Dados

### 1. Solicitação do Portal (collection: solicitacoes)

```json
{
  "_id": ObjectId("690dc9d4538b6f438726e053"),
  "user_id": "690dc2b0b87de491cd982e82",
  "cliente_id": "690dc2b0b87de491cd982e86",
  "servico": "buscar_documentos",
  "cnjs": [
    "4000312-69.2025.8.26.0441",
    "0001234-56.2024.8.00.0000"
  ],
  "status": "em_execucao",
  "total_cnjs": 2,
  "cnjs_processados": 0,
  "cnjs_sucesso": 0,
  "cnjs_erro": 0,
  "resultados": [],
  "rpa_task_ids": [],  // Será preenchido pelo worker
  "created_at": ISODate("2025-11-07T10:28:36.738Z"),
  "updated_at": ISODate("2025-11-07T10:28:36.738Z")
}
```

### 2. Task do RPA (collection: tasks)

```json
{
  "_id": ObjectId("690cba42765b6cdf636afa11"),
  "process_number": "4000312-69.2025.8.26.0441",
  "client_name": "cogna",
  "status": "pending",  // pending → processing → completed/failed
  "file_path": null,     // Azure blob path quando completed
  "created_at": ISODate("2025-11-07T10:28:40.000Z"),
  "updated_at": ISODate("2025-11-07T10:28:40.000Z"),
  "portal_metadata": {
    "solicitacao_id": "690dc9d4538b6f438726e053",
    "source": "portal_web",
    "created_by": "solicitacao_worker"
  }
}
```

---

## 🔄 Fluxo Completo

### Passo 1: Usuário Cria Solicitação no Portal

```
POST /api/solicitacoes
{
  "cliente_id": "690dc2b0b87de491cd982e86",
  "servico": "buscar_documentos",
  "cnjs": ["4000312-69.2025.8.26.0441"]
}
```

**Backend cria:**
1. Documento em `solicitacoes` (status: `pendente`)
2. Evento em `eventos` (tipo: `NOVA_SOLICITACAO`)

---

### Passo 2: Worker Converte para Tasks

**Worker `SolicitacaoToTaskConverter`:**

1. Lê evento `NOVA_SOLICITACAO`
2. Busca solicitação
3. Para cada CNJ, cria task:
```python
{
  "process_number": "4000312-69.2025.8.26.0441",
  "client_name": "cogna",
  "status": "pending",
  "portal_metadata": {"solicitacao_id": "..."}
}
```
4. Atualiza solicitação para `em_execucao`

---

### Passo 3: RPA Processa Tasks

**RPA existente deve:**

```python
# 1. Buscar tasks pendentes
tasks = db.tasks.find({"status": "pending"})

for task in tasks:
    # 2. Atualizar status
    db.tasks.update_one(
        {"_id": task["_id"]},
        {"$set": {"status": "processing"}}
    )

    # 3. Executar automação
    client_name = task["client_name"]  # cogna, agibank, etc
    process_number = task["process_number"]

    # Buscar documentos no portal do cliente
    documents = scrape_documents(client_name, process_number)

    # 4. Upload para Azure Storage
    azure_path = upload_to_azure(documents, client_name, process_number)

    # 5. Marcar como completed
    db.tasks.update_one(
        {"_id": task["_id"]},
        {"$set": {
            "status": "completed",
            "file_path": azure_path,
            "updated_at": datetime.utcnow()
        }}
    )
```

---

### Passo 4: Worker Atualiza Portal

**Worker `TaskStatusMonitor`:**

1. Detecta mudança de status na task
2. Atualiza array `resultados` da solicitação:
```python
{
  "cnj": "4000312-69.2025.8.26.0441",
  "status": "concluido",
  "documentos_encontrados": 5,
  "documentos_urls": ["azure://path/to/doc.pdf"],
  "processado_em": "2025-11-07T10:35:00"
}
```
3. Incrementa contadores
4. Se todos CNJs processados, atualiza status geral

---

### Passo 5: Usuário Faz Download

1. Acessa `/solicitacao/{id}`
2. Vê status "concluído"
3. Clica em "Download"
4. Backend gera SAS URLs
5. Download direto do Azure

---

## 🚀 Setup do Worker

### 1. Instalar Dependências (já feito)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Arquivo `backend/.env` já configurado com MongoDB Atlas.

### 3. Executar Worker

```bash
cd backend
source venv/bin/activate

# Rodar worker
python -m workers.solicitacao_to_task_worker
```

**Saída esperada:**
```
🚀 Starting Portal RPA Workers...
🤖 Starting Solicitacao to Task converter...
👀 Starting Task Status Monitor...
```

### 4. Testar Integração

```bash
# Em outro terminal, criar solicitação
curl -X POST http://localhost:8001/api/solicitacoes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "690dc2b0b87de491cd982e86",
    "servico": "buscar_documentos",
    "cnjs": ["4000312-69.2025.8.26.0441"]
  }'

# Verificar que task foi criada
mongo
> use portal_rpa
> db.tasks.find({"portal_metadata.source": "portal_web"})
```

---

## 🔧 Adaptações Necessárias no RPA

### Mudanças Mínimas

O RPA existente precisa apenas:

1. **Buscar tasks com qualquer client_name:**
```python
# Antes (se só processava agibank)
tasks = db.tasks.find({"client_name": "agibank", "status": "pending"})

# Depois (processar todos)
tasks = db.tasks.find({"status": "pending"})
```

2. **Upload para Azure Storage:**
```python
from workers.azure_storage import AzureStorageHandler

azure = AzureStorageHandler()

# Upload documento
result = azure.upload_file(
    local_file_path="documento.pdf",
    cliente_codigo=task["client_name"],
    cnj=task["process_number"],
    filename="documento.pdf"
)

# Atualizar task com blob path
db.tasks.update_one(
    {"_id": task["_id"]},
    {"$set": {"file_path": result["blob_path"]}}
)
```

### Exemplo Completo de Adaptação

**Arquivo:** `/rpa/src/robos/generic/process_portal_tasks.py`

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Importar RPA existente
from config.azure_storage import AzureBlobStorageHandler

async def process_portal_tasks():
    """Process tasks from Portal Web"""

    # Conectar MongoDB
    client = AsyncIOMotorClient("mongodb+srv://...")
    db = client.portal_rpa

    # Azure Storage
    azure = AzureBlobStorageHandler()

    while True:
        # Buscar tasks pendentes
        tasks = await db.tasks.find({"status": "pending"}).to_list(length=10)

        for task in tasks:
            try:
                # Atualizar para processing
                await db.tasks.update_one(
                    {"_id": task["_id"]},
                    {"$set": {"status": "processing"}}
                )

                # Processar conforme cliente
                client_name = task["client_name"]
                process_number = task["process_number"]

                # Executar scraping (reutilizar código existente)
                if client_name == "agibank":
                    from robos.agibank.scraper import buscar_documentos
                    docs = buscar_documentos(process_number)
                elif client_name == "cogna":
                    from robos.cogna.scraper import buscar_documentos
                    docs = buscar_documentos(process_number)
                # ... outros clientes

                # Upload para Azure
                for doc in docs:
                    azure.upload_file(
                        local_file_path=doc,
                        categoria="documentos",
                        task_id=task["_id"],
                        filename=f"{process_number}_{i}.pdf"
                    )

                # Marcar como completed
                await db.tasks.update_one(
                    {"_id": task["_id"]},
                    {"$set": {
                        "status": "completed",
                        "file_path": f"documentos/{client_name}/{process_number}",
                        "updated_at": datetime.utcnow()
                    }}
                )

            except Exception as e:
                # Marcar como failed
                await db.tasks.update_one(
                    {"_id": task["_id"]},
                    {"$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow()
                    }}
                )

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(process_portal_tasks())
```

---

## 📊 Monitoramento

### Dashboard de Tasks

```python
# Ver estatísticas
async def stats():
    db = db_manager.db

    total = await db.tasks.count_documents({"portal_metadata.source": "portal_web"})
    pending = await db.tasks.count_documents({"status": "pending"})
    processing = await db.tasks.count_documents({"status": "processing"})
    completed = await db.tasks.count_documents({"status": "completed"})
    failed = await db.tasks.count_documents({"status": "failed"})

    print(f"""
    📊 Portal RPA Tasks Statistics
    ================================
    Total:      {total}
    Pending:    {pending}
    Processing: {processing}
    Completed:  {completed}
    Failed:     {failed}
    """)

asyncio.run(stats())
```

---

## ✅ Checklist de Integração

### Portal Web ✅
- [x] API criada
- [x] Eventos publicados
- [x] Worker conversor criado

### Worker Bridge ✅
- [x] Converter solicitacoes → tasks
- [x] Monitorar tasks → atualizar solicitacoes
- [x] Mapeamento de status

### RPA (A Fazer)
- [ ] Adaptar para processar tasks genéricas
- [ ] Upload para Azure Storage
- [ ] Atualizar status das tasks

---

## 🎯 Próximos Passos

### Imediato (Você pode fazer agora)

1. **Iniciar o Worker:**
```bash
cd backend
source venv/bin/activate
python -m workers.solicitacao_to_task_worker
```

2. **Criar uma solicitação no Portal**
3. **Verificar que task foi criada:**
```bash
mongo --eval "db.tasks.find({}).pretty()"
```

### Curto Prazo (Próximos dias)

1. Adaptar RPA existente para processar tasks
2. Configurar Azure Storage no RPA
3. Testar fluxo E2E

---

**Com essa integração, o Portal Web e o RPA trabalharão juntos automaticamente!** 🚀
