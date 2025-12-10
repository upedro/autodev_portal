"""
Simplified event system for document request workflow
Based on MongoDB event-driven architecture from RPA project
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.status import EventoTipo, SolicitacaoStatus

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to MongoDB for event-driven processing"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def publish_event(
        self,
        tipo_evento: EventoTipo,
        solicitacao_id: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Publish an event to the events collection

        Args:
            tipo_evento: Event type
            solicitacao_id: Request ID
            metadata: Additional event metadata

        Returns:
            True if published successfully
        """
        try:
            event_doc = {
                "tipo_evento": tipo_evento.value,
                "solicitacao_id": solicitacao_id,
                "metadata": metadata or {},
                "processado": False,
                "created_at": datetime.utcnow(),
                "processed_at": None,
            }

            result = await self.db.eventos.insert_one(event_doc)

            logger.info(
                f"Event published: {tipo_evento.value} for solicitacao {solicitacao_id}"
            )
            return result.inserted_id is not None

        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False

    async def get_pending_events(
        self, tipo_evento: Optional[EventoTipo] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get pending (unprocessed) events

        Args:
            tipo_evento: Filter by event type (optional)
            limit: Maximum number of events to return

        Returns:
            List of pending events
        """
        try:
            query = {"processado": False}

            if tipo_evento:
                query["tipo_evento"] = tipo_evento.value

            cursor = (
                self.db.eventos.find(query)
                .sort("created_at", 1)  # FIFO processing
                .limit(limit)
            )

            events = await cursor.to_list(length=limit)
            return events

        except Exception as e:
            logger.error(f"Error getting pending events: {e}")
            return []

    async def mark_event_processed(
        self, event_id: Any, success: bool = True, error: str = None
    ) -> bool:
        """
        Mark an event as processed

        Args:
            event_id: Event document ID
            success: Whether processing was successful
            error: Error message if failed

        Returns:
            True if marked successfully
        """
        try:
            update_data = {
                "processado": True,
                "processed_at": datetime.utcnow(),
                "success": success,
            }

            if error:
                update_data["error"] = error

            result = await self.db.eventos.update_one(
                {"_id": event_id}, {"$set": update_data}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error marking event as processed: {e}")
            return False


class SolicitacaoUpdater:
    """Updates solicitacao status and results"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def update_status(
        self, solicitacao_id: str, new_status: SolicitacaoStatus
    ) -> bool:
        """
        Update solicitacao status

        Args:
            solicitacao_id: Request ID
            new_status: New status

        Returns:
            True if updated successfully
        """
        try:
            from bson import ObjectId

            update_data = {
                "status": new_status.value,
                "updated_at": datetime.utcnow(),
            }

            # Set iniciado_em when starting
            if new_status == SolicitacaoStatus.EM_EXECUCAO:
                update_data["iniciado_em"] = datetime.utcnow()

            # Set concluido_em when finishing
            if new_status in [
                SolicitacaoStatus.CONCLUIDO,
                SolicitacaoStatus.ERRO,
                SolicitacaoStatus.DOCUMENTOS_NAO_ENCONTRADOS,
            ]:
                update_data["concluido_em"] = datetime.utcnow()

            result = await self.db.solicitacoes.update_one(
                {"_id": ObjectId(solicitacao_id)}, {"$set": update_data}
            )

            logger.info(f"Solicitacao {solicitacao_id} status updated to {new_status.value}")
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating solicitacao status: {e}")
            return False

    async def add_cnj_result(
        self,
        solicitacao_id: str,
        cnj: str,
        status: str,
        documentos_urls: List[str] = None,
        erro: str = None,
    ) -> bool:
        """
        Add processing result for a CNJ

        Args:
            solicitacao_id: Request ID
            cnj: CNJ process number
            status: Processing status
            documentos_urls: List of document URLs
            erro: Error message if failed

        Returns:
            True if added successfully
        """
        try:
            from bson import ObjectId

            resultado = {
                "cnj": cnj,
                "status": status,
                "documentos_encontrados": len(documentos_urls or []),
                "documentos_urls": documentos_urls or [],
                "erro": erro,
                "processado_em": datetime.utcnow(),
            }

            # Add result to array
            await self.db.solicitacoes.update_one(
                {"_id": ObjectId(solicitacao_id)},
                {
                    "$push": {"resultados": resultado},
                    "$inc": {
                        "cnjs_processados": 1,
                        "cnjs_sucesso": 1 if status == "concluido" else 0,
                        "cnjs_erro": 1 if status == "erro" else 0,
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            logger.info(f"Result added for CNJ {cnj} in solicitacao {solicitacao_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding CNJ result: {e}")
            return False

    async def get_solicitacao(self, solicitacao_id: str) -> Optional[Dict[str, Any]]:
        """
        Get solicitacao by ID

        Args:
            solicitacao_id: Request ID

        Returns:
            Solicitacao document or None
        """
        try:
            from bson import ObjectId

            solicitacao = await self.db.solicitacoes.find_one(
                {"_id": ObjectId(solicitacao_id)}
            )
            return solicitacao

        except Exception as e:
            logger.error(f"Error getting solicitacao: {e}")
            return None
