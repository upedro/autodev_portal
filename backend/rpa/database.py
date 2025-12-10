"""
Gerenciamento de conexão com MongoDB
"""
from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
import logging

from settings import settings
from models import TaskStatus

logger = logging.getLogger(__name__)


class MongoDB:
    """Classe para gerenciar conexão com MongoDB"""

    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    @classmethod
    def connect(cls):
        """Conecta ao MongoDB"""
        try:
            cls.client = MongoClient(settings.MONGODB_URL)
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            # Testa a conexão
            cls.client.admin.command('ping')
            logger.info("Conectado ao MongoDB com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise

    @classmethod
    def disconnect(cls):
        """Desconecta do MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("Desconectado do MongoDB")

    @classmethod
    def get_tasks_collection(cls) -> Collection:
        """Retorna a coleção de tasks"""
        if cls.db is None:
            cls.connect()
        return cls.db[settings.MONGODB_COLLECTION_TASKS]


class TaskRepository:
    """Repositório para operações de tasks"""

    @staticmethod
    def create_task(process_number: str, client_name: str) -> str:
        """
        Cria uma nova tarefa

        Args:
            process_number: Número do processo
            client_name: Nome do cliente/robô

        Returns:
            ID da tarefa criada
        """
        collection = MongoDB.get_tasks_collection()

        task = {
            "process_number": process_number,
            "client_name": client_name,
            "status": TaskStatus.PENDING.value,
            "file_path": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = collection.insert_one(task)
        logger.info(f"Tarefa criada: {result.inserted_id}")
        return str(result.inserted_id)

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[dict]:
        """
        Busca uma tarefa pelo ID

        Args:
            task_id: ID da tarefa

        Returns:
            Documento da tarefa ou None
        """
        collection = MongoDB.get_tasks_collection()

        try:
            task = collection.find_one({"_id": ObjectId(task_id)})
            if task:
                task["_id"] = str(task["_id"])
            return task
        except Exception as e:
            logger.error(f"Erro ao buscar tarefa {task_id}: {e}")
            return None

    @staticmethod
    def get_task_by_process_number(process_number: str) -> Optional[dict]:
        """
        Busca uma tarefa pelo número do processo

        Args:
            process_number: Número do processo

        Returns:
            Documento da tarefa ou None
        """
        collection = MongoDB.get_tasks_collection()

        task = collection.find_one({"process_number": process_number})
        if task:
            task["_id"] = str(task["_id"])
        return task

    @staticmethod
    def get_tasks_by_status(status: TaskStatus) -> list:
        """
        Busca todas as tarefas com um determinado status

        Args:
            status: Status da tarefa

        Returns:
            Lista de tarefas
        """
        collection = MongoDB.get_tasks_collection()

        tasks = list(collection.find({"status": status.value}))
        for task in tasks:
            task["_id"] = str(task["_id"])
        return tasks

    @staticmethod
    def update_task_status(
        task_id: str,
        status: TaskStatus,
        file_path: Optional[str] = None,
        documents: Optional[list] = None
    ) -> bool:
        """
        Atualiza o status de uma tarefa

        Args:
            task_id: ID da tarefa
            status: Novo status
            file_path: Caminho do arquivo principal (opcional, compatibilidade)
            documents: Lista de documentos baixados com metadados (opcional)

        Returns:
            True se atualizado com sucesso
        """
        collection = MongoDB.get_tasks_collection()

        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }

        if file_path is not None:
            update_data["file_path"] = file_path

        if documents is not None:
            update_data["documents"] = documents
            update_data["total_documents"] = len(documents)

        try:
            result = collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )
            logger.info(f"Tarefa {task_id} atualizada para status {status.value}")
            if documents:
                logger.info(f"Tarefa {task_id} atualizada com {len(documents)} documento(s)")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erro ao atualizar tarefa {task_id}: {e}")
            return False

    @staticmethod
    def bulk_create_tasks(tasks_data: list) -> int:
        """
        Cria múltiplas tarefas de uma vez

        Args:
            tasks_data: Lista de dicionários com process_number e client_name

        Returns:
            Número de tarefas criadas
        """
        collection = MongoDB.get_tasks_collection()

        tasks = []
        for task_data in tasks_data:
            task = {
                "process_number": task_data["process_number"],
                "client_name": task_data["client_name"],
                "status": TaskStatus.PENDING.value,
                "file_path": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            tasks.append(task)

        if tasks:
            result = collection.insert_many(tasks)
            logger.info(f"{len(result.inserted_ids)} tarefas criadas")
            return len(result.inserted_ids)

        return 0
