"""
Repositório para acesso às collections do Portal (MongoDB compartilhado)
Usa driver síncrono (pymongo) para compatibilidade com Celery workers
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from pymongo import MongoClient
from bson import ObjectId

from settings import settings

logger = logging.getLogger(__name__)


class PortalRepository:
    """
    Acesso sincronizado às collections do Portal.
    Projetado para uso em Celery workers.
    """

    _client: Optional[MongoClient] = None
    _db = None

    @classmethod
    def connect(cls):
        """Estabelece conexão com MongoDB do Portal"""
        if cls._client is None:
            cls._client = MongoClient(settings.MONGODB_URL)
            cls._db = cls._client[settings.PORTAL_MONGODB_DB_NAME]
            # Teste de conexão
            cls._client.admin.command('ping')
            logger.info(f"Conectado ao MongoDB do Portal: {settings.PORTAL_MONGODB_DB_NAME}")

    @classmethod
    def disconnect(cls):
        """Fecha conexão com MongoDB"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("Desconectado do MongoDB do Portal")

    @classmethod
    def ensure_connected(cls):
        """Garante que a conexão está ativa"""
        if cls._db is None:
            cls.connect()

    # ==================== Tasks Collection ====================

    @classmethod
    def get_pending_tasks_with_portal_metadata(cls, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca tasks criadas pelo Portal que estão pendentes.
        Tasks do Portal possuem o campo 'portal_metadata'.
        """
        cls.ensure_connected()

        tasks = list(cls._db.tasks.find({
            "status": "pending",
            "portal_metadata": {"$exists": True}
        }).sort("created_at", 1).limit(limit))

        # Converte ObjectId para string
        for task in tasks:
            task["_id"] = str(task["_id"])

        logger.info(f"Encontradas {len(tasks)} tasks pendentes do Portal")
        return tasks

    @classmethod
    def update_task_status(
        cls,
        task_id: str,
        status: str,
        file_path: Optional[str] = None,
        documents: Optional[List[Dict]] = None
    ) -> bool:
        """Atualiza status de uma task"""
        cls.ensure_connected()

        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if file_path is not None:
            update_data["file_path"] = file_path

        if documents is not None:
            update_data["documents"] = documents
            update_data["total_documents"] = len(documents)

        result = cls._db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    # ==================== Clientes Collection ====================

    @classmethod
    def get_cliente_by_id(cls, cliente_id: str) -> Optional[Dict[str, Any]]:
        """Busca cliente pelo ID"""
        cls.ensure_connected()

        cliente = cls._db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if cliente:
            cliente["_id"] = str(cliente["_id"])
        return cliente

    @classmethod
    def get_cliente_by_codigo(cls, codigo: str) -> Optional[Dict[str, Any]]:
        """Busca cliente pelo código (ex: 'cogna', 'loft')"""
        cls.ensure_connected()

        cliente = cls._db.clientes.find_one({"codigo": codigo, "ativo": True})
        if cliente:
            cliente["_id"] = str(cliente["_id"])
        return cliente

    # ==================== Solicitacoes Collection ====================

    @classmethod
    def get_solicitacao_by_id(cls, solicitacao_id: str) -> Optional[Dict[str, Any]]:
        """Busca solicitação pelo ID"""
        cls.ensure_connected()

        sol = cls._db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})
        if sol:
            sol["_id"] = str(sol["_id"])
        return sol

    @classmethod
    def update_solicitacao_status(
        cls,
        solicitacao_id: str,
        status: str,
        iniciado_em: Optional[datetime] = None,
        concluido_em: Optional[datetime] = None
    ) -> bool:
        """Atualiza status de uma solicitação"""
        cls.ensure_connected()

        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if iniciado_em:
            update_data["iniciado_em"] = iniciado_em

        if concluido_em:
            update_data["concluido_em"] = concluido_em

        result = cls._db.solicitacoes.update_one(
            {"_id": ObjectId(solicitacao_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    @classmethod
    def update_solicitacao_to_em_execucao(cls, solicitacao_id: str) -> bool:
        """
        Atualiza solicitação para 'em_execucao' apenas se ainda estiver 'pendente'.
        Usa operação atômica para evitar race conditions.
        """
        cls.ensure_connected()

        result = cls._db.solicitacoes.update_one(
            {
                "_id": ObjectId(solicitacao_id),
                "status": "pendente"
            },
            {
                "$set": {
                    "status": "em_execucao",
                    "iniciado_em": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    @classmethod
    def update_solicitacao_cnj_result(
        cls,
        solicitacao_id: str,
        cnj: str,
        status: str,
        documentos_urls: List[str],
        erro: Optional[str] = None
    ) -> bool:
        """
        Adiciona resultado de processamento de um CNJ à solicitação.
        Usa operações atômicas ($push, $inc) para thread-safety.
        """
        cls.ensure_connected()

        resultado = {
            "cnj": cnj,
            "status": status,
            "documentos_encontrados": len(documentos_urls),
            "documentos_urls": documentos_urls,
            "erro": erro,
            "processado_em": datetime.utcnow()
        }

        # Determina incrementos baseado no status
        is_success = status in ["concluido", "completed"]
        is_error = status in ["erro", "failed"]

        result = cls._db.solicitacoes.update_one(
            {"_id": ObjectId(solicitacao_id)},
            {
                "$push": {"resultados": resultado},
                "$inc": {
                    "cnjs_processados": 1,
                    "cnjs_sucesso": 1 if is_success else 0,
                    "cnjs_erro": 1 if is_error else 0,
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"Resultado CNJ {cnj} adicionado à solicitação {solicitacao_id}: {status}")
        return result.modified_count > 0

    @classmethod
    def check_and_update_solicitacao_final_status(cls, solicitacao_id: str) -> Optional[str]:
        """
        Verifica se todos os CNJs foram processados e atualiza o status final.
        Retorna o status final se a solicitação foi concluída, None caso contrário.
        """
        cls.ensure_connected()

        sol = cls._db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})

        if not sol:
            logger.warning(f"Solicitação {solicitacao_id} não encontrada")
            return None

        # Verifica se todos CNJs foram processados
        if sol["cnjs_processados"] < sol["total_cnjs"]:
            logger.debug(f"Solicitação {solicitacao_id}: {sol['cnjs_processados']}/{sol['total_cnjs']} CNJs processados")
            return None

        # Determina status final
        if sol["cnjs_erro"] == sol["total_cnjs"]:
            final_status = "erro"
        elif sol["cnjs_sucesso"] > 0:
            final_status = "concluido"
        else:
            final_status = "documentos_nao_encontrados"

        # Atualiza status final
        cls._db.solicitacoes.update_one(
            {"_id": ObjectId(solicitacao_id)},
            {
                "$set": {
                    "status": final_status,
                    "concluido_em": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Solicitação {solicitacao_id} concluída com status: {final_status}")
        return final_status

    # ==================== Utility Methods ====================

    @classmethod
    def get_portal_stats(cls) -> Dict[str, Any]:
        """Retorna estatísticas do Portal"""
        cls.ensure_connected()

        # Contagem de solicitações por status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]

        status_counts = {}
        for doc in cls._db.solicitacoes.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        # Contagem de tasks pendentes do portal
        pending_tasks = cls._db.tasks.count_documents({
            "status": "pending",
            "portal_metadata": {"$exists": True}
        })

        return {
            "solicitacoes_by_status": status_counts,
            "pending_portal_tasks": pending_tasks
        }
