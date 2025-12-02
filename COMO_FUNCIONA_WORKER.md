# 🤖 Como Funciona o Worker - Portal → RPA

## ✅ O Worker JÁ FAZ ISSO!

O arquivo `backend/workers/solicitacao_to_task_worker.py` **já cria uma task para cada CNJ** automaticamente!

---

## 📋 Exemplo Prático

### Solicitação com 3 CNJs

Quando você cria uma solicitação com 3 CNJs:

```json
{
  "cliente_id": "690dc2b0b87de491cd982e86",
  "servico": "buscar_documentos",
  "cnjs": [
    "0001234-56.2024.8.00.0000",
    "0005678-90.2023.8.26.0200",
    "4000312-69.2025.8.26.0441"
  ]
}
```

### O Worker Cria 3 Tasks Separadas

**Task 1:**
```json
{
  "process_number": "0001234-56.2024.8.00.0000",
  "client_name": "cogna",
  "status": "pending",
  "portal_metadata": {
    "solicitacao_id": "690dc9d4538b6f438726e053"
  }
}
```

**Task 2:**
```json
{
  "process_number": "0005678-90.2023.8.26.0200",
  "client_name": "cogna",
  "status": "pending",
  "portal_metadata": {
    "solicitacao_id": "690dc9d4538b6f438726e053"
  }
}
```

**Task 3:**
```json
{
  "process_number": "4000312-69.2025.8.26.0441",
  "client_name": "cogna",
  "status": "pending",
  "portal_metadata": {
    "solicitacao_id": "690dc9d4538b6f438726e053"
  }
}
```

---

## 🔄 Código Responsável

### No arquivo `solicitacao_to_task_worker.py` (linha 79-85):

```python
# Create RPA tasks for each CNJ
tasks_created = []
for cnj in solicitacao["cnjs"]:
    task_doc = await self._create_rpa_task(
        cnj=cnj,
        client_name=cliente["codigo"],
        solicitacao_id=solicitacao_id
    )
    if task_doc:
        tasks_created.append(task_doc["_id"])
```

**Isso cria uma task separada para CADA CNJ!** ✅

---

## 📊 Rastreamento

### A solicitação guarda os IDs das tasks criadas:

```json
{
  "_id": "690dc9d4538b6f438726e053",
  "cnjs": [
    "0001234-56.2024.8.00.0000",
    "0005678-90.2023.8.26.0200",
    "4000312-69.2025.8.26.0441"
  ],
  "rpa_task_ids": [
    "690dcxxx...",  // Task do CNJ 1
    "690dcyyy...",  // Task do CNJ 2
    "690dczzz..."   // Task do CNJ 3
  ],
  "total_cnjs": 3,
  "cnjs_processados": 0,
  "cnjs_sucesso": 0,
  "cnjs_erro": 0,
  "resultados": []
}
```

---

## 🔍 Monitoramento Individual

### O Worker monitora CADA task separadamente:

Quando a **Task 1** é processada pelo RPA:
```python
# RPA atualiza task
db.tasks.update_one(
    {"_id": "690dcxxx..."},
    {"$set": {"status": "completed"}}
)
```

**Worker detecta e atualiza solicitação:**
```python
# Adiciona resultado individual
solicitacao.resultados.append({
    "cnj": "0001234-56.2024.8.00.0000",
    "status": "concluido",
    "documentos_encontrados": 5,
    "documentos_urls": ["..."]
})

# Incrementa contadores
solicitacao.cnjs_processados += 1
solicitacao.cnjs_sucesso += 1
```

---

## 🎯 Status Individual vs Geral

### Status Individual (por CNJ)

Cada CNJ tem seu próprio status no array `resultados`:

```json
"resultados": [
  {
    "cnj": "0001234-56.2024.8.00.0000",
    "status": "concluido",
    "documentos_encontrados": 5
  },
  {
    "cnj": "0005678-90.2023.8.26.0200",
    "status": "em_execucao",
    "documentos_encontrados": 0
  },
  {
    "cnj": "4000312-69.2025.8.26.0441",
    "status": "pendente",
    "documentos_encontrados": 0
  }
]
```

### Status Geral (da solicitação)

Calculado automaticamente:
- **em_execucao:** Enquanto houver CNJs não processados
- **concluido:** Quando todos CNJs processados e pelo menos 1 sucesso
- **erro:** Quando todos CNJs falharam

---

## 🚀 Como Executar

### Terminal 1: Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8001
```

### Terminal 2: Worker
```bash
cd backend
source venv/bin/activate
python -m workers.solicitacao_to_task_worker
```

### Terminal 3: Frontend
```bash
cd portal-web
npm run dev
```

---

## ✅ Verificar Funcionamento

### 1. Criar Solicitação com 3 CNJs

No Portal: http://localhost:3000/solicitar

```
CNJs:
0001234-56.2024.8.00.0000
0005678-90.2023.8.26.0200
4000312-69.2025.8.26.0441
```

### 2. Worker Cria 3 Tasks

```bash
# Ver tasks criadas
mongo
> use portal_rpa
> db.tasks.find({"portal_metadata.source": "portal_web"}).count()
// Deve retornar: 3
```

### 3. Ver Logs do Worker

```
📋 Processing solicitacao 690dc9d4538b6f438726e053
✅ Created RPA task ... for CNJ 0001234-56.2024.8.00.0000
✅ Created RPA task ... for CNJ 0005678-90.2023.8.26.0200
✅ Created RPA task ... for CNJ 4000312-69.2025.8.26.0441
✅ Created 3 RPA tasks for solicitacao 690dc9d4538b6f438726e053
```

---

## 🎉 RESUMO

**SIM! O worker cria uma task INDIVIDUAL para cada processo/CNJ!**

- ✅ 1 Solicitação → N Tasks
- ✅ Cada task processa 1 CNJ
- ✅ Status individual rastreado
- ✅ Status geral calculado automaticamente
- ✅ Download individual por CNJ disponível

**O sistema está pronto para integração com o RPA existente!** 🚀
