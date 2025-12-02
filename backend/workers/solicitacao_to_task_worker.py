"""
Worker to convert Solicitacoes to RPA Tasks
Listens for new solicitacoes and creates tasks in the RPA format
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from database import db_manager
from models.status import EventoTipo, SolicitacaoStatus
from workers.event_system import EventPublisher, SolicitacaoUpdater

logger = logging.getLogger(__name__)


class SolicitacaoToTaskConverter:
    """
    Converts Portal Web solicitacoes to RPA tasks format
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.event_publisher = EventPublisher(db)
        self.solicitacao_updater = SolicitacaoUpdater(db)
        self.is_running = False

    async def start_monitoring(self):
        """Monitor for new solicitacoes and create RPA tasks"""
        logger.info("🤖 Starting Solicitacao to Task converter...")
        self.is_running = True

        while self.is_running:
            try:
                # Get pending events
                events = await self.event_publisher.get_pending_events(
                    tipo_evento=EventoTipo.NOVA_SOLICITACAO,
                    limit=10
                )

                for event in events:
                    try:
                        await self._process_solicitacao_event(event)
                        await self.event_publisher.mark_event_processed(
                            event["_id"],
                            success=True
                        )
                    except Exception as e:
                        logger.error(f"Error processing event {event['_id']}: {e}")
                        await self.event_publisher.mark_event_processed(
                            event["_id"],
                            success=False,
                            error=str(e)
                        )

                # Sleep before next poll
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)

    async def stop_monitoring(self):
        """Stop monitoring"""
        logger.info("🛑 Stopping Solicitacao to Task converter...")
        self.is_running = False

    async def _process_solicitacao_event(self, event: Dict[str, Any]):
        """
        Process a NOVA_SOLICITACAO event and create RPA tasks

        Args:
            event: Event document from MongoDB
        """
        solicitacao_id = event["solicitacao_id"]
        metadata = event.get("metadata", {})

        logger.info(f"📋 Processing solicitacao {solicitacao_id}")

        # Get solicitacao from database
        solicitacao = await self.solicitacao_updater.get_solicitacao(solicitacao_id)

        if not solicitacao:
            logger.error(f"Solicitacao {solicitacao_id} not found")
            return

        # Get client info
        cliente = await self.db.clientes.find_one(
            {"_id": ObjectId(solicitacao["cliente_id"])}
        )

        if not cliente:
            logger.error(f"Client {solicitacao['cliente_id']} not found")
            return

        # Update solicitacao status to EM_EXECUCAO
        await self.solicitacao_updater.update_status(
            solicitacao_id,
            SolicitacaoStatus.EM_EXECUCAO
        )

        # Create RPA tasks for each CNJ
        tasks_created = []
        for cnj in solicitacao["cnjs"]:
            task_doc = await self._create_rpa_task(
                cnj=cnj,
                client_name=cliente["codigo"],
                solicitacao_id=solicitacao_id
            )
            if task_doc:
                tasks_created.append(task_doc["_id"])

        logger.info(
            f"✅ Created {len(tasks_created)} RPA tasks for solicitacao {solicitacao_id}"
        )

        # Store task IDs in solicitacao metadata
        await self.db.solicitacoes.update_one(
            {"_id": ObjectId(solicitacao_id)},
            {
                "$set": {
                    "rpa_task_ids": [str(tid) for tid in tasks_created],
                    "updated_at": datetime.utcnow(),
                }
            }
        )

    async def _create_rpa_task(
        self, cnj: str, client_name: str, solicitacao_id: str
    ) -> Dict[str, Any]:
        """
        Create a task in RPA format

        Args:
            cnj: CNJ process number
            client_name: Client code (agibank, creditas, etc)
            solicitacao_id: Portal solicitacao ID

        Returns:
            Created task document
        """
        try:
            # Clean CNJ to match RPA format (remove dots and dashes if needed)
            # Keep original format for now
            process_number = cnj

            # Create task document in RPA format
            task_doc = {
                "process_number": process_number,
                "client_name": client_name,
                "status": "pending",  # RPA will process from pending
                "file_path": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                # Additional metadata for tracking back to portal
                "portal_metadata": {
                    "solicitacao_id": solicitacao_id,
                    "source": "portal_web",
                    "created_by": "solicitacao_worker",
                },
            }

            # Insert into tasks collection
            result = await self.db.tasks.insert_one(task_doc)

            logger.info(
                f"✅ Created RPA task {result.inserted_id} for CNJ {cnj}"
            )

            return {**task_doc, "_id": result.inserted_id}

        except Exception as e:
            logger.error(f"Error creating RPA task for CNJ {cnj}: {e}")
            return None


class TaskStatusMonitor:
    """
    Monitors RPA tasks and updates Portal solicitacoes
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.solicitacao_updater = SolicitacaoUpdater(db)
        self.is_running = False
        self._last_checked = {}

    async def start_monitoring(self):
        """Monitor RPA tasks and update solicitacoes"""
        logger.info("👀 Starting Task Status Monitor...")
        self.is_running = True

        while self.is_running:
            try:
                # Find tasks created by portal
                tasks = await self.db.tasks.find(
                    {"portal_metadata.source": "portal_web"}
                ).to_list(length=100)

                for task in tasks:
                    task_id = str(task["_id"])
                    current_status = task["status"]
                    last_status = self._last_checked.get(task_id)

                    # Check if status changed
                    if last_status != current_status:
                        await self._update_solicitacao_from_task(task)
                        self._last_checked[task_id] = current_status

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in task monitoring: {e}")
                await asyncio.sleep(15)

    async def stop_monitoring(self):
        """Stop monitoring"""
        logger.info("🛑 Stopping Task Status Monitor...")
        self.is_running = False

    async def _update_solicitacao_from_task(self, task: Dict[str, Any]):
        """
        Update solicitacao based on task status change

        Args:
            task: RPA task document
        """
        try:
            portal_metadata = task.get("portal_metadata", {})
            solicitacao_id = portal_metadata.get("solicitacao_id")

            if not solicitacao_id:
                return

            cnj = task["process_number"]
            task_status = task["status"]

            logger.info(f"📊 Updating solicitacao {solicitacao_id} for CNJ {cnj}: {task_status}")

            # Map RPA status to portal status
            status_map = {
                "pending": "pendente",
                "processing": "em_execucao",
                "completed": "concluido",
                "failed": "erro",
            }

            portal_status = status_map.get(task_status, "pendente")

            # Get file URLs if completed
            documentos_urls = []
            if task_status == "completed" and task.get("file_path"):
                # The RPA should have uploaded to Azure
                # We'll store the Azure blob path
                documentos_urls = [task.get("file_path")]

            # Add/Update CNJ result in solicitacao
            await self.solicitacao_updater.add_cnj_result(
                solicitacao_id=solicitacao_id,
                cnj=cnj,
                status=portal_status,
                documentos_urls=documentos_urls,
                erro=task.get("error_message") if task_status == "failed" else None
            )

            # Check if all CNJs are processed
            solicitacao = await self.solicitacao_updater.get_solicitacao(solicitacao_id)

            if solicitacao:
                if solicitacao["cnjs_processados"] >= solicitacao["total_cnjs"]:
                    # All CNJs processed, update overall status
                    if solicitacao["cnjs_erro"] > 0:
                        final_status = SolicitacaoStatus.ERRO
                    elif solicitacao["cnjs_sucesso"] > 0:
                        final_status = SolicitacaoStatus.CONCLUIDO
                    else:
                        final_status = SolicitacaoStatus.DOCUMENTOS_NAO_ENCONTRADOS

                    await self.solicitacao_updater.update_status(
                        solicitacao_id,
                        final_status
                    )

                    logger.info(
                        f"✅ Solicitacao {solicitacao_id} completed: {final_status.value}"
                    )

        except Exception as e:
            logger.error(f"Error updating solicitacao from task: {e}")


# Main worker function
async def run_workers():
    """
    Run both workers: Solicitacao to Task converter and Task Status Monitor
    """
    db = db_manager.db

    converter = SolicitacaoToTaskConverter(db)
    monitor = TaskStatusMonitor(db)

    # Run both workers concurrently
    await asyncio.gather(
        converter.start_monitoring(),
        monitor.start_monitoring(),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("🚀 Starting Portal RPA Workers...")

    try:
        asyncio.run(run_workers())
    except KeyboardInterrupt:
        logger.info("👋 Workers stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        raise
