"""
API FastAPI para orquestração de tarefas RPA
"""
import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, Path, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from models import (
    TaskResponse,
    TaskStatusResponse,
    UploadResponse,
    TaskStatus
)
from database import MongoDB, TaskRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando aplicação...")
    MongoDB.connect()
    logger.info("Aplicação iniciada com sucesso")

    yield

    # Shutdown
    logger.info("Encerrando aplicação...")
    MongoDB.disconnect()
    logger.info("Aplicação encerrada")


# Inicializa a aplicação FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# Configuração de CORS para permitir requisições do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Endpoint raiz para verificar se a API está funcionando"""
    return {
        "message": "RPA FluxLaw API está funcionando",
        "version": settings.API_VERSION
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de health check"""
    try:
        # Tenta acessar o MongoDB
        MongoDB.get_tasks_collection()
        return {
            "status": "healthy",
            "mongodb": "connected"
        }
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post(
    "/tasks/upload/{client_name}",
    response_model=UploadResponse,
    tags=["Tasks"],
    status_code=status.HTTP_201_CREATED
)
async def upload_tasks(
    client_name: str = Path(..., description="Nome do cliente/robô"),
    file: UploadFile = File(..., description="Planilha Excel ou CSV com os números de processo")
):
    """
    Endpoint para upload de planilha com números de processo.

    Este endpoint aceita um arquivo Excel (.xlsx, .xls) ou CSV contendo
    números de processo e cria tarefas pendentes no MongoDB.

    A planilha deve conter uma coluna chamada 'process_number'.

    Args:
        client_name: Nome do cliente/robô que processará as tarefas
        file: Arquivo da planilha (Excel ou CSV)

    Returns:
        Informações sobre o upload e quantidade de tarefas criadas
    """
    try:
        # Valida a extensão do arquivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de arquivo não suportado. Use: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Lê o arquivo
        contents = await file.read()

        # Processa de acordo com a extensão
        if file_extension == '.csv':
            df = pd.read_csv(pd.io.common.BytesIO(contents))
        else:  # .xlsx ou .xls
            df = pd.read_excel(pd.io.common.BytesIO(contents))

        # Verifica se a coluna 'process_number' existe
        if 'process_number' not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A planilha deve conter uma coluna 'process_number'"
            )

        # Remove linhas com process_number vazio
        df = df.dropna(subset=['process_number'])

        # Converte para string e remove espaços
        df['process_number'] = df['process_number'].astype(str).str.strip()

        # Remove duplicatas
        df = df.drop_duplicates(subset=['process_number'])

        # Prepara os dados para inserção
        tasks_data = [
            {
                "process_number": row['process_number'],
                "client_name": client_name
            }
            for _, row in df.iterrows()
        ]

        # Cria as tarefas no MongoDB
        tasks_created = TaskRepository.bulk_create_tasks(tasks_data)

        logger.info(
            f"{tasks_created} tarefas criadas para o cliente {client_name}"
        )

        return UploadResponse(
            message="Tarefas criadas com sucesso",
            tasks_created=tasks_created,
            client_name=client_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"]
)
async def get_task(
    task_id: str = Path(..., description="ID da tarefa")
):
    """
    Busca uma tarefa pelo ID.

    Args:
        task_id: ID da tarefa

    Returns:
        Detalhes completos da tarefa
    """
    task = TaskRepository.get_task_by_id(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa {task_id} não encontrada"
        )

    return TaskResponse(
        id=task["_id"],
        process_number=task["process_number"],
        client_name=task["client_name"],
        status=TaskStatus(task["status"]),
        file_path=task.get("file_path"),
        documents=task.get("documents"),
        total_documents=task.get("total_documents"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@app.get(
    "/tasks/status/{process_number}",
    response_model=TaskStatusResponse,
    tags=["Tasks"]
)
async def get_task_status(
    process_number: str = Path(..., description="Número do processo")
):
    """
    Busca o status de uma tarefa pelo número do processo.

    Args:
        process_number: Número do processo

    Returns:
        Status e informações da tarefa
    """
    task = TaskRepository.get_task_by_process_number(process_number)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com processo {process_number} não encontrada"
        )

    return TaskStatusResponse(
        process_number=task["process_number"],
        status=TaskStatus(task["status"]),
        file_path=task.get("file_path"),
        documents=task.get("documents"),
        total_documents=task.get("total_documents"),
        updated_at=task["updated_at"]
    )


@app.get(
    "/tasks/",
    tags=["Tasks"]
)
async def list_tasks(
    status_filter: Optional[str] = None,
    limit: int = 100
):
    """
    Lista tarefas com filtros opcionais.

    Args:
        status_filter: Filtrar por status (pending, processing, completed, failed)
        limit: Número máximo de tarefas a retornar

    Returns:
        Lista de tarefas
    """
    try:
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter)
                tasks = TaskRepository.get_tasks_by_status(status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status inválido. Use: {', '.join([s.value for s in TaskStatus])}"
                )
        else:
            # Busca todas as tarefas
            collection = MongoDB.get_tasks_collection()
            tasks = list(collection.find().limit(limit))
            for task in tasks:
                task["_id"] = str(task["_id"])

        # Limita o número de resultados
        tasks = tasks[:limit]

        # Converte para o formato de resposta
        response = []
        for task in tasks:
            response.append({
                "id": task["_id"],
                "process_number": task["process_number"],
                "client_name": task["client_name"],
                "status": task["status"],
                "file_path": task.get("file_path"),
                "documents": task.get("documents"),
                "total_documents": task.get("total_documents"),
                "created_at": task["created_at"].isoformat(),
                "updated_at": task["updated_at"].isoformat()
            })

        return {
            "count": len(response),
            "tasks": response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar tarefas: {str(e)}"
        )


@app.post("/tasks/process-pending", tags=["Tasks"])
async def trigger_pending_tasks():
    """
    Força o processamento imediato de todas as tarefas pendentes.

    Útil para testes sem precisar esperar o Celery Beat (10 minutos).

    Returns:
        Informações sobre tarefas disparadas
    """
    try:
        from worker import check_pending_tasks

        logger.info("Disparando processamento manual de tarefas pendentes...")

        # Executa a verificação de tarefas pendentes
        result = check_pending_tasks.delay()

        return {
            "message": "Processamento de tarefas pendentes disparado",
            "task_id": result.id,
            "info": "As tarefas serão processadas pelo worker em alguns segundos"
        }

    except Exception as e:
        logger.error(f"Erro ao disparar processamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao disparar processamento: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
