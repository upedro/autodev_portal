"""
Azure Blob Storage handler for document management
Adapted from RPA project
"""
import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError
import tempfile

logger = logging.getLogger(__name__)


class AzureStorageHandler:
    """Handler for Azure Blob Storage operations"""

    def __init__(
        self,
        connection_string: str = None,
        container_name: str = "portal-documentos",
    ):
        """
        Initialize Azure Blob Storage handler

        Args:
            connection_string: Azure Storage connection string
            container_name: Container name for document storage
        """
        self.connection_string = connection_string or os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING"
        )

        if not self.connection_string:
            raise ValueError(
                "Azure Storage connection string not found. "
                "Set AZURE_STORAGE_CONNECTION_STRING environment variable."
            )

        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )

        self._ensure_container_exists()
        logger.info(f"Azure Blob Storage configured with container: {container_name}")

    def _ensure_container_exists(self):
        """Ensure container exists, create if necessary"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            container_client.get_container_properties()
            logger.info(f"Container '{self.container_name}' already exists")
        except ResourceNotFoundError:
            container_client = self.blob_service_client.create_container(
                self.container_name
            )
            logger.info(f"Container '{self.container_name}' created successfully")

    def _generate_blob_path(
        self, cliente_codigo: str, cnj: str, filename: str
    ) -> str:
        """
        Generate structured blob path

        Args:
            cliente_codigo: Client code
            cnj: CNJ process number
            filename: File name

        Returns:
            Structured blob path: cliente/cnj/filename
        """
        # Clean CNJ for use in path
        cnj_clean = cnj.replace(".", "_").replace("-", "_")
        return f"{cliente_codigo}/{cnj_clean}/{filename}"

    def upload_file(
        self,
        local_file_path: str,
        cliente_codigo: str,
        cnj: str,
        filename: str = None,
        metadata: Dict = None,
    ) -> Dict:
        """
        Upload file to Azure Blob Storage

        Args:
            local_file_path: Local file path
            cliente_codigo: Client code
            cnj: CNJ process number
            filename: File name (optional, uses local filename if not provided)
            metadata: Additional blob metadata

        Returns:
            Upload result dictionary
        """
        try:
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")

            if not filename:
                filename = os.path.basename(local_file_path)

            blob_path = self._generate_blob_path(cliente_codigo, cnj, filename)

            blob_metadata = {
                "cliente_codigo": cliente_codigo,
                "cnj": cnj,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "original_filename": filename,
                "uploaded_by": "portal_rpa_system",
            }

            if metadata:
                blob_metadata.update(metadata)

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_path
            )

            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True, metadata=blob_metadata)

            blob_properties = blob_client.get_blob_properties()

            result = {
                "success": True,
                "blob_path": blob_path,
                "blob_url": blob_client.url,
                "size_bytes": blob_properties.size,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "metadata": blob_metadata,
                "etag": blob_properties.etag,
                "container": self.container_name,
            }

            logger.info(f"File uploaded successfully: {blob_path}")
            return result

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def upload_from_memory(
        self,
        data: bytes,
        cliente_codigo: str,
        cnj: str,
        filename: str,
        metadata: Dict = None,
    ) -> Dict:
        """
        Upload data from memory to Azure Blob Storage

        Args:
            data: Data in bytes
            cliente_codigo: Client code
            cnj: CNJ process number
            filename: File name
            metadata: Additional metadata

        Returns:
            Upload result dictionary
        """
        try:
            blob_path = self._generate_blob_path(cliente_codigo, cnj, filename)

            blob_metadata = {
                "cliente_codigo": cliente_codigo,
                "cnj": cnj,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "original_filename": filename,
                "uploaded_by": "portal_rpa_system",
                "upload_method": "memory",
            }

            if metadata:
                blob_metadata.update(metadata)

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_path
            )

            blob_client.upload_blob(data, overwrite=True, metadata=blob_metadata)

            blob_properties = blob_client.get_blob_properties()

            result = {
                "success": True,
                "blob_path": blob_path,
                "blob_url": blob_client.url,
                "size_bytes": blob_properties.size,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "metadata": blob_metadata,
                "etag": blob_properties.etag,
                "container": self.container_name,
            }

            logger.info(f"Data uploaded from memory successfully: {blob_path}")
            return result

        except Exception as e:
            logger.error(f"Error uploading from memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def list_files_by_cnj(
        self, cliente_codigo: str, cnj: str
    ) -> List[Dict]:
        """
        List all files for a specific CNJ

        Args:
            cliente_codigo: Client code
            cnj: CNJ process number

        Returns:
            List of file information dictionaries
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            cnj_clean = cnj.replace(".", "_").replace("-", "_")
            prefix = f"{cliente_codigo}/{cnj_clean}/"

            blobs = container_client.list_blobs(name_starts_with=prefix)

            files = []
            for blob in blobs:
                file_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat(),
                    "metadata": blob.metadata or {},
                    "url": f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}",
                }
                files.append(file_info)

            logger.info(f"Found {len(files)} files for CNJ {cnj}")
            return files

        except Exception as e:
            logger.error(f"Error listing files for CNJ {cnj}: {e}")
            return []

    def generate_sas_url(self, blob_path: str, expiry_hours: int = 24) -> str:
        """
        Generate SAS URL for temporary file access

        Args:
            blob_path: Blob path
            expiry_hours: Hours until expiration (default: 24h)

        Returns:
            URL with SAS token
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_path
            )

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
            )

            sas_url = f"{blob_client.url}?{sas_token}"

            logger.info(f"SAS URL generated for {blob_path}")
            return sas_url

        except Exception as e:
            logger.error(f"Error generating SAS URL: {e}")
            return ""

    def delete_file(self, blob_path: str) -> Dict:
        """
        Delete file from Azure Blob Storage

        Args:
            blob_path: Blob path

        Returns:
            Operation result dictionary
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_path
            )

            blob_client.delete_blob()

            result = {
                "success": True,
                "blob_path": blob_path,
                "deleted_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"File deleted successfully: {blob_path}")
            return result

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
