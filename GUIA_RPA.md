# 🤖 Guia de Integração RPA - Consumir API do Portal

## Visão Geral

O Portal Web disponibiliza **endpoints REST** para o RPA buscar tarefas e atualizar status. **Não é necessário worker bridge**, o RPA consome a API diretamente.

---

## 📡 Endpoints Disponíveis para o RPA

### 1. GET `/api/rpa/tasks/pending` - Buscar Tarefas Pendentes

**Descrição:** Retorna lista de CNJs pendentes de processamento (1 task por CNJ)

**Request:**
```bash
GET http://localhost:8001/api/rpa/tasks/pending
GET http://localhost:8001/api/rpa/tasks/pending?client_name=agibank&limit=10
```

**Response:**
```json
[
  {
    "id": "690dc9d4538b6f438726e053_0001234-56.2024.8.00.0000",
    "process_number": "0001234-56.2024.8.00.0000",
    "client_name": "agibank",
    "status": "pending",
    "solicitacao_id": "690dc9d4538b6f438726e053",
    "created_at": "2025-11-07T10:28:36.738000"
  },
  {
    "id": "690dc9d4538b6f438726e053_0005678-90.2023.8.26.0200",
    "process_number": "0005678-90.2023.8.26.0200",
    "client_name": "agibank",
    "status": "pending",
    "solicitacao_id": "690dc9d4538b6f438726e053",
    "created_at": "2025-11-07T10:28:36.738000"
  }
]
```

**Parâmetros:**
- `client_name` (opcional): Filtrar por cliente específico
- `limit` (opcional): Máximo de tasks (padrão: 50)

---

### 2. POST `/api/rpa/tasks/{solicitacao_id}/{cnj}/start` - Iniciar Processamento

**Descrição:** Marca que o RPA começou a processar um CNJ

**Request:**
```bash
POST http://localhost:8001/api/rpa/tasks/690dc9d4538b6f438726e053/0001234-56.2024.8.00.0000/start
```

**Response:**
```json
{
  "success": true,
  "solicitacao_id": "690dc9d4538b6f438726e053",
  "cnj": "0001234-56.2024.8.00.0000",
  "message": "Task marked as processing"
}
```

---

### 3. PUT `/api/rpa/tasks/{solicitacao_id}/{cnj}` - Atualizar Status

**Descrição:** Atualizar resultado do processamento de um CNJ

**Request:**
```bash
PUT http://localhost:8001/api/rpa/tasks/690dc9d4538b6f438726e053/0001234-56.2024.8.00.0000
Content-Type: application/json

{
  "status": "completed",
  "documentos_encontrados": 5,
  "documentos_urls": [
    "documentos/agibank/0001234_56_2024_8_00_0000/peticao.pdf",
    "documentos/agibank/0001234_56_2024_8_00_0000/contrato.pdf"
  ]
}
```

**Status possíveis:**
- `processing` - Em processamento
- `completed` - Concluído com sucesso
- `failed` - Erro no processamento

**Response:**
```json
{
  "success": true,
  "solicitacao_id": "690dc9d4538b6f438726e053",
  "cnj": "0001234-56.2024.8.00.0000",
  "status": "completed",
  "message": "Task status updated successfully"
}
```

---

### 4. GET `/api/rpa/tasks/stats` - Estatísticas

**Descrição:** Retorna estatísticas gerais

**Request:**
```bash
GET http://localhost:8001/api/rpa/tasks/stats
```

**Response:**
```json
{
  "solicitacoes": {
    "total": 10,
    "pendente": 3,
    "em_execucao": 2,
    "concluido": 4,
    "erro": 1
  },
  "cnjs": {
    "total": 25,
    "processados": 18,
    "sucesso": 15,
    "erro": 3,
    "pendentes": 7
  }
}
```

---

## 🔄 Fluxo de Integração

### Passo 1: RPA Busca Tarefas Pendentes

```python
import requests

API_URL = "http://localhost:8001/api/rpa"

# Buscar tasks pendentes
response = requests.get(f"{API_URL}/tasks/pending?client_name=agibank&limit=10")
tasks = response.json()

print(f"📋 {len(tasks)} tarefas pendentes")
```

### Passo 2: Para Cada Task

```python
for task in tasks:
    solicitacao_id = task["solicitacao_id"]
    cnj = task["process_number"]
    client_name = task["client_name"]

    # Marcar como iniciado
    requests.post(f"{API_URL}/tasks/{solicitacao_id}/{cnj}/start")

    try:
        # Processar (buscar documentos, etc)
        documentos = buscar_documentos_no_portal(client_name, cnj)

        # Upload para Azure
        azure_urls = upload_to_azure(documentos, client_name, cnj)

        # Atualizar como concluído
        requests.put(
            f"{API_URL}/tasks/{solicitacao_id}/{cnj}",
            json={
                "status": "completed",
                "documentos_encontrados": len(documentos),
                "documentos_urls": azure_urls
            }
        )

        print(f"✅ CNJ {cnj} processado com sucesso!")

    except Exception as e:
        # Atualizar como erro
        requests.put(
            f"{API_URL}/tasks/{solicitacao_id}/{cnj}",
            json={
                "status": "failed",
                "erro": str(e)
            }
        )

        print(f"❌ Erro ao processar CNJ {cnj}: {e}")
```

---

## 🎯 Exemplo Completo de Worker RPA

```python
"""
RPA Worker - Processa tasks do Portal Web
Arquivo: /rpa/src/workers/portal_web_worker.py
"""
import requests
import time
from datetime import datetime


class PortalWebWorker:
    """Worker que consome tasks do Portal Web"""

    def __init__(self, api_url="http://localhost:8001/api/rpa"):
        self.api_url = api_url

    def get_pending_tasks(self, client_name=None, limit=10):
        """Busca tasks pendentes"""
        params = {"limit": limit}
        if client_name:
            params["client_name"] = client_name

        response = requests.get(f"{self.api_url}/tasks/pending", params=params)
        response.raise_for_status()
        return response.json()

    def mark_task_started(self, solicitacao_id, cnj):
        """Marca task como iniciada"""
        response = requests.post(
            f"{self.api_url}/tasks/{solicitacao_id}/{cnj}/start"
        )
        response.raise_for_status()
        return response.json()

    def update_task_status(self, solicitacao_id, cnj, status, **kwargs):
        """Atualiza status da task"""
        data = {"status": status, **kwargs}

        response = requests.put(
            f"{self.api_url}/tasks/{solicitacao_id}/{cnj}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    def process_task(self, task):
        """Processa uma task individual"""
        solicitacao_id = task["solicitacao_id"]
        cnj = task["process_number"]
        client_name = task["client_name"]

        print(f"🔄 Processando {cnj} ({client_name})...")

        # Marcar como iniciado
        self.mark_task_started(solicitacao_id, cnj)

        try:
            # ==== AQUI VOCÊ COLOCA SEU CÓDIGO RPA EXISTENTE ====

            # Exemplo (adapte para seu RPA)
            if client_name == "agibank":
                from robos.agibank.scraper import buscar_documentos
                documentos = buscar_documentos(cnj)
            elif client_name == "cogna":
                from robos.cogna.scraper import buscar_documentos
                documentos = buscar_documentos(cnj)
            # ... outros clientes

            # Upload para Azure (código existente)
            from config.azure_storage import AzureBlobStorageHandler
            azure = AzureBlobStorageHandler()

            azure_urls = []
            for doc in documentos:
                result = azure.upload_file(
                    local_file_path=doc,
                    cliente_codigo=client_name,
                    cnj=cnj,
                    filename=doc.name
                )
                if result["success"]:
                    azure_urls.append(result["blob_path"])

            # ====================================================

            # Marcar como concluído
            self.update_task_status(
                solicitacao_id=solicitacao_id,
                cnj=cnj,
                status="completed",
                documentos_encontrados=len(documentos),
                documentos_urls=azure_urls
            )

            print(f"✅ {cnj} concluído! {len(documentos)} documentos encontrados")
            return True

        except Exception as e:
            # Marcar como erro
            self.update_task_status(
                solicitacao_id=solicitacao_id,
                cnj=cnj,
                status="failed",
                erro=str(e)
            )

            print(f"❌ Erro ao processar {cnj}: {e}")
            return False

    def run(self, client_name=None, poll_interval=10):
        """Loop principal do worker"""
        print(f"🤖 Worker RPA iniciado! Aguardando tasks...")

        while True:
            try:
                # Buscar tasks pendentes
                tasks = self.get_pending_tasks(client_name=client_name, limit=5)

                if tasks:
                    print(f"📋 {len(tasks)} tasks encontradas")

                    for task in tasks:
                        self.process_task(task)

                else:
                    print("⏳ Nenhuma task pendente...")

            except Exception as e:
                print(f"❌ Erro no worker: {e}")

            # Aguardar antes de próxima verificação
            time.sleep(poll_interval)


if __name__ == "__main__":
    # Iniciar worker
    worker = PortalWebWorker(api_url="http://localhost:8001/api/rpa")

    # Processar apenas tasks do agibank (opcional)
    # worker.run(client_name="agibank")

    # Ou processar de todos os clientes
    worker.run()
```

---

## 🚀 Como Usar

### 1. Criar Solicitação no Portal

Via frontend (http://localhost:3000) ou API:

```bash
curl -X POST http://localhost:8001/api/solicitacoes \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "690dc2b0b87de491cd982e86",
    "servico": "buscar_documentos",
    "cnjs": [
      "0001234-56.2024.8.00.0000",
      "0005678-90.2023.8.26.0200"
    ]
  }'
```

### 2. RPA Busca Tasks

```bash
curl http://localhost:8001/api/rpa/tasks/pending
```

**Retorna 2 tasks (1 por CNJ):**
```json
[
  {
    "id": "..._0001234-56.2024.8.00.0000",
    "process_number": "0001234-56.2024.8.00.0000",
    "client_name": "cogna",
    "solicitacao_id": "..."
  },
  {
    "id": "..._0005678-90.2023.8.26.0200",
    "process_number": "0005678-90.2023.8.26.0200",
    "client_name": "cogna",
    "solicitacao_id": "..."
  }
]
```

### 3. RPA Processa Cada Task

```bash
# Marcar como iniciado
POST /api/rpa/tasks/{solicitacao_id}/{cnj}/start

# ... processar ...

# Atualizar como concluído
PUT /api/rpa/tasks/{solicitacao_id}/{cnj}
{
  "status": "completed",
  "documentos_encontrados": 5,
  "documentos_urls": ["azure://path/doc.pdf"]
}
```

### 4. Portal Atualiza Automaticamente

O status da solicitação é atualizado quando todos CNJs forem processados!

---

## 📊 Lógica de Atualização

### Status Individual (por CNJ)

Cada CNJ tem resultado independente no array `resultados[]`:

```json
{
  "cnj": "0001234-56.2024.8.00.0000",
  "status": "completed",
  "documentos_encontrados": 5,
  "documentos_urls": ["..."],
  "processado_em": "2025-11-07T11:00:00"
}
```

### Status Geral (da solicitação)

Calculado automaticamente quando todos CNJs processados:

- **Todos falharam?** → `erro`
- **Pelo menos 1 sucesso?** → `concluido`
- **Nenhum documento?** → `documentos_nao_encontrados`

---

## 🔧 Adaptação do RPA Existente

### Mudanças Necessárias (Mínimas)

**Antes (tabela tasks própria):**
```python
tasks = db.tasks.find({"status": "pending"})
```

**Depois (consumir API do Portal):**
```python
import requests

response = requests.get("http://localhost:8001/api/rpa/tasks/pending")
tasks = response.json()
```

**Vantagens:**
- ✅ Não precisa acessar MongoDB diretamente
- ✅ API REST padronizada
- ✅ Autenticação opcional (pode adicionar depois)
- ✅ Versionamento da API
- ✅ Documentação Swagger

---

## 📝 Exemplo de Adaptação

**Arquivo:** `/rpa/src/workers/portal_web_consumer.py`

```python
import requests
import time
from typing import List, Dict


class PortalAPIClient:
    """Cliente para consumir API do Portal Web"""

    def __init__(self, base_url="http://localhost:8001/api/rpa"):
        self.base_url = base_url

    def get_pending_tasks(self, client_name=None) -> List[Dict]:
        """Busca tasks pendentes"""
        params = {}
        if client_name:
            params["client_name"] = client_name

        response = requests.get(f"{self.base_url}/tasks/pending", params=params)
        response.raise_for_status()
        return response.json()

    def start_task(self, solicitacao_id: str, cnj: str):
        """Marca task como iniciada"""
        response = requests.post(
            f"{self.base_url}/tasks/{solicitacao_id}/{cnj}/start"
        )
        response.raise_for_status()

    def complete_task(
        self,
        solicitacao_id: str,
        cnj: str,
        documentos_urls: List[str]
    ):
        """Marca task como concluída"""
        response = requests.put(
            f"{self.base_url}/tasks/{solicitacao_id}/{cnj}",
            json={
                "status": "completed",
                "documentos_encontrados": len(documentos_urls),
                "documentos_urls": documentos_urls
            }
        )
        response.raise_for_status()

    def fail_task(self, solicitacao_id: str, cnj: str, erro: str):
        """Marca task como erro"""
        response = requests.put(
            f"{self.base_url}/tasks/{solicitacao_id}/{cnj}",
            json={"status": "failed", "erro": erro}
        )
        response.raise_for_status()


def main_worker_loop():
    """Loop principal do worker RPA"""
    client = PortalAPIClient()

    print("🤖 RPA Worker iniciado!")

    while True:
        try:
            # 1. Buscar tasks pendentes
            tasks = client.get_pending_tasks()

            if not tasks:
                print("⏳ Sem tasks pendentes...")
                time.sleep(10)
                continue

            print(f"📋 {len(tasks)} tasks encontradas")

            # 2. Processar cada task
            for task in tasks:
                solicitacao_id = task["solicitacao_id"]
                cnj = task["process_number"]
                client_name = task["client_name"]

                print(f"🔄 Processando {cnj} ({client_name})...")

                # Marcar como iniciado
                client.start_task(solicitacao_id, cnj)

                try:
                    # ==== SEU CÓDIGO RPA AQUI ====
                    documentos = processar_cnj(cnj, client_name)
                    azure_urls = upload_documentos(documentos, client_name, cnj)
                    # =============================

                    # Marcar como concluído
                    client.complete_task(solicitacao_id, cnj, azure_urls)
                    print(f"✅ {cnj} concluído!")

                except Exception as e:
                    # Marcar como erro
                    client.fail_task(solicitacao_id, cnj, str(e))
                    print(f"❌ Erro: {e}")

        except Exception as e:
            print(f"❌ Erro no worker: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main_worker_loop()
```

---

## 🧪 Testar Endpoints

### 1. Criar Solicitação de Teste

No Swagger (http://localhost:8001/docs):
1. Login em `/api/auth/login`
2. Authorize com token
3. POST `/api/solicitacoes` com 2 CNJs

### 2. Buscar Tasks Pendentes

```bash
curl http://localhost:8001/api/rpa/tasks/pending
```

Deve retornar 2 tasks!

### 3. Simular RPA Processando

```bash
# Pegar IDs do passo anterior
SOLICITACAO_ID="690dc9d4538b6f438726e053"
CNJ="0001234-56.2024.8.00.0000"

# Iniciar
curl -X POST http://localhost:8001/api/rpa/tasks/$SOLICITACAO_ID/$CNJ/start

# Concluir
curl -X PUT http://localhost:8001/api/rpa/tasks/$SOLICITACAO_ID/$CNJ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "documentos_encontrados": 3,
    "documentos_urls": ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
  }'
```

### 4. Verificar no Portal

Acesse http://localhost:3000/acompanhamento

Você verá a solicitação atualizada! ✅

---

## 📊 Monitoramento

### Ver Estatísticas

```bash
curl http://localhost:8001/api/rpa/tasks/stats
```

### Ver Tasks Específicas do Cliente

```bash
curl "http://localhost:8001/api/rpa/tasks/pending?client_name=agibank"
```

---

## 🎯 Resumo da Integração

**Portal Web fornece:**
- ✅ Endpoint para buscar CNJs pendentes
- ✅ Endpoint para atualizar status
- ✅ Endpoint para estatísticas
- ✅ **1 task individual por CNJ**

**RPA precisa:**
- ✅ Chamar GET `/tasks/pending` periodicamente
- ✅ Processar cada CNJ
- ✅ Chamar PUT `/tasks/{id}/{cnj}` com resultado
- ✅ **Pronto!**

**Sem necessidade de:**
- ❌ Worker intermediário
- ❌ Acessar MongoDB diretamente
- ❌ Sistema de filas complexo

---

## ✅ Vantagens Dessa Abordagem

1. **Simplicidade** - API REST simples
2. **Desacoplamento** - RPA não precisa conhecer estrutura do Portal
3. **Flexibilidade** - Pode adicionar autenticação depois
4. **Rastreabilidade** - Cada CNJ tem ID único
5. **Escalabilidade** - Múltiplos workers RPA podem consumir

---

**Pronto para integração! O RPA só precisa consumir esses 3 endpoints.** 🚀
