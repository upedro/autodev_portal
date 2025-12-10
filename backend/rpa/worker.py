"""
Celery worker para processamento de tarefas RPA
"""
import os
import logging
from celery import Celery
from celery.schedules import crontab

from settings import settings
from models import TaskStatus
from database import MongoDB, TaskRepository
from rpa_logic import download_document, validate_process_number
from cloud_storage import get_azure_storage

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa o Celery
celery_app = Celery(
    'rpa_fluxlaw',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configuração do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Configuração do Celery Beat (agendamento)
celery_app.conf.beat_schedule = {
    'check-pending-tasks-every-10-minutes': {
        'task': 'worker.check_pending_tasks',
        'schedule': settings.BEAT_SCHEDULE_MINUTES * 60.0,  # Converte minutos para segundos
    },
}


@celery_app.task(name='worker.check_pending_tasks', bind=True)
def check_pending_tasks(self):
    """
    Tarefa agendada que busca tarefas pendentes e dispara o processamento.

    Esta tarefa é executada pelo Celery Beat a cada N minutos (configurado em settings).
    Busca todas as tarefas com status='pending' e dispara uma tarefa de processamento
    para cada uma delas.

    Returns:
        Dicionário com informações sobre as tarefas encontradas e disparadas
    """
    try:
        logger.info("Verificando tarefas pendentes...")

        # Conecta ao MongoDB se necessário
        if MongoDB.db is None:
            MongoDB.connect()

        # Busca tarefas pendentes
        pending_tasks = TaskRepository.get_tasks_by_status(TaskStatus.PENDING)

        logger.info(f"Encontradas {len(pending_tasks)} tarefas pendentes")

        # Dispara processamento para cada tarefa
        dispatched = 0
        for task in pending_tasks:
            task_id = task["_id"]
            try:
                # Dispara a tarefa de processamento de forma assíncrona
                process_task.delay(task_id)
                dispatched += 1
                logger.info(f"Tarefa {task_id} disparada para processamento")
            except Exception as e:
                logger.error(f"Erro ao disparar tarefa {task_id}: {e}")

        result = {
            "pending_tasks_found": len(pending_tasks),
            "tasks_dispatched": dispatched
        }

        logger.info(f"Verificação concluída: {result}")
        return result

    except Exception as e:
        logger.error(f"Erro ao verificar tarefas pendentes: {e}")
        raise


@celery_app.task(name='worker.process_task', bind=True, max_retries=3)
def process_task(self, task_id: str):
    """
    Tarefa principal de processamento RPA.

    Esta tarefa executa o fluxo completo de:
    1. Atualizar status para 'processing'
    2. Validar número do processo
    3. Executar lógica RPA (download do documento)
    4. Upload para Azure Blob Storage
    5. Atualizar status para 'completed' com file_path

    Em caso de erro, atualiza o status para 'failed'.

    Args:
        task_id: ID da tarefa a ser processada

    Returns:
        Dicionário com informações sobre o processamento
    """
    try:
        logger.info(f"Iniciando processamento da tarefa {task_id}")

        # Conecta ao MongoDB se necessário
        if MongoDB.db is None:
            MongoDB.connect()

        # Busca a tarefa
        task = TaskRepository.get_task_by_id(task_id)
        if not task:
            logger.error(f"Tarefa {task_id} não encontrada")
            raise Exception(f"Tarefa {task_id} não encontrada")

        process_number = task["process_number"]
        client_name = task["client_name"]

        # 1. Atualiza status para 'processing'
        TaskRepository.update_task_status(task_id, TaskStatus.PROCESSING)
        logger.info(f"Tarefa {task_id} marcada como 'processing'")

        # 2. Valida o número do processo
        if not validate_process_number(process_number):
            raise Exception(f"Número do processo inválido: {process_number}")

        # 3. Executa a lógica RPA (download dos documentos)
        logger.info(f"Executando download para processo {process_number}")
        documentos = download_document(process_number, client_name)

        if not documentos or len(documentos) == 0:
            raise Exception("Erro no download: nenhum documento foi baixado")

        logger.info(f"Download concluído: {len(documentos)} documento(s) baixado(s)")

        # 4. Upload para Azure Blob Storage de todos os documentos
        documentos_upload = []
        try:
            azure_storage = get_azure_storage()

            for idx, doc in enumerate(documentos, start=1):
                local_file_path = doc['caminho_arquivo']
                nome_arquivo_final = doc['nome_arquivo_final']

                # Gera o nome do blob (caminho no Azure)
                blob_name = f"{client_name}/{process_number}/{nome_arquivo_final}"

                logger.info(f"[{idx}/{len(documentos)}] Fazendo upload para Azure: {blob_name}")
                blob_url = azure_storage.upload_file(local_file_path, blob_name)

                if not blob_url:
                    raise Exception(f"Erro no upload para Azure: URL não retornada para {nome_arquivo_final}")

                logger.info(f"[{idx}/{len(documentos)}] Upload concluído: {blob_url}")

                # Adiciona informações do upload aos metadados
                documentos_upload.append({
                    "numero_linha": doc['numero_linha'],
                    "nome_arquivo_original": doc['nome_arquivo'],
                    "tipo_documento": doc['tipo_documento'],
                    "nome_arquivo_final": nome_arquivo_final,
                    "blob_url": blob_url
                })

                # Remove o arquivo local após upload bem-sucedido
                try:
                    os.remove(local_file_path)
                    logger.info(f"Arquivo local removido: {local_file_path}")
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo local: {e}")

        except Exception as e:
            logger.error(f"Erro no upload para Azure: {e}")
            raise

        # 5. Atualiza status para 'completed' com lista de documentos
        TaskRepository.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            file_path=documentos_upload[0]['blob_url'] if len(documentos_upload) > 0 else None,
            documents=documentos_upload  # Nova lista de documentos
        )

        logger.info(f"Tarefa {task_id} concluída com sucesso")
        logger.info(f"Total de documentos enviados: {len(documentos_upload)}")

        return {
            "task_id": task_id,
            "process_number": process_number,
            "client_name": client_name,
            "status": "completed",
            "total_documents": len(documentos_upload),
            "documents": documentos_upload
        }

    except Exception as e:
        logger.error(f"Erro ao processar tarefa {task_id}: {e}")

        # Atualiza status para 'failed'
        try:
            if MongoDB.db is None:
                MongoDB.connect()
            TaskRepository.update_task_status(task_id, TaskStatus.FAILED)
            logger.info(f"Tarefa {task_id} marcada como 'failed'")
        except Exception as update_error:
            logger.error(f"Erro ao atualizar status para failed: {update_error}")

        # Tenta fazer retry (até 3 vezes)
        try:
            raise self.retry(exc=e, countdown=60)  # Aguarda 60 segundos antes de tentar novamente
        except Exception:
            # Se já atingiu o número máximo de retries, não faz mais nada
            logger.error(f"Número máximo de retries atingido para tarefa {task_id}")
            raise


@celery_app.task(name='worker.process_multiple_tasks', bind=True)
def process_multiple_tasks(self, task_ids: list):
    """
    Processa múltiplas tarefas em lote.

    Args:
        task_ids: Lista de IDs de tarefas

    Returns:
        Dicionário com estatísticas do processamento
    """
    results = {
        "total": len(task_ids),
        "processed": 0,
        "failed": 0
    }

    for task_id in task_ids:
        try:
            process_task.delay(task_id)
            results["processed"] += 1
        except Exception as e:
            logger.error(f"Erro ao disparar tarefa {task_id}: {e}")
            results["failed"] += 1

    return results


@celery_app.task(name='worker.cleanup_old_files', bind=True)
def cleanup_old_files(self):
    """
    Tarefa de manutenção para limpar arquivos temporários antigos.

    Esta tarefa pode ser agendada para executar periodicamente
    e limpar arquivos da pasta temp_downloads que não foram removidos.

    Returns:
        Número de arquivos removidos
    """
    try:
        temp_dir = os.path.join(os.getcwd(), "temp_downloads")

        if not os.path.exists(temp_dir):
            logger.info("Diretório temp_downloads não existe")
            return 0

        files_removed = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_removed += 1
                    logger.info(f"Arquivo removido: {file_path}")
            except Exception as e:
                logger.error(f"Erro ao remover arquivo {file_path}: {e}")

        logger.info(f"Limpeza concluída: {files_removed} arquivos removidos")
        return files_removed

    except Exception as e:
        logger.error(f"Erro na limpeza de arquivos: {e}")
        raise


if __name__ == '__main__':
    # Para executar o worker, use o comando:
    # celery -A worker worker --loglevel=info
    #
    # Para executar o beat (agendador), use o comando:
    # celery -A worker beat --loglevel=info
    #
    # Para executar ambos ao mesmo tempo:
    # celery -A worker worker --beat --loglevel=info
    pass
