"""
Celery Worker para integração com o Portal Web.

Este worker processa tasks criadas pelo Portal através do MongoDB compartilhado.
Ele faz polling da collection 'tasks' buscando tasks com 'portal_metadata',
executa o RPA apropriado e atualiza os resultados na 'solicitacao'.

Uso:
    # Iniciar worker
    celery -A portal_worker worker --loglevel=info --pool=solo

    # Iniciar beat (agendador)
    celery -A portal_worker beat --loglevel=info

    # Ou ambos juntos
    celery -A portal_worker worker --beat --loglevel=info --pool=solo
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from celery import Celery
from celery.schedules import crontab
from bson import ObjectId

from settings import settings
from portal_repository import PortalRepository
from rpa_dispatcher import (
    get_rpa_class,
    get_credentials_for_client,
    is_client_supported,
    get_download_method_name
)
from rpa_logic import _criar_driver_local
from cloud_storage import get_azure_storage

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração do Celery
celery_app = Celery(
    'portal_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos (hard limit)
    task_soft_time_limit=25 * 60,  # 25 minutos (soft limit)
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Beat schedule - verifica tasks do portal a cada X minutos
celery_app.conf.beat_schedule = {
    'check-portal-tasks': {
        'task': 'portal_worker.check_portal_tasks',
        'schedule': settings.PORTAL_BEAT_SCHEDULE_MINUTES * 60.0,
    },
}


@celery_app.task(name='portal_worker.check_portal_tasks')
def check_portal_tasks() -> Dict[str, Any]:
    """
    Task agendada que verifica tasks pendentes do Portal.
    Executada pelo Celery Beat a cada X minutos (configurável).

    Returns:
        Dict com estatísticas do processamento
    """
    logger.info("Verificando tasks pendentes do Portal...")

    try:
        PortalRepository.connect()

        # Busca tasks pendentes com metadata do portal
        tasks = PortalRepository.get_pending_tasks_with_portal_metadata(limit=20)

        if not tasks:
            logger.info("Nenhuma task pendente do Portal encontrada")
            return {"tasks_found": 0, "dispatched": 0}

        dispatched = 0
        skipped = 0

        for task in tasks:
            try:
                # Extrai informações da task
                task_id = task["_id"]
                process_number = task["process_number"]
                client_name = task["client_name"]
                portal_metadata = task.get("portal_metadata", {})
                solicitacao_id = portal_metadata.get("solicitacao_id")

                if not solicitacao_id:
                    logger.warning(f"Task {task_id} sem solicitacao_id, pulando...")
                    skipped += 1
                    continue

                # Verifica se o cliente é suportado
                if not is_client_supported(client_name):
                    logger.warning(f"Cliente {client_name} não suportado, pulando task {task_id}")
                    skipped += 1
                    continue

                # Extrai pasta e codigo_pasta da task (dados do ADVWin)
                pasta = task.get("pasta")
                codigo_pasta = task.get("codigo_pasta")

                # Dispara processamento assíncrono
                process_portal_task.delay(
                    task_id=task_id,
                    process_number=process_number,
                    client_name=client_name,
                    solicitacao_id=solicitacao_id,
                    pasta=pasta,
                    codigo_pasta=codigo_pasta
                )
                dispatched += 1

                logger.info(f"Task {task_id} (CNJ: {process_number}) despachada para processamento")

            except Exception as e:
                logger.error(f"Erro ao despachar task: {e}")
                skipped += 1

        result = {
            "tasks_found": len(tasks),
            "dispatched": dispatched,
            "skipped": skipped
        }

        logger.info(f"Verificação concluída: {result}")
        return result

    except Exception as e:
        logger.error(f"Erro ao verificar tasks do Portal: {e}")
        return {"error": str(e)}


@celery_app.task(
    name='portal_worker.process_portal_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_portal_task(
    self,
    task_id: str,
    process_number: str,
    client_name: str,
    solicitacao_id: str,
    pasta: Optional[str] = None,
    codigo_pasta: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processa uma task individual do Portal.

    Fluxo:
    1. Marca task como 'processing'
    2. Atualiza solicitação para 'em_execucao' (se ainda pendente)
    3. Executa RPA apropriado para o cliente
    4. Faz upload dos documentos para Azure/Local
    5. Atualiza task como 'completed'
    6. Adiciona resultado à solicitação
    7. Verifica se solicitação está completa

    Args:
        task_id: ID da task no MongoDB
        process_number: Número do processo (CNJ)
        client_name: Código do cliente (cogna, loft, supersim)
        solicitacao_id: ID da solicitação do Portal
        pasta: Pasta/folder no ADVWin (opcional)
        codigo_pasta: Código da pasta no ADVWin (codigo_comp) (opcional)

    Returns:
        Dict com resultado do processamento
    """
    logger.info(f"Iniciando processamento: Task={task_id}, CNJ={process_number}, Cliente={client_name}")

    driver = None

    try:
        PortalRepository.connect()

        # 1. Marcar task como processing
        PortalRepository.update_task_status(task_id, "processing")
        logger.info(f"Task {task_id} marcada como 'processing'")

        # 2. Atualizar solicitação para em_execucao (operação atômica, só atualiza se pendente)
        PortalRepository.update_solicitacao_to_em_execucao(solicitacao_id)
        logger.info(f"Solicitação {solicitacao_id} atualizada para 'em_execucao'")

        # 3. Obter classe RPA e credenciais
        RpaClass = get_rpa_class(client_name)
        username, password = get_credentials_for_client(client_name)

        if not username or not password:
            raise ValueError(f"Credenciais não configuradas para cliente {client_name}")

        # 4. Criar driver e executar RPA
        driver = _criar_driver_local()
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")

        rpa = RpaClass(
            driver=driver,
            usuario=username,
            senha=password,
            download_path=download_path
        )

        # Login
        logger.info(f"Entrando no sistema para cliente {client_name}...")
        rpa.ENTRAR_NO_SISTEMA()

        logger.info("Fazendo login...")
        if not rpa.LOGIN():
            raise Exception(f"Falha no login para cliente {client_name}")

        # Download de documentos
        logger.info(f"Baixando documentos do processo {process_number}...")
        if pasta:
            logger.info(f"Pasta ADVWin: {pasta}")
        if codigo_pasta:
            logger.info(f"Código pasta ADVWin: {codigo_pasta}")

        download_method = get_download_method_name(client_name)
        documentos = getattr(rpa, download_method)(
            process_number,
            pasta=pasta,
            codigo_pasta=codigo_pasta
        )

        if not documentos:
            documentos = []

        logger.info(f"Download concluído: {len(documentos)} documento(s)")

        # 5. Upload para Azure/Local storage
        storage = get_azure_storage()
        docs_urls = []
        docs_metadata = []

        for doc in documentos:
            try:
                local_path = doc.get('caminho_arquivo')
                nome_final = doc.get('nome_arquivo_final', os.path.basename(local_path))

                if not local_path or not os.path.exists(local_path):
                    logger.warning(f"Arquivo não encontrado: {local_path}")
                    continue

                # Sanitiza o process_number para usar como path
                cnj_safe = process_number.replace(".", "_").replace("-", "_").replace("/", "_")
                blob_name = f"{client_name}/{cnj_safe}/{nome_final}"

                # Upload
                blob_url = storage.upload_file(local_path, blob_name)
                docs_urls.append(blob_url)

                # Metadata do documento (inclui pasta e codigo_pasta se disponíveis)
                doc_metadata = {
                    "numero_linha": doc.get('numero_linha', 0),
                    "nome_arquivo_original": doc.get('nome_arquivo', nome_final),
                    "tipo_documento": doc.get('tipo_documento', 'documento'),
                    "nome_arquivo_final": nome_final,
                    "blob_url": blob_url
                }

                # Adiciona pasta e codigo_pasta do documento ou dos parâmetros da task
                doc_pasta = doc.get('pasta') or pasta
                doc_codigo_pasta = doc.get('codigo_pasta') or codigo_pasta
                if doc_pasta:
                    doc_metadata["pasta"] = doc_pasta
                if doc_codigo_pasta:
                    doc_metadata["codigo_pasta"] = doc_codigo_pasta

                docs_metadata.append(doc_metadata)

                # Remove arquivo local após upload
                try:
                    os.remove(local_path)
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo local {local_path}: {e}")

                logger.info(f"Upload concluído: {blob_name}")

            except Exception as e:
                logger.error(f"Erro ao fazer upload do documento: {e}")

        # 6. Atualizar task como completed
        PortalRepository.update_task_status(
            task_id,
            "completed",
            file_path=docs_urls[0] if docs_urls else None,
            documents=docs_metadata
        )
        logger.info(f"Task {task_id} marcada como 'completed'")

        # 7. Adicionar resultado à solicitação
        status_resultado = "concluido" if docs_urls else "documentos_nao_encontrados"
        PortalRepository.update_solicitacao_cnj_result(
            solicitacao_id=solicitacao_id,
            cnj=process_number,
            status=status_resultado,
            documentos_urls=docs_urls,
            erro=None
        )

        # 8. Verificar se solicitação está completa
        final_status = PortalRepository.check_and_update_solicitacao_final_status(solicitacao_id)
        if final_status:
            logger.info(f"Solicitação {solicitacao_id} concluída com status: {final_status}")

        return {
            "status": "success",
            "task_id": task_id,
            "process_number": process_number,
            "documents_uploaded": len(docs_urls),
            "solicitacao_final_status": final_status
        }

    except Exception as e:
        logger.error(f"Erro ao processar task {task_id}: {e}")

        try:
            # Marcar task como failed
            PortalRepository.update_task_status(task_id, "failed")

            # Adicionar resultado de erro à solicitação
            PortalRepository.update_solicitacao_cnj_result(
                solicitacao_id=solicitacao_id,
                cnj=process_number,
                status="erro",
                documentos_urls=[],
                erro=str(e)
            )

            # Verificar se solicitação está completa (mesmo com erro)
            PortalRepository.check_and_update_solicitacao_final_status(solicitacao_id)

        except Exception as update_error:
            logger.error(f"Erro ao atualizar status de falha: {update_error}")

        # Retry com backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver fechado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao fechar driver: {e}")


@celery_app.task(name='portal_worker.get_portal_stats')
def get_portal_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do Portal.
    Útil para monitoramento e debugging.
    """
    try:
        PortalRepository.connect()
        return PortalRepository.get_portal_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return {"error": str(e)}


@celery_app.task(name='portal_worker.manual_process_task')
def manual_process_task(task_id: str) -> Dict[str, Any]:
    """
    Processa manualmente uma task específica.
    Útil para reprocessamento ou debugging.

    Args:
        task_id: ID da task no MongoDB

    Returns:
        Dict com resultado do processamento
    """
    try:
        PortalRepository.connect()

        # Busca a task
        task = PortalRepository._db.tasks.find_one({"_id": ObjectId(task_id)})

        if not task:
            return {"error": f"Task {task_id} não encontrada"}

        portal_metadata = task.get("portal_metadata", {})
        solicitacao_id = portal_metadata.get("solicitacao_id")

        if not solicitacao_id:
            return {"error": "Task não possui portal_metadata.solicitacao_id"}

        # Reseta status para pending
        PortalRepository.update_task_status(task_id, "pending")

        # Extrai pasta e codigo_pasta da task
        pasta = task.get("pasta")
        codigo_pasta = task.get("codigo_pasta")

        # Dispara processamento
        result = process_portal_task.delay(
            task_id=task_id,
            process_number=task["process_number"],
            client_name=task["client_name"],
            solicitacao_id=solicitacao_id,
            pasta=pasta,
            codigo_pasta=codigo_pasta
        )

        return {
            "status": "dispatched",
            "task_id": task_id,
            "celery_task_id": result.id
        }

    except Exception as e:
        logger.error(f"Erro ao processar manualmente: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Para debug local
    celery_app.start()
