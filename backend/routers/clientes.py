"""
Clientes router
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_database
from models import ClienteResponse
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ClienteResponse])
async def list_clientes(
    ativo_apenas: bool = True,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    List available clients

    Args:
        ativo_apenas: Return only active clients (default: True)
        current_user: Current authenticated user
        db: Database instance

    Returns:
        List of clients
    """
    try:
        # Build query
        query = {}
        if ativo_apenas:
            query["ativo"] = True

        # Find clients
        cursor = db.clientes.find(query).sort("nome", 1)
        clientes = await cursor.to_list(length=None)

        # Convert to response model
        clientes_response = [
            ClienteResponse(
                id=str(cliente["_id"]),
                nome=cliente["nome"],
                codigo=cliente["codigo"],
                ativo=cliente.get("ativo", True),
                descricao=cliente.get("descricao"),
                created_at=cliente.get("created_at"),
            )
            for cliente in clientes
        ]

        logger.info(f"Listed {len(clientes_response)} clients")
        return clientes_response

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get client by ID

    Args:
        cliente_id: Client ID
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Client information
    """
    try:
        from bson import ObjectId

        cliente = await db.clientes.find_one({"_id": ObjectId(cliente_id)})

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        cliente_response = ClienteResponse(
            id=str(cliente["_id"]),
            nome=cliente["nome"],
            codigo=cliente["codigo"],
            ativo=cliente.get("ativo", True),
            descricao=cliente.get("descricao"),
            created_at=cliente.get("created_at"),
        )

        return cliente_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
