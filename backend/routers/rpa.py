"""
RPA endpoints - For RPA system to consume and update tasks
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

from database import get_database
from models import SolicitacaoStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================


class TaskRPA(BaseModel):
    """Task model for RPA consumption"""

    id: str
    process_number: str
    client_name: str
    status: str
    solicitacao_id: str
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "690dc9d4538b6f438726e053",
                "process_number": "0001234-56.2024.8.00.0000",
                "client_name": "agibank",
                "status": "pending",
                "solicitacao_id": "690dc9d4538b6f438726e053",
                "created_at": "2025-11-07T10:00:00",
            }
        }


class TaskUpdateRequest(BaseModel):
    """Request to update task status"""

    status: str = Field(..., description="New status: processing, completed, failed")
    documentos_encontrados: Optional[int] = Field(
        default=0, description="Number of documents found"
    )
    documentos_urls: Optional[List[str]] = Field(
        default_factory=list, description="List of Azure blob URLs"
    )
    erro: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "documentos_encontrados": 5,
                "documentos_urls": [
                    "documentos/agibank/0001234-56_2024_8_00_0000/doc1.pdf"
                ],
            }
        }


# ==================== Endpoints ====================


@router.get("/tasks/pending", response_model=List[TaskRPA])
async def get_pending_tasks(
    client_name: Optional[str] = None,
    limit: int = 50,
    db=Depends(get_database),
):
    """
    Get pending tasks for RPA to process

    Args:
        client_name: Filter by client (optional)
        limit: Maximum number of tasks to return
        db: Database instance

    Returns:
        List of pending tasks
    """
    try:
        # Build query
        query = {"status": SolicitacaoStatus.PENDENTE.value}

        if client_name:
            query["cliente_id"] = client_name

        # Find pending solicitacoes
        cursor = (
            db.solicitacoes.find(query)
            .sort("created_at", 1)  # FIFO
            .limit(limit)
        )

        solicitacoes = await cursor.to_list(length=limit)

        # Convert to tasks (one task per CNJ)
        tasks = []
        for sol in solicitacoes:
            # Get client info
            cliente = await db.clientes.find_one({"_id": ObjectId(sol["cliente_id"])})

            if not cliente:
                continue

            # Create a task for each CNJ
            for cnj in sol["cnjs"]:
                # Check if this CNJ already has a result
                existing_result = next(
                    (r for r in sol.get("resultados", []) if r["cnj"] == cnj),
                    None
                )

                # Only return if not yet processed
                if not existing_result:
                    task = TaskRPA(
                        id=f"{sol['_id']}_{cnj}",  # Composite ID
                        process_number=cnj,
                        client_name=cliente["codigo"],
                        status="pending",
                        solicitacao_id=str(sol["_id"]),
                        created_at=sol["created_at"].isoformat(),
                    )
                    tasks.append(task)

        logger.info(f"Returning {len(tasks)} pending tasks for RPA")
        return tasks

    except Exception as e:
        logger.error(f"Error getting pending tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/tasks/{solicitacao_id}/{cnj}")
async def update_task_status(
    solicitacao_id: str,
    cnj: str,
    update_data: TaskUpdateRequest,
    db=Depends(get_database),
):
    """
    Update task status (called by RPA when processing completes)

    Args:
        solicitacao_id: Solicitacao ID
        cnj: CNJ process number
        update_data: Status update data
        db: Database instance

    Returns:
        Updated task status
    """
    try:
        # Get solicitacao
        sol = await db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})

        if not sol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitacao not found",
            )

        # Check if CNJ exists in solicitacao
        if cnj not in sol["cnjs"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CNJ {cnj} not found in this solicitacao",
            )

        # Create or update result for this CNJ
        resultado = {
            "cnj": cnj,
            "status": update_data.status,
            "documentos_encontrados": update_data.documentos_encontrados,
            "documentos_urls": update_data.documentos_urls,
            "erro": update_data.erro,
            "processado_em": datetime.utcnow(),
        }

        # Check if result already exists
        existing_idx = next(
            (i for i, r in enumerate(sol.get("resultados", []))
             if r["cnj"] == cnj),
            None
        )

        if existing_idx is not None:
            # Update existing result
            await db.solicitacoes.update_one(
                {"_id": ObjectId(solicitacao_id)},
                {
                    "$set": {
                        f"resultados.{existing_idx}": resultado,
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
        else:
            # Add new result
            await db.solicitacoes.update_one(
                {"_id": ObjectId(solicitacao_id)},
                {
                    "$push": {"resultados": resultado},
                    "$inc": {
                        "cnjs_processados": 1,
                        "cnjs_sucesso": 1 if update_data.status == "completed" else 0,
                        "cnjs_erro": 1 if update_data.status == "failed" else 0,
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                }
            )

        # Check if all CNJs are processed
        updated_sol = await db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})

        if updated_sol["cnjs_processados"] >= updated_sol["total_cnjs"]:
            # All CNJs processed, update overall status
            if updated_sol["cnjs_erro"] == updated_sol["total_cnjs"]:
                # All failed
                final_status = SolicitacaoStatus.ERRO
            elif updated_sol["cnjs_sucesso"] > 0:
                # At least one success
                final_status = SolicitacaoStatus.CONCLUIDO
            else:
                # No documents found
                final_status = SolicitacaoStatus.DOCUMENTOS_NAO_ENCONTRADOS

            await db.solicitacoes.update_one(
                {"_id": ObjectId(solicitacao_id)},
                {
                    "$set": {
                        "status": final_status.value,
                        "concluido_em": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                }
            )

            logger.info(
                f"Solicitacao {solicitacao_id} completed with status: {final_status.value}"
            )

        logger.info(f"Task updated: {cnj} → {update_data.status}")

        return {
            "success": True,
            "solicitacao_id": solicitacao_id,
            "cnj": cnj,
            "status": update_data.status,
            "message": "Task status updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/tasks/{solicitacao_id}/{cnj}/start")
async def start_task_processing(
    solicitacao_id: str,
    cnj: str,
    db=Depends(get_database),
):
    """
    Mark a task as processing (RPA started working on it)

    Args:
        solicitacao_id: Solicitacao ID
        cnj: CNJ process number
        db: Database instance

    Returns:
        Success confirmation
    """
    try:
        # Update solicitacao status to EM_EXECUCAO if still PENDENTE
        await db.solicitacoes.update_one(
            {
                "_id": ObjectId(solicitacao_id),
                "status": SolicitacaoStatus.PENDENTE.value,
            },
            {
                "$set": {
                    "status": SolicitacaoStatus.EM_EXECUCAO.value,
                    "iniciado_em": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        logger.info(f"Task started: {cnj} in solicitacao {solicitacao_id}")

        return {
            "success": True,
            "solicitacao_id": solicitacao_id,
            "cnj": cnj,
            "message": "Task marked as processing",
        }

    except Exception as e:
        logger.error(f"Error starting task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/tasks/stats")
async def get_tasks_stats(db=Depends(get_database)):
    """
    Get statistics about tasks

    Returns:
        Task statistics
    """
    try:
        total = await db.solicitacoes.count_documents({})
        pendente = await db.solicitacoes.count_documents(
            {"status": SolicitacaoStatus.PENDENTE.value}
        )
        em_execucao = await db.solicitacoes.count_documents(
            {"status": SolicitacaoStatus.EM_EXECUCAO.value}
        )
        concluido = await db.solicitacoes.count_documents(
            {"status": SolicitacaoStatus.CONCLUIDO.value}
        )
        erro = await db.solicitacoes.count_documents(
            {"status": SolicitacaoStatus.ERRO.value}
        )

        # Count total CNJs
        pipeline = [
            {"$group": {
                "_id": None,
                "total_cnjs": {"$sum": "$total_cnjs"},
                "cnjs_processados": {"$sum": "$cnjs_processados"},
                "cnjs_sucesso": {"$sum": "$cnjs_sucesso"},
                "cnjs_erro": {"$sum": "$cnjs_erro"},
            }}
        ]

        result = await db.solicitacoes.aggregate(pipeline).to_list(length=1)
        cnj_stats = result[0] if result else {
            "total_cnjs": 0,
            "cnjs_processados": 0,
            "cnjs_sucesso": 0,
            "cnjs_erro": 0,
        }

        return {
            "solicitacoes": {
                "total": total,
                "pendente": pendente,
                "em_execucao": em_execucao,
                "concluido": concluido,
                "erro": erro,
            },
            "cnjs": {
                "total": cnj_stats["total_cnjs"],
                "processados": cnj_stats["cnjs_processados"],
                "sucesso": cnj_stats["cnjs_sucesso"],
                "erro": cnj_stats["cnjs_erro"],
                "pendentes": cnj_stats["total_cnjs"] - cnj_stats["cnjs_processados"],
            },
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
