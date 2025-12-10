# RPA FluxLaw - Sistema de Orquestração de Tarefas

Sistema de RPA (Robotic Process Automation) para orquestração de tarefas de download de documentos jurídicos de sistemas brasileiros (eLaw COGNA, BCLegal Loft, Lexxy SuperSim), com upload para ADVWin GED e armazenamento em Azure Blob Storage.

## Quick Start com Docker

```powershell
# 1. Clone o repositório
git clone <repo-url>
cd rpa-fluxlaw

# 2. Configure o ambiente
cp .env.docker .env
# Edite .env com suas credenciais

# 3. Inicie tudo com um comando
.\scripts\deploy.ps1 dev

# 4. Acesse
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

> Para documentação completa do Docker, veja [DOCKER.md](DOCKER.md)

## Tecnologias Utilizadas

- **Python 3.9+**
- **FastAPI** - Framework web para a API REST
- **MongoDB** - Banco de dados NoSQL para rastreamento de tarefas
- **Celery** - Sistema de filas para processamento assíncrono
- **Redis** - Broker para o Celery
- **Azure Blob Storage** - Armazenamento em nuvem dos documentos (opcional)
- **Armazenamento Local** - Alternativa ao Azure para desenvolvimento
- **Pandas** - Processamento de planilhas Excel/CSV

## Estrutura do Projeto

```
rpa-fluxlaw/
├── main.py              # API FastAPI com endpoints
├── worker.py            # Celery worker e tarefas assíncronas
├── models.py            # Modelos Pydantic para validação
├── database.py          # Conexão e operações com MongoDB
├── settings.py          # Configurações do projeto
├── cloud_storage.py     # Operações com Azure/Local Storage
├── rpa_logic.py         # Lógica RPA (placeholder)
├── requirements.txt     # Dependências do projeto
├── .env                 # Variáveis de ambiente (não versionado)
├── .env.example         # Exemplo de variáveis de ambiente
├── downloads/           # Pasta de armazenamento local (criada automaticamente)
└── temp_downloads/      # Pasta temporária para downloads RPA
```

## Modelos de Dados

### Task (Coleção: tasks)

```python
{
    "_id": ObjectId,
    "process_number": str,      # Número do processo
    "client_name": str,         # Nome do cliente/robô
    "status": str,              # pending, processing, completed, failed
    "file_path": str | None,    # URL do arquivo no Azure ou caminho local
    "created_at": datetime,     # Data de criação
    "updated_at": datetime      # Data de atualização
}
```

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd rpa-fluxlaw
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure as variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Armazenamento Local (padrão - deixe como true enquanto não tiver Azure configurado)
USE_LOCAL_STORAGE=true
LOCAL_STORAGE_PATH=downloads

# Azure Storage (opcional - configure quando tiver as credenciais)
# AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string

# Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Nota:** Por padrão, o sistema usa armazenamento local na pasta `downloads`. Os arquivos serão salvos automaticamente nesta pasta enquanto o Azure não estiver configurado.

### 5. Instale e inicie o Redis (necessário para o Celery)

**Windows:**
```bash
# Baixe e instale Redis do https://github.com/microsoftarchive/redis/releases
# Ou use Docker:
docker run -d -p 6379:6379 redis:latest
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Mac:**
```bash
brew install redis
brew services start redis
```

## Executando o Projeto

### 1. Inicie a API FastAPI

```bash
python main.py
```

Ou use o Uvicorn diretamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

Documentação interativa: http://localhost:8000/docs

### 2. Inicie o Celery Worker

Em outro terminal:

```bash
celery -A worker worker --loglevel=info --pool=solo
```

Nota: No Windows, use `--pool=solo` ou `--pool=threads`

### 3. Inicie o Celery Beat (Agendador)

Em outro terminal:

```bash
celery -A worker beat --loglevel=info
```

Ou execute worker e beat juntos:

```bash
celery -A worker worker --beat --loglevel=info --pool=solo
```

## Endpoints da API

### POST /tasks/upload/{client_name}

Faz upload de uma planilha Excel/CSV com números de processo.

**Parâmetros:**
- `client_name` (path): Nome do cliente/robô
- `file` (form-data): Arquivo Excel (.xlsx, .xls) ou CSV

**Formato da Planilha:**
A planilha deve conter uma coluna chamada `process_number`:

| process_number |
|----------------|
| 12345-2024     |
| 67890-2024     |
| 13579-2024     |

**Resposta:**
```json
{
    "message": "Tarefas criadas com sucesso",
    "tasks_created": 3,
    "client_name": "cliente1"
}
```

### GET /tasks/{task_id}

Retorna os detalhes de uma tarefa específica.

**Resposta:**
```json
{
    "id": "65abc123...",
    "process_number": "12345-2024",
    "client_name": "cliente1",
    "status": "completed",
    "file_path": "https://storage.azure.com/...",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:35:00"
}
```

### GET /tasks/status/{process_number}

Busca uma tarefa pelo número do processo.

**Resposta:**
```json
{
    "process_number": "12345-2024",
    "status": "completed",
    "file_path": "https://storage.azure.com/...",
    "updated_at": "2024-01-15T10:35:00"
}
```

### GET /tasks/

Lista todas as tarefas com filtros opcionais.

**Parâmetros de Query:**
- `status_filter` (opcional): pending, processing, completed, failed
- `limit` (opcional): Número máximo de resultados (padrão: 100)

**Resposta:**
```json
{
    "count": 3,
    "tasks": [...]
}
```

## Fluxo de Processamento

1. **Upload da Planilha**: O usuário faz upload de uma planilha via API
2. **Criação de Tarefas**: Para cada linha, uma tarefa com status "pending" é criada no MongoDB
3. **Celery Beat**: A cada 10 minutos, verifica tarefas pendentes
4. **Processamento**: Para cada tarefa pendente:
   - Status atualizado para "processing"
   - RPA executa o download do documento
   - Documento é salvo no armazenamento (Azure ou pasta local `downloads/`)
   - Status atualizado para "completed" com o caminho do arquivo
5. **Consulta**: O status pode ser consultado a qualquer momento via API

## Armazenamento de Arquivos

O sistema suporta dois modos de armazenamento:

### Modo Local (Padrão)

Por padrão, o sistema usa armazenamento local, ideal para desenvolvimento e testes:

- Arquivos são salvos na pasta `downloads/`
- Estrutura: `downloads/{client_name}/{process_number}.pdf`
- Não requer configuração adicional
- Ativado quando `USE_LOCAL_STORAGE=true` ou quando Azure não está configurado

### Modo Azure (Produção)

Para usar Azure Blob Storage em produção:

1. Configure a connection string no arquivo `.env`:
```env
USE_LOCAL_STORAGE=false
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

2. O sistema automaticamente:
   - Cria o container "documentos" se não existir
   - Salva arquivos com a estrutura: `client_name/process_number.pdf`
   - Retorna URLs públicas dos arquivos

### Alternando entre Local e Azure

Para alternar do modo local para Azure:
1. Atualize o `.env` com `USE_LOCAL_STORAGE=false`
2. Configure `AZURE_STORAGE_CONNECTION_STRING`
3. Reinicie os serviços (API e Worker)

**Nota:** O sistema detecta automaticamente se o Azure está disponível e usa armazenamento local como fallback em caso de erro.

## Desenvolvimento

### Implementando a Lógica RPA Real

O arquivo `rpa_logic.py` contém uma função placeholder. Para implementar a lógica real:

1. Descomente as dependências do Selenium no `requirements.txt`
2. Implemente a função `download_document_real()` usando Selenium
3. Substitua a chamada no `worker.py`

Exemplo de estrutura:

```python
from selenium import webdriver

def download_document_real(process_number: str, client_name: str):
    driver = webdriver.Chrome()
    try:
        # 1. Navegue para o site
        driver.get("https://sistema.com")

        # 2. Faça login
        # ...

        # 3. Busque pelo processo
        # ...

        # 4. Faça o download
        # ...

        return local_file_path
    finally:
        driver.quit()
```

### Configurando o Agendamento

O Celery Beat está configurado para executar a cada 10 minutos. Para alterar:

Em `settings.py`:
```python
BEAT_SCHEDULE_MINUTES: int = 5  # Executa a cada 5 minutos
```

### Adicionando Novas Tarefas Celery

No `worker.py`:

```python
@celery_app.task(name='worker.minha_tarefa')
def minha_tarefa():
    # Sua lógica aqui
    pass
```

## Monitoramento

### Flower - Monitoramento do Celery

Instale o Flower:
```bash
pip install flower
```

Execute:
```bash
celery -A worker flower
```

Acesse: http://localhost:5555

### Logs

Os logs são exibidos no console dos processos (API, Worker, Beat).

Para salvar em arquivo, configure em `logging.basicConfig()`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## Tratamento de Erros

- Se uma tarefa falhar, o status é atualizado para "failed"
- O Celery tenta reprocessar até 3 vezes com intervalo de 60 segundos
- Erros são logados com detalhes

## Estrutura de Armazenamento de Arquivos

### Armazenamento Local

```
downloads/
├── cliente1/
│   ├── 12345-2024.pdf
│   └── 67890-2024.pdf
└── cliente2/
    └── 13579-2024.pdf
```

### Azure Blob Storage (quando configurado)

```
Container: documentos/
├── cliente1/
│   ├── 12345-2024.pdf
│   └── 67890-2024.pdf
└── cliente2/
    └── 13579-2024.pdf
```

### Obtendo a Connection String do Azure

1. Acesse o Azure Portal
2. Vá para sua Storage Account
3. Em "Access keys", copie a "Connection string"

## MongoDB

A string de conexão já está configurada no `settings.py`:

```python
MONGODB_URL = "mongodb+srv://pedro_db_user:0fOGUSiodZIlWpvo@lfa-db.wpr5usp.mongodb.net/?retryWrites=true&w=majority&appName=lfa-db"
```

**Database:** projeto_fluxlaw
**Collection:** tasks

## Testes

Para testar a API, você pode usar:

### cURL

```bash
# Upload de planilha
curl -X POST "http://localhost:8000/tasks/upload/cliente1" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@planilha.xlsx"

# Consultar tarefa
curl -X GET "http://localhost:8000/tasks/{task_id}"

# Consultar por processo
curl -X GET "http://localhost:8000/tasks/status/12345-2024"
```

### Python

```python
import requests

# Upload
files = {'file': open('planilha.xlsx', 'rb')}
response = requests.post(
    'http://localhost:8000/tasks/upload/cliente1',
    files=files
)
print(response.json())

# Consultar
response = requests.get('http://localhost:8000/tasks/status/12345-2024')
print(response.json())
```

## Problemas Comuns

### Redis não conecta

Verifique se o Redis está rodando:
```bash
redis-cli ping
# Deve retornar: PONG
```

### MongoDB não conecta

Verifique a string de conexão e se seu IP está na whitelist do MongoDB Atlas.

### Azure upload falha

Verifique se a connection string do Azure está correta no `.env`.

### Celery não processa tarefas

Verifique se o worker está rodando e se o Redis está acessível.

## Segurança

- Nunca versione o arquivo `.env`
- Use variáveis de ambiente para credenciais
- Configure CORS adequadamente em produção
- Use HTTPS em produção
- Implemente autenticação na API (JWT, OAuth2)

## Deploy

### Docker (Recomendado)

O projeto inclui configuração Docker completa. Veja [DOCKER.md](DOCKER.md) para instruções detalhadas.

```powershell
# Desenvolvimento
.\scripts\deploy.ps1 dev

# Produção
.\scripts\deploy.ps1 prod
```

### Estrutura Docker

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│    API      │   Worker    │    Beat     │   Redis     │
│  (FastAPI)  │  (Celery)   │  (Scheduler)│  (Broker)   │
│  :8000      │  +Chrome    │             │  :6379      │
└─────────────┴─────────────┴─────────────┴─────────────┘
                    │
         ┌──────────┴──────────┐
         │   MongoDB Atlas     │
         └─────────────────────┘
```

### Cloud Deploy (Railway / Render / AWS)

1. Configure as variáveis de ambiente
2. Use as imagens Docker do projeto
3. Configure os serviços necessários (Redis, MongoDB)

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto é privado e confidencial.

## Contato

Para dúvidas ou suporte, entre em contato com a equipe de desenvolvimento.
