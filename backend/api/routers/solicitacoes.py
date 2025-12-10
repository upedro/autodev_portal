"""
Solicitações router
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from datetime import datetime
from bson import ObjectId

from database import get_database
from models import (
    SolicitacaoCreate,
    SolicitacaoResponse,
    SolicitacaoStatus,
    EventoTipo,
)
from utils.auth import get_current_user
from utils.excel_parser import parse_excel_cnjs, is_valid_cnj, clean_cnj
from workers.event_system import EventPublisher

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[SolicitacaoResponse])
async def list_solicitacoes(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    List user's solicitacoes

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (optional)
        current_user: Current authenticated user
        db: Database instance

    Returns:
        List of solicitacoes
    """
    try:
        # Build query
        query = {"user_id": str(current_user["_id"])}

        if status:
            query["status"] = status

        # Find solicitacoes
        cursor = (
            db.solicitacoes.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        solicitacoes = await cursor.to_list(length=limit)

        # Get client names for each solicitacao
        solicitacoes_response = []
        for sol in solicitacoes:
            # Get client name
            cliente = await db.clientes.find_one({"_id": ObjectId(sol["cliente_id"])})
            cliente_nome = cliente["nome"] if cliente else "Unknown"

            sol_response = SolicitacaoResponse(
                id=str(sol["_id"]),
                user_id=sol["user_id"],
                cliente_id=sol["cliente_id"],
                cliente_nome=cliente_nome,
                servico=sol["servico"],
                cnjs=sol["cnjs"],
                status=sol["status"],
                total_cnjs=sol["total_cnjs"],
                cnjs_processados=sol.get("cnjs_processados", 0),
                cnjs_sucesso=sol.get("cnjs_sucesso", 0),
                cnjs_erro=sol.get("cnjs_erro", 0),
                resultados=sol.get("resultados", []),
                created_at=sol["created_at"],
                updated_at=sol["updated_at"],
                iniciado_em=sol.get("iniciado_em"),
                concluido_em=sol.get("concluido_em"),
            )
            solicitacoes_response.append(sol_response)

        logger.info(f"Listed {len(solicitacoes_response)} solicitacoes")
        return solicitacoes_response

    except Exception as e:
        logger.error(f"Error listing solicitacoes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{solicitacao_id}", response_model=SolicitacaoResponse)
async def get_solicitacao(
    solicitacao_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get solicitacao by ID

    Args:
        solicitacao_id: Solicitacao ID
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Solicitacao information
    """
    try:
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

        # Get client name
        cliente = await db.clientes.find_one({"_id": ObjectId(sol["cliente_id"])})
        cliente_nome = cliente["nome"] if cliente else "Unknown"

        sol_response = SolicitacaoResponse(
            id=str(sol["_id"]),
            user_id=sol["user_id"],
            cliente_id=sol["cliente_id"],
            cliente_nome=cliente_nome,
            servico=sol["servico"],
            cnjs=sol["cnjs"],
            status=sol["status"],
            total_cnjs=sol["total_cnjs"],
            cnjs_processados=sol.get("cnjs_processados", 0),
            cnjs_sucesso=sol.get("cnjs_sucesso", 0),
            cnjs_erro=sol.get("cnjs_erro", 0),
            resultados=sol.get("resultados", []),
            created_at=sol["created_at"],
            updated_at=sol["updated_at"],
            iniciado_em=sol.get("iniciado_em"),
            concluido_em=sol.get("concluido_em"),
        )

        return sol_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting solicitacao: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/", response_model=SolicitacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitacao(
    solicitacao_data: SolicitacaoCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Create new solicitacao

    Args:
        solicitacao_data: Solicitacao creation data
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Created solicitacao
    """
    try:
        # Verify client exists
        cliente = await db.clientes.find_one(
            {"_id": ObjectId(solicitacao_data.cliente_id)}
        )

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        # Validate and clean CNJs
        valid_cnjs = []
        for cnj in solicitacao_data.cnjs:
            cleaned = clean_cnj(cnj)
            if is_valid_cnj(cleaned):
                valid_cnjs.append(cleaned)
            else:
                logger.warning(f"Invalid CNJ skipped: {cnj}")

        if not valid_cnjs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid CNJ numbers provided",
            )

        # Create solicitacao document
        sol_doc = {
            "user_id": str(current_user["_id"]),
            "cliente_id": solicitacao_data.cliente_id,
            "servico": solicitacao_data.servico,
            "cnjs": valid_cnjs,
            "status": SolicitacaoStatus.PENDENTE.value,
            "total_cnjs": len(valid_cnjs),
            "cnjs_processados": 0,
            "cnjs_sucesso": 0,
            "cnjs_erro": 0,
            "resultados": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Insert solicitacao
        result = await db.solicitacoes.insert_one(sol_doc)
        solicitacao_id = str(result.inserted_id)

        # Publish event for processing
        event_publisher = EventPublisher(db)
        await event_publisher.publish_event(
            tipo_evento=EventoTipo.NOVA_SOLICITACAO,
            solicitacao_id=solicitacao_id,
            metadata={
                "cliente_codigo": cliente["codigo"],
                "servico": solicitacao_data.servico,
                "total_cnjs": len(valid_cnjs),
            },
        )

        logger.info(f"Created solicitacao {solicitacao_id} with {len(valid_cnjs)} CNJs")

        # Prepare response
        sol_response = SolicitacaoResponse(
            id=solicitacao_id,
            user_id=sol_doc["user_id"],
            cliente_id=sol_doc["cliente_id"],
            cliente_nome=cliente["nome"],
            servico=sol_doc["servico"],
            cnjs=sol_doc["cnjs"],
            status=sol_doc["status"],
            total_cnjs=sol_doc["total_cnjs"],
            cnjs_processados=0,
            cnjs_sucesso=0,
            cnjs_erro=0,
            resultados=[],
            created_at=sol_doc["created_at"],
            updated_at=sol_doc["updated_at"],
        )

        return sol_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating solicitacao: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/upload", response_model=SolicitacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitacao_from_excel(
    file: UploadFile = File(...),
    cliente_id: str = Form(...),
    servico: str = Form(default="buscar_documentos"),
    current_user=Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Create solicitacao from Excel file upload

    Args:
        file: Excel file with CNJ numbers
        cliente_id: Client ID
        servico: Service type
        current_user: Current authenticated user
        db: Database instance

    Returns:
        Created solicitacao
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel files (.xlsx, .xls) are supported",
            )

        # Read file content
        file_content = await file.read()

        # Parse CNJs from Excel
        try:
            cnjs = await parse_excel_cnjs(file_content)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Create solicitacao using the parsed CNJs
        solicitacao_data = SolicitacaoCreate(
            cliente_id=cliente_id,
            servico=servico,
            cnjs=cnjs,
        )

        # Reuse the create_solicitacao logic
        return await create_solicitacao(solicitacao_data, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating solicitacao from Excel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
