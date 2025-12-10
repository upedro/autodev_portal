"""
Gerenciamento de upload para Azure Blob Storage e armazenamento local
"""
import os
import shutil
import logging
from typing import Optional
from pathlib import Path

from settings import settings

logger = logging.getLogger(__name__)

# Tenta importar Azure (pode não estar disponível ou configurado)
try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
except ImportError:
    logger.warning("Azure Storage não está instalado. Usando apenas armazenamento local.")
    AZURE_AVAILABLE = False


class AzureBlobStorage:
    """Classe para gerenciar uploads para Azure Blob Storage"""

    def __init__(self):
        """Inicializa o cliente do Azure Blob Storage"""
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            self.container_name = settings.AZURE_CONTAINER_NAME
            self._ensure_container_exists()
            logger.info("Cliente Azure Blob Storage inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Azure: {e}")
            raise

    def _ensure_container_exists(self):
        """Garante que o container existe, criando-o se necessário"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Container '{self.container_name}' criado")
            else:
                logger.info(f"Container '{self.container_name}' já existe")
        except Exception as e:
            logger.error(f"Erro ao verificar/criar container: {e}")
            raise

    def upload_file(
        self,
        local_file_path: str,
        blob_name: str,
        overwrite: bool = True
    ) -> Optional[str]:
        """
        Faz upload de um arquivo para o Azure Blob Storage

        Args:
            local_file_path: Caminho do arquivo local
            blob_name: Nome do blob no Azure (ex: client_name/process_number.pdf)
            overwrite: Se True, sobrescreve arquivo existente

        Returns:
            URL do blob no Azure ou None em caso de erro
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(local_file_path):
                logger.error(f"Arquivo não encontrado: {local_file_path}")
                return None

            # Cria o cliente do blob
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Faz upload do arquivo
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=overwrite)

            # Retorna a URL do blob
            blob_url = blob_client.url
            logger.info(f"Arquivo enviado com sucesso: {blob_url}")
            return blob_url

        except AzureError as e:
            logger.error(f"Erro ao fazer upload para Azure: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao fazer upload: {e}")
            return None

    def download_file(
        self,
        blob_name: str,
        local_file_path: str
    ) -> bool:
        """
        Faz download de um arquivo do Azure Blob Storage

        Args:
            blob_name: Nome do blob no Azure
            local_file_path: Caminho onde salvar o arquivo localmente

        Returns:
            True se o download foi bem-sucedido
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Faz download do blob
            with open(local_file_path, "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())

            logger.info(f"Arquivo baixado com sucesso: {local_file_path}")
            return True

        except AzureError as e:
            logger.error(f"Erro ao fazer download do Azure: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao fazer download: {e}")
            return False

    def delete_file(self, blob_name: str) -> bool:
        """
        Delete um arquivo do Azure Blob Storage

        Args:
            blob_name: Nome do blob no Azure

        Returns:
            True se o arquivo foi deletado com sucesso
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_client.delete_blob()
            logger.info(f"Arquivo deletado com sucesso: {blob_name}")
            return True

        except AzureError as e:
            logger.error(f"Erro ao deletar arquivo do Azure: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar arquivo: {e}")
            return False

    def file_exists(self, blob_name: str) -> bool:
        """
        Verifica se um arquivo existe no Azure Blob Storage

        Args:
            blob_name: Nome do blob no Azure

        Returns:
            True se o arquivo existe
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            return blob_client.exists()

        except Exception as e:
            logger.error(f"Erro ao verificar existência do arquivo: {e}")
            return False

    def get_blob_url(self, blob_name: str) -> Optional[str]:
        """
        Retorna a URL de um blob

        Args:
            blob_name: Nome do blob no Azure

        Returns:
            URL do blob ou None
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            return blob_client.url

        except Exception as e:
            logger.error(f"Erro ao obter URL do blob: {e}")
            return None

    def generate_sas_url(self, blob_name: str, expiry_hours: int = 24) -> Optional[str]:
        """
        Gera URL com SAS token para download temporário.
        Útil para compartilhar links de download com tempo de expiração.

        Args:
            blob_name: Nome do blob no Azure
            expiry_hours: Horas até expiração do token (padrão: 24)

        Returns:
            URL com SAS token ou None em caso de erro
        """
        try:
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import datetime, timedelta

            # Obtém account name e key da connection string
            conn_parts = dict(
                part.split('=', 1) for part in
                settings.AZURE_STORAGE_CONNECTION_STRING.split(';')
                if '=' in part
            )

            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')

            if not account_name or not account_key:
                logger.error("Não foi possível extrair credenciais da connection string")
                return None

            # Gera SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )

            # Monta URL completa
            sas_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

            logger.info(f"SAS URL gerada para {blob_name} (expira em {expiry_hours}h)")
            return sas_url

        except ImportError:
            logger.error("Módulo azure.storage.blob não suporta generate_blob_sas")
            return self.get_blob_url(blob_name)
        except Exception as e:
            logger.error(f"Erro ao gerar SAS URL: {e}")
            return None


class LocalStorage:
    """Classe para gerenciar armazenamento local de arquivos"""

    def __init__(self):
        """Inicializa o armazenamento local"""
        self.storage_path = settings.LOCAL_STORAGE_PATH
        self._ensure_directory_exists()
        logger.info(f"Armazenamento local inicializado em: {self.storage_path}")

    def _ensure_directory_exists(self):
        """Garante que o diretório de armazenamento existe"""
        os.makedirs(self.storage_path, exist_ok=True)

    def upload_file(
        self,
        local_file_path: str,
        blob_name: str,
        overwrite: bool = True
    ) -> Optional[str]:
        """
        Copia um arquivo para o armazenamento local

        Args:
            local_file_path: Caminho do arquivo local
            blob_name: Nome relativo do arquivo (ex: client_name/process_number.pdf)
            overwrite: Se True, sobrescreve arquivo existente

        Returns:
            Caminho do arquivo no armazenamento local
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(local_file_path):
                logger.error(f"Arquivo não encontrado: {local_file_path}")
                return None

            # Define o caminho de destino
            destination_path = os.path.join(self.storage_path, blob_name)

            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Verifica se o arquivo já existe
            if os.path.exists(destination_path) and not overwrite:
                logger.warning(f"Arquivo já existe: {destination_path}")
                return destination_path

            # Copia o arquivo
            shutil.copy2(local_file_path, destination_path)

            logger.info(f"Arquivo salvo com sucesso: {destination_path}")
            return destination_path

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo localmente: {e}")
            return None

    def download_file(
        self,
        blob_name: str,
        local_file_path: str
    ) -> bool:
        """
        Copia um arquivo do armazenamento local

        Args:
            blob_name: Nome relativo do arquivo
            local_file_path: Caminho onde salvar o arquivo

        Returns:
            True se o download foi bem-sucedido
        """
        try:
            source_path = os.path.join(self.storage_path, blob_name)

            if not os.path.exists(source_path):
                logger.error(f"Arquivo não encontrado: {source_path}")
                return False

            # Cria o diretório de destino se não existir
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Copia o arquivo
            shutil.copy2(source_path, local_file_path)

            logger.info(f"Arquivo copiado com sucesso: {local_file_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao copiar arquivo: {e}")
            return False

    def delete_file(self, blob_name: str) -> bool:
        """
        Deleta um arquivo do armazenamento local

        Args:
            blob_name: Nome relativo do arquivo

        Returns:
            True se o arquivo foi deletado com sucesso
        """
        try:
            file_path = os.path.join(self.storage_path, blob_name)

            if not os.path.exists(file_path):
                logger.warning(f"Arquivo não encontrado para deletar: {file_path}")
                return False

            os.remove(file_path)
            logger.info(f"Arquivo deletado com sucesso: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {e}")
            return False

    def file_exists(self, blob_name: str) -> bool:
        """
        Verifica se um arquivo existe no armazenamento local

        Args:
            blob_name: Nome relativo do arquivo

        Returns:
            True se o arquivo existe
        """
        file_path = os.path.join(self.storage_path, blob_name)
        return os.path.exists(file_path)

    def get_file_path(self, blob_name: str) -> Optional[str]:
        """
        Retorna o caminho completo de um arquivo

        Args:
            blob_name: Nome relativo do arquivo

        Returns:
            Caminho completo do arquivo ou None
        """
        file_path = os.path.join(self.storage_path, blob_name)
        if os.path.exists(file_path):
            return os.path.abspath(file_path)
        return None


# Instâncias globais para reuso
azure_storage = None
local_storage = None


def get_storage():
    """
    Retorna uma instância de armazenamento (Azure ou Local)

    Se USE_LOCAL_STORAGE estiver True ou Azure não estiver configurado,
    retorna LocalStorage, caso contrário retorna AzureBlobStorage.

    Returns:
        Instância de LocalStorage ou AzureBlobStorage
    """
    global azure_storage, local_storage

    # Verifica se deve usar armazenamento local
    use_local = settings.USE_LOCAL_STORAGE or not settings.AZURE_STORAGE_CONNECTION_STRING

    if use_local:
        if local_storage is None:
            local_storage = LocalStorage()
            logger.info("Usando armazenamento LOCAL")
        return local_storage
    else:
        if not AZURE_AVAILABLE:
            logger.warning("Azure não disponível, usando armazenamento local")
            if local_storage is None:
                local_storage = LocalStorage()
            return local_storage

        if azure_storage is None:
            try:
                azure_storage = AzureBlobStorage()
                logger.info("Usando armazenamento AZURE")
            except Exception as e:
                logger.error(f"Erro ao inicializar Azure, usando local: {e}")
                if local_storage is None:
                    local_storage = LocalStorage()
                return local_storage
        return azure_storage


# Mantém compatibilidade com código existente
def get_azure_storage():
    """
    Retorna uma instância de armazenamento (compatibilidade com código existente)

    Returns:
        Instância de LocalStorage ou AzureBlobStorage
    """
    return get_storage()
