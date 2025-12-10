# 📋 Exemplos Práticos de Uso da API

## 🔧 Configuração Inicial

```bash
# Base URL da API
API_URL="http://localhost:8000"
```

---

## 🧪 Testes com cURL

### 1. Health Check

```bash
curl -X GET "${API_URL}/health"
```

**Resposta esperada:**
```json
{"status": "healthy", "mongodb": "connected"}
```

---

### 2. Upload de Planilha

```bash
# Upload de arquivo Excel
curl -X POST "${API_URL}/tasks/upload/cogna" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@processos.xlsx"

# Upload de arquivo CSV
curl -X POST "${API_URL}/tasks/upload/cogna" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@processos.csv"
```

---

### 3. Buscar Tarefa por ID

```bash
TASK_ID="507f1f77bcf86cd799439011"
curl -X GET "${API_URL}/tasks/${TASK_ID}"
```

---

### 4. Buscar Status por Número do Processo

```bash
PROCESS_NUMBER="0569584-89.2017.8.05.0001"
curl -X GET "${API_URL}/tasks/status/${PROCESS_NUMBER}"
```

---

### 5. Listar Tarefas

```bash
# Todas as tarefas
curl -X GET "${API_URL}/tasks/"

# Apenas tarefas pendentes
curl -X GET "${API_URL}/tasks/?status_filter=pending"

# Apenas tarefas concluídas (primeiras 50)
curl -X GET "${API_URL}/tasks/?status_filter=completed&limit=50"

# Tarefas com falha
curl -X GET "${API_URL}/tasks/?status_filter=failed"
```

---

### 6. Disparar Processamento Manual

```bash
curl -X POST "${API_URL}/tasks/process-pending"
```

---

## 🐍 Python com Requests

### Script Completo de Upload e Monitoramento

```python
#!/usr/bin/env python3
"""
Script de exemplo para upload e monitoramento de tarefas
"""
import requests
import time
from typing import Optional, Dict, List

API_URL = "http://localhost:8000"

def upload_spreadsheet(file_path: str, client_name: str) -> Dict:
    """Upload de planilha"""
    url = f"{API_URL}/tasks/upload/{client_name}"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
        response.raise_for_status()

    return response.json()

def get_task_by_id(task_id: str) -> Dict:
    """Busca tarefa por ID"""
    url = f"{API_URL}/tasks/{task_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_task_status(process_number: str) -> Dict:
    """Busca status por número do processo"""
    url = f"{API_URL}/tasks/status/{process_number}"
    response = requests.get(url)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()

def list_tasks(status_filter: Optional[str] = None, limit: int = 100) -> Dict:
    """Lista tarefas com filtros"""
    url = f"{API_URL}/tasks/"
    params = {'limit': limit}

    if status_filter:
        params['status_filter'] = status_filter

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def trigger_processing() -> Dict:
    """Força processamento de tarefas pendentes"""
    url = f"{API_URL}/tasks/process-pending"
    response = requests.post(url)
    response.raise_for_status()
    return response.json()

def monitor_task(
    process_number: str,
    check_interval: int = 10,
    max_attempts: int = 60
) -> Optional[Dict]:
    """
    Monitora uma tarefa até conclusão ou timeout

    Args:
        process_number: Número do processo
        check_interval: Intervalo entre verificações (segundos)
        max_attempts: Número máximo de tentativas

    Returns:
        Dict com dados da tarefa ou None em caso de timeout
    """
    print(f"🔍 Monitorando processo: {process_number}")

    for attempt in range(1, max_attempts + 1):
        task = get_task_status(process_number)

        if not task:
            print(f"❌ Tarefa não encontrada")
            return None

        status = task['status']
        print(f"  [{attempt}/{max_attempts}] Status: {status}", end='')

        if status == 'pending':
            print(" ⏳")
        elif status == 'processing':
            print(" 🔄")
        elif status == 'completed':
            print(" ✅")
            print(f"\n🎉 Processo concluído!")
            print(f"📁 {task['total_documents']} documento(s) baixado(s)")
            return task
        elif status == 'failed':
            print(" ❌")
            print(f"\n⚠️  Processo falhou!")
            return task

        time.sleep(check_interval)

    print(f"\n⏰ Timeout após {max_attempts * check_interval}s")
    return None

def download_documents(task: Dict, output_dir: str = "./downloads"):
    """
    Baixa todos os documentos de uma tarefa concluída

    Args:
        task: Dados da tarefa
        output_dir: Diretório de saída
    """
    import os
    from urllib.parse import urlparse

    if task['status'] != 'completed':
        print("⚠️  Tarefa não está concluída")
        return

    os.makedirs(output_dir, exist_ok=True)

    documents = task.get('documents', [])
    print(f"\n📥 Baixando {len(documents)} documento(s)...")

    for idx, doc in enumerate(documents, start=1):
        url = doc['blob_url']
        filename = doc['nome_arquivo_final']
        filepath = os.path.join(output_dir, filename)

        print(f"  [{idx}/{len(documents)}] {filename}...", end=' ')

        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print("✅")
        except Exception as e:
            print(f"❌ Erro: {e}")

    print(f"\n✅ Downloads concluídos em: {output_dir}")

# Exemplo de uso completo
if __name__ == "__main__":
    print("=" * 70)
    print("RPA FLUXLAW - EXEMPLO DE INTEGRAÇÃO")
    print("=" * 70)

    # 1. Upload de planilha
    print("\n📤 1. Upload de planilha...")
    try:
        result = upload_spreadsheet("processos.xlsx", "cogna")
        print(f"✅ {result['tasks_created']} tarefas criadas")
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        exit(1)

    # 2. Força processamento (opcional para testes)
    print("\n🚀 2. Disparando processamento...")
    try:
        trigger_result = trigger_processing()
        print(f"✅ Processamento disparado")
    except Exception as e:
        print(f"⚠️  Erro ao disparar: {e}")

    # 3. Lista tarefas pendentes
    print("\n📋 3. Listando tarefas pendentes...")
    try:
        pending = list_tasks(status_filter='pending', limit=10)
        print(f"✅ {pending['count']} tarefa(s) pendente(s)")
    except Exception as e:
        print(f"❌ Erro ao listar: {e}")

    # 4. Monitora um processo específico
    print("\n🔍 4. Monitorando processo...")
    process_number = "0569584-89.2017.8.05.0001"
    task = monitor_task(process_number, check_interval=5, max_attempts=60)

    # 5. Baixa documentos se concluído
    if task and task['status'] == 'completed':
        print("\n📥 5. Baixando documentos...")
        download_documents(task, output_dir="./documentos_baixados")

        # Mostra lista de documentos
        print("\n📄 Documentos baixados:")
        for doc in task['documents']:
            print(f"  - {doc['tipo_documento']}: {doc['nome_arquivo_final']}")

    print("\n" + "=" * 70)
    print("✅ Processo concluído!")
    print("=" * 70)
```

### Salvar em arquivo

```bash
# Salve o script acima como: example_integration.py
# Execute:
python example_integration.py
```

---

## 🌐 JavaScript/Node.js

### Exemplo com Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_URL = 'http://localhost:8000';

// Upload de planilha
async function uploadSpreadsheet(filePath, clientName) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  const response = await axios.post(
    `${API_URL}/tasks/upload/${clientName}`,
    formData,
    { headers: formData.getHeaders() }
  );

  return response.data;
}

// Buscar tarefa
async function getTask(taskId) {
  const response = await axios.get(`${API_URL}/tasks/${taskId}`);
  return response.data;
}

// Buscar status
async function getTaskStatus(processNumber) {
  try {
    const response = await axios.get(`${API_URL}/tasks/status/${processNumber}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

// Listar tarefas
async function listTasks(statusFilter = null, limit = 100) {
  const params = { limit };
  if (statusFilter) params.status_filter = statusFilter;

  const response = await axios.get(`${API_URL}/tasks/`, { params });
  return response.data;
}

// Monitorar tarefa
async function monitorTask(processNumber, checkInterval = 10, maxAttempts = 60) {
  console.log(`🔍 Monitorando processo: ${processNumber}`);

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const task = await getTaskStatus(processNumber);

    if (!task) {
      console.log('❌ Tarefa não encontrada');
      return null;
    }

    const status = task.status;
    console.log(`  [${attempt}/${maxAttempts}] Status: ${status}`);

    if (status === 'completed') {
      console.log(`\n🎉 Processo concluído!`);
      console.log(`📁 ${task.total_documents} documento(s) baixado(s)`);
      return task;
    } else if (status === 'failed') {
      console.log(`\n⚠️  Processo falhou!`);
      return task;
    }

    await new Promise(resolve => setTimeout(resolve, checkInterval * 1000));
  }

  console.log(`\n⏰ Timeout após ${maxAttempts * checkInterval}s`);
  return null;
}

// Exemplo de uso
(async () => {
  try {
    console.log('=' .repeat(70));
    console.log('RPA FLUXLAW - EXEMPLO DE INTEGRAÇÃO');
    console.log('=' .repeat(70));

    // 1. Upload
    console.log('\n📤 1. Upload de planilha...');
    const uploadResult = await uploadSpreadsheet('processos.xlsx', 'cogna');
    console.log(`✅ ${uploadResult.tasks_created} tarefas criadas`);

    // 2. Listar pendentes
    console.log('\n📋 2. Listando tarefas pendentes...');
    const pending = await listTasks('pending', 10);
    console.log(`✅ ${pending.count} tarefa(s) pendente(s)`);

    // 3. Monitorar processo
    console.log('\n🔍 3. Monitorando processo...');
    const task = await monitorTask('0569584-89.2017.8.05.0001', 5, 60);

    // 4. Mostrar documentos
    if (task && task.status === 'completed') {
      console.log('\n📄 Documentos baixados:');
      task.documents.forEach(doc => {
        console.log(`  - ${doc.tipo_documento}: ${doc.nome_arquivo_final}`);
        console.log(`    URL: ${doc.blob_url}`);
      });
    }

    console.log('\n' + '='.repeat(70));
    console.log('✅ Processo concluído!');
    console.log('='.repeat(70));

  } catch (error) {
    console.error('❌ Erro:', error.message);
    process.exit(1);
  }
})();
```

---

## ⚛️ React Hooks

### Hook Customizado para Monitoramento

```javascript
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export function useTaskMonitor(processNumber, interval = 10000) {
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTask = useCallback(async () => {
    try {
      setError(null);
      const response = await axios.get(
        `${API_URL}/tasks/status/${processNumber}`
      );
      setTask(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Tarefa não encontrada');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [processNumber]);

  useEffect(() => {
    fetchTask();

    // Polling apenas se não estiver concluído ou falhou
    if (task && !['completed', 'failed'].includes(task.status)) {
      const timer = setInterval(fetchTask, interval);
      return () => clearInterval(timer);
    }
  }, [fetchTask, task, interval]);

  return { task, loading, error, refetch: fetchTask };
}

// Componente de exemplo
function TaskMonitor({ processNumber }) {
  const { task, loading, error } = useTaskMonitor(processNumber, 5000);

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!task) return <div>Tarefa não encontrada</div>;

  return (
    <div className="task-monitor">
      <h2>Processo: {task.process_number}</h2>

      <div className="status">
        Status: <strong className={`status-${task.status}`}>
          {task.status}
        </strong>
      </div>

      {task.total_documents > 0 && (
        <div className="documents">
          <h3>Documentos ({task.total_documents})</h3>
          <ul>
            {task.documents?.map((doc, idx) => (
              <li key={idx}>
                <a href={doc.blob_url} target="_blank" rel="noopener noreferrer">
                  📄 {doc.tipo_documento} - {doc.nome_arquivo_final}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default TaskMonitor;
```

---

## 🔥 Postman Collection

Importe esta coleção no Postman:

```json
{
  "info": {
    "name": "RPA FluxLaw API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "client_name",
      "value": "cogna"
    },
    {
      "key": "process_number",
      "value": "0569584-89.2017.8.05.0001"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Upload Spreadsheet",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": "/path/to/processos.xlsx"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/tasks/upload/{{client_name}}",
          "host": ["{{base_url}}"],
          "path": ["tasks", "upload", "{{client_name}}"]
        }
      }
    },
    {
      "name": "Get Task Status",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/tasks/status/{{process_number}}",
          "host": ["{{base_url}}"],
          "path": ["tasks", "status", "{{process_number}}"]
        }
      }
    },
    {
      "name": "List Pending Tasks",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/tasks/?status_filter=pending&limit=100",
          "host": ["{{base_url}}"],
          "path": ["tasks"],
          "query": [
            { "key": "status_filter", "value": "pending" },
            { "key": "limit", "value": "100" }
          ]
        }
      }
    },
    {
      "name": "Trigger Processing",
      "request": {
        "method": "POST",
        "header": [],
        "url": {
          "raw": "{{base_url}}/tasks/process-pending",
          "host": ["{{base_url}}"],
          "path": ["tasks", "process-pending"]
        }
      }
    }
  ]
}
```

---

## 🧪 Testes Automatizados (Pytest)

```python
import pytest
import requests
from time import sleep

API_URL = "http://localhost:8000"

@pytest.fixture
def api_client():
    """Fixture para cliente da API"""
    return requests.Session()

def test_health_check(api_client):
    """Testa o health check"""
    response = api_client.get(f"{API_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_spreadsheet(api_client):
    """Testa upload de planilha"""
    with open("processos_teste.xlsx", "rb") as f:
        files = {"file": f}
        response = api_client.post(
            f"{API_URL}/tasks/upload/cogna",
            files=files
        )

    assert response.status_code == 201
    data = response.json()
    assert "tasks_created" in data
    assert data["tasks_created"] > 0

def test_list_tasks(api_client):
    """Testa listagem de tarefas"""
    response = api_client.get(f"{API_URL}/tasks/")
    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert "tasks" in data

def test_get_task_status(api_client):
    """Testa busca de status"""
    process_number = "0569584-89.2017.8.05.0001"
    response = api_client.get(f"{API_URL}/tasks/status/{process_number}")

    # Pode retornar 404 se não existir
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed", "failed"]

@pytest.mark.integration
def test_full_workflow(api_client):
    """Teste de integração completo"""
    # 1. Upload
    with open("processos_teste.xlsx", "rb") as f:
        files = {"file": f}
        response = api_client.post(
            f"{API_URL}/tasks/upload/cogna",
            files=files
        )
    assert response.status_code == 201

    # 2. Dispara processamento
    response = api_client.post(f"{API_URL}/tasks/process-pending")
    assert response.status_code == 200

    # 3. Aguarda conclusão (com timeout)
    process_number = "0569584-89.2017.8.05.0001"
    max_attempts = 60

    for _ in range(max_attempts):
        response = api_client.get(f"{API_URL}/tasks/status/{process_number}")

        if response.status_code == 200:
            task = response.json()
            if task["status"] in ["completed", "failed"]:
                break

        sleep(10)

    # 4. Verifica resultado
    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "completed"
    assert task["total_documents"] > 0
```

---

## 📊 Exemplos de Resposta

### Tarefa Pendente

```json
{
  "id": "507f1f77bcf86cd799439011",
  "process_number": "0569584-89.2017.8.05.0001",
  "client_name": "cogna",
  "status": "pending",
  "file_path": null,
  "total_documents": null,
  "documents": null,
  "created_at": "2025-01-06T10:00:00",
  "updated_at": "2025-01-06T10:00:00"
}
```

### Tarefa Concluída

```json
{
  "id": "507f1f77bcf86cd799439011",
  "process_number": "0569584-89.2017.8.05.0001",
  "client_name": "cogna",
  "status": "completed",
  "file_path": "https://storage.blob.core.windows.net/rpa-documents/cogna/0569584-89.2017.8.05.0001/056958489201780050001_documentos_01.pdf",
  "total_documents": 9,
  "documents": [
    {
      "numero_linha": 1,
      "nome_arquivo_original": "COGNA - Check list ALINE CRISTINE GONCALVES SOUZA.pdf",
      "tipo_documento": "documentos",
      "nome_arquivo_final": "056958489201780050001_documentos_01.pdf",
      "blob_url": "https://storage.blob.core.windows.net/rpa-documents/cogna/0569584-89.2017.8.05.0001/056958489201780050001_documentos_01.pdf"
    },
    {
      "numero_linha": 2,
      "nome_arquivo_original": "0569584-89.2017.8.05.0001-1723572343570-10817-decisao.pdf",
      "tipo_documento": "decisao_intimacao_de_pagamento",
      "nome_arquivo_final": "056958489201780050001_decisao_intimacao_de_pagamento_02.pdf",
      "blob_url": "https://storage.blob.core.windows.net/rpa-documents/cogna/0569584-89.2017.8.05.0001/056958489201780050001_decisao_intimacao_de_pagamento_02.pdf"
    }
  ],
  "created_at": "2025-01-06T10:00:00",
  "updated_at": "2025-01-06T10:05:30"
}
```

---

**🎉 Pronto para usar! Copie e cole os exemplos conforme necessário.**
