"""
EXEMPLO: Worker modificado para incluir envio automático de GED

Este é um arquivo de exemplo mostrando como integrar o envio de GED
no worker existente. NÃO substitui o worker.py atual.

Para implementar:
1. Compare este arquivo com worker.py
2. Adicione apenas as seções marcadas com # *** GED ***
3. Teste em ambiente de desenvolvimento primeiro
"""

import os
import logging
from celery import Celery

from settings import settings
from models import TaskStatus
from database import MongoDB, TaskRepository
from rpa_logic import download_document, validate_process_number
from cloud_storage import get_azure_storage

# *** GED: Import do helper ***
from sistemas.advwin import get_ged_helper

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

# ... configurações do Celery ...


@celery_app.task(name='worker.process_task', bind=True, max_retries=3)
def process_task(self, task_id: str):
    """
    Tarefa principal de processamento RPA com envio para GED.

    Fluxo:
    1. Atualizar status para 'processing'
    2. Validar número do processo
    3. Executar lógica RPA (download do documento)
    4. *** NOVO: Enviar para ADVWin GED ***
    5. Upload para Azure Blob Storage
    6. Atualizar status para 'completed'
    """
    try:
        logger.info(f"Iniciando processamento da tarefa {task_id}")

        # Conecta ao MongoDB
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

        # ================================================================
        # *** GED: NOVO - Envio para ADVWin GED ***
        # ================================================================
        resultado_ged = None
        try:
            logger.info("="*80)
            logger.info("INICIANDO ENVIO PARA ADVWIN GED")
            logger.info("="*80)

            # Obtém instância do helper
            ged_helper = get_ged_helper()

            # Envia documentos para o GED
            resultado_ged = ged_helper.enviar_documentos_ged(
                documentos=documentos,
                numero_processo=process_number,
                tabela_or="Pastas",  # AJUSTE conforme necessário
                codigo_or=None,      # Usa numero_processo automaticamente
                id_or=None
            )

            logger.info("="*80)
            logger.info("RESULTADO DO ENVIO PARA GED")
            logger.info("="*80)
            logger.info(f"Total: {resultado_ged['total']}")
            logger.info(f"✓ Sucesso: {resultado_ged['sucesso']}")
            logger.info(f"✗ Falha: {resultado_ged['falha']}")
            logger.info("="*80)

            # Adiciona informação do GED aos metadados da tarefa
            if resultado_ged['sucesso'] > 0:
                logger.info(f"✓ {resultado_ged['sucesso']} documento(s) enviado(s) para GED")

        except Exception as e:
            # IMPORTANTE: Não falha a tarefa se o GED falhar
            # O processo continua com o upload para Azure
            logger.error("="*80)
            logger.error("ERRO NO ENVIO PARA GED (NÃO CRÍTICO)")
            logger.error("="*80)
            logger.error(f"Erro: {e}")
            logger.error("O processamento continuará com upload para Azure")
            logger.error("="*80)

            import traceback
            logger.error(traceback.format_exc())

            # Marca que houve erro no GED mas não interrompe
            resultado_ged = {
                "sucesso": 0,
                "falha": len(documentos),
                "erro": str(e)
            }

        # ================================================================
        # 4. Upload para Azure Blob Storage
        # ================================================================
        documentos_upload = []
        try:
            azure_storage = get_azure_storage()

            for idx, doc in enumerate(documentos, start=1):
                local_file_path = doc['caminho_arquivo']
                nome_arquivo_final = doc['nome_arquivo_final']

                # Gera o nome do blob
                blob_name = f"{client_name}/{process_number}/{nome_arquivo_final}"

                logger.info(f"[{idx}/{len(documentos)}] Fazendo upload para Azure: {blob_name}")
                blob_url = azure_storage.upload_file(local_file_path, blob_name)

                if not blob_url:
                    raise Exception(f"Erro no upload para Azure: URL não retornada")

                logger.info(f"[{idx}/{len(documentos)}] Upload Azure concluído: {blob_url}")

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

        # ================================================================
        # 5. Atualiza status para 'completed'
        # ================================================================

        # *** GED: Adiciona informações do GED aos metadados ***
        task_metadata = {
            "documents": documentos_upload,
            "ged_upload": resultado_ged  # Adiciona resultado do GED
        }

        TaskRepository.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            file_path=documentos_upload[0]['blob_url'] if len(documentos_upload) > 0 else None,
            documents=documentos_upload,
            metadata=task_metadata  # Metadados completos incluindo GED
        )

        logger.info("="*80)
        logger.info(f"✓ Tarefa {task_id} concluída com sucesso!")
        logger.info(f"  - Documentos baixados: {len(documentos)}")
        logger.info(f"  - Enviados para Azure: {len(documentos_upload)}")
        if resultado_ged:
            logger.info(f"  - Enviados para GED: {resultado_ged['sucesso']}")
        logger.info("="*80)

        return {
            "task_id": task_id,
            "status": "completed",
            "process_number": process_number,
            "client_name": client_name,
            "documents_count": len(documentos_upload),
            "ged_upload": resultado_ged
        }

    except Exception as e:
        logger.error(f"Erro ao processar tarefa {task_id}: {e}")

        # Atualiza status para 'failed'
        try:
            TaskRepository.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=str(e)
            )
        except Exception as db_error:
            logger.error(f"Erro ao atualizar status de falha: {db_error}")

        # Tenta retry
        if self.request.retries < self.max_retries:
            logger.info(f"Tentando novamente... (tentativa {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        raise


# ================================================================
# *** GED: NOVA TASK OPCIONAL - Reenvio de GED ***
# ================================================================

@celery_app.task(name='worker.retry_ged_upload', bind=True)
def retry_ged_upload(self, task_id: str):
    """
    Task opcional para reenviar documentos para o GED

    Útil para casos onde o upload para Azure funcionou mas o GED falhou.
    Pode ser chamado manualmente ou agendado.

    Args:
        task_id: ID da tarefa cujos documentos devem ser reenviados

    Returns:
        dict: Resultado do reenvio
    """
    try:
        logger.info(f"Reenviando documentos para GED - Tarefa {task_id}")

        # Conecta ao MongoDB
        if MongoDB.db is None:
            MongoDB.connect()

        # Busca a tarefa
        task = TaskRepository.get_task_by_id(task_id)
        if not task:
            raise Exception(f"Tarefa {task_id} não encontrada")

        # Verifica se a tarefa foi completada
        if task.get("status") != TaskStatus.COMPLETED.value:
            raise Exception(f"Tarefa {task_id} não está com status 'completed'")

        # Busca documentos da tarefa
        documentos = task.get("documents", [])
        if not documentos:
            raise Exception("Nenhum documento encontrado na tarefa")

        process_number = task["process_number"]

        logger.info(f"Reenviando {len(documentos)} documento(s) para processo {process_number}")

        # Prepara lista de documentos no formato esperado pelo helper
        # NOTA: Os arquivos devem ainda existir localmente ou serem baixados do Azure
        # Este é um exemplo simplificado

        ged_helper = get_ged_helper()

        # ... lógica de reenvio aqui ...
        # (implementação depende se os arquivos ainda existem localmente)

        logger.info(f"✓ Reenvio para GED concluído para tarefa {task_id}")

        return {
            "task_id": task_id,
            "status": "ged_resent",
            "process_number": process_number
        }

    except Exception as e:
        logger.error(f"Erro ao reenviar para GED - Tarefa {task_id}: {e}")
        raise


if __name__ == '__main__':
    """
    Para executar o worker:
    celery -A worker worker --loglevel=info --pool=solo
    """
    celery_app.start()
