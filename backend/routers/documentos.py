"""
Documentos router - Generate download URLs for completed documents
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from database import get_database
from models import SolicitacaoStatus
from utils.auth import get_current_user
from workers.azure_storage import AzureStorageHandler
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{solicitacao_id}")
async def get_documentos(
    solicitacao_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get download URLs for documents of a solicitacao

    Args:
        solicitacao_id: Solicitacao ID
        current_user: Current authenticated user
        db: Database instance

    Returns:
        List of documents with download URLs
    """
    try:
        # Get solicitacao
        sol = await db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})

        if not sol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitacao not found",
            )

        # Verify user owns this solicitacao
        if sol["user_id"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Check if solicitacao has results
        if not sol.get("resultados"):
            return {
                "solicitacao_id": solicitacao_id,
                "status": sol["status"],
                "documentos": [],
                "message": "No documents available yet",
            }

        # Get client info
        cliente = await db.clientes.find_one({"_id": ObjectId(sol["cliente_id"])})

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        # Initialize Azure Storage handler
        try:
            azure_handler = AzureStorageHandler(
                connection_string=settings.azure_storage_connection_string,
                container_name=settings.azure_storage_container or "portal-documentos",
            )
        except Exception as e:
            logger.error(f"Error initializing Azure Storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage service unavailable",
            )

        # Generate download URLs for each CNJ with documents
        documentos_response = []

        for resultado in sol["resultados"]:
            cnj = resultado["cnj"]

            # Only process successful results with documents
            if resultado.get("status") == "concluido" and resultado.get("documentos_encontrados", 0) > 0:
                # List files for this CNJ
                try:
                    files = azure_handler.list_files_by_cnj(
                        cliente_codigo=cliente["codigo"],
                        cnj=cnj
                    )

                    # Generate SAS URLs for each file
                    cnj_documentos = []
                    for file_info in files:
                        sas_url = azure_handler.generate_sas_url(
                            blob_path=file_info["name"],
                            expiry_hours=24  # URLs expire in 24 hours
                        )

                        if sas_url:
                            cnj_documentos.append({
                                "filename": file_info["name"].split("/")[-1],  # Get just filename
                                "size_bytes": file_info["size"],
                                "download_url": sas_url,
                                "expires_in_hours": 24,
                            })

                    if cnj_documentos:
                        documentos_response.append({
                            "cnj": cnj,
                            "total_documentos": len(cnj_documentos),
                            "documentos": cnj_documentos,
                        })

                except Exception as e:
                    logger.warning(f"Error getting documents for CNJ {cnj}: {e}")
                    continue

        return {
            "solicitacao_id": solicitacao_id,
            "status": sol["status"],
            "cliente_nome": cliente["nome"],
            "total_cnjs_com_documentos": len(documentos_response),
            "cnjs": documentos_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{solicitacao_id}/{cnj}")
async def get_documentos_by_cnj(
    solicitacao_id: str,
    cnj: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get download URLs for documents of a specific CNJ in a solicitacao

    Args:
        solicitacao_id: Solicitacao ID
        cnj: CNJ process number
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Documents for the specified CNJ
    """
    try:
        # Get solicitacao
        sol = await db.solicitacoes.find_one({"_id": ObjectId(solicitacao_id)})

        if not sol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitacao not found",
            )

        # Verify user owns this solicitacao
        if sol["user_id"] != str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Find result for this CNJ
        resultado = next(
            (r for r in sol.get("resultados", []) if r["cnj"] == cnj),
            None
        )

        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CNJ {cnj} not found in this solicitacao",
            )

        # Get client info
        cliente = await db.clientes.find_one({"_id": ObjectId(sol["cliente_id"])})

        # Initialize Azure Storage
        azure_handler = AzureStorageHandler(
            connection_string=settings.azure_storage_connection_string,
            container_name=settings.azure_storage_container or "portal-documentos",
        )

        # Get files for this CNJ
        files = azure_handler.list_files_by_cnj(
            cliente_codigo=cliente["codigo"],
            cnj=cnj
        )

        # Generate SAS URLs
        documentos = []
        for file_info in files:
            sas_url = azure_handler.generate_sas_url(
                blob_path=file_info["name"],
                expiry_hours=24
            )

            if sas_url:
                documentos.append({
                    "filename": file_info["name"].split("/")[-1],
                    "size_bytes": file_info["size"],
                    "download_url": sas_url,
                    "expires_in_hours": 24,
                    "last_modified": file_info["last_modified"],
                })

        return {
            "cnj": cnj,
            "status": resultado.get("status"),
            "total_documentos": len(documentos),
            "documentos": documentos,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents for CNJ: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
