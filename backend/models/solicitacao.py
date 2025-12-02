"""
Solicitação models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from .usuario import PyObjectId
from .status import SolicitacaoStatus


class ResultadoProcessamento(BaseModel):
    """Result of document processing for a single CNJ"""

    cnj: str
    status: str
    documentos_encontrados: int = 0
    documentos_urls: List[str] = Field(default_factory=list)
    erro: Optional[str] = None
    processado_em: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "cnj": "0001234-56.2024.8.00.0000",
                "status": "concluido",
                "documentos_encontrados": 3,
                "documentos_urls": [
                    "https://storage.azure.com/doc1.pdf",
                    "https://storage.azure.com/doc2.pdf",
                ],
                "processado_em": "2024-01-01T10:30:00",
            }
        }


class Solicitacao(BaseModel):
    """Request model for document fetching service"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str  # ID of the user who created the request
    cliente_id: str  # ID of the client (company)
    servico: str = "buscar_documentos"  # Service type (only one for MVP)
    cnjs: List[str]  # List of CNJ process numbers
    status: SolicitacaoStatus = SolicitacaoStatus.PENDENTE
    resultados: List[ResultadoProcessamento] = Field(default_factory=list)
    total_cnjs: int
    cnjs_processados: int = 0
    cnjs_sucesso: int = 0
    cnjs_erro: int = 0
    erro_geral: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    iniciado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "cliente_id": "507f1f77bcf86cd799439012",
                "servico": "buscar_documentos",
                "cnjs": ["0001234-56.2024.8.00.0000", "0001234-56.2024.8.00.0001"],
                "status": "pendente",
                "total_cnjs": 2,
            }
        }


class SolicitacaoCreate(BaseModel):
    """Schema for creating a new request"""

    cliente_id: str
    servico: str = "buscar_documentos"
    cnjs: List[str] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "cliente_id": "507f1f77bcf86cd799439012",
                "servico": "buscar_documentos",
                "cnjs": ["0001234-56.2024.8.00.0000", "0001234-56.2024.8.00.0001"],
            }
        }


class SolicitacaoResponse(BaseModel):
    """Response schema for solicitação"""

    id: str
    user_id: str
    cliente_id: str
    cliente_nome: Optional[str] = None  # Populated via join
    servico: str
    cnjs: List[str]
    status: SolicitacaoStatus
    total_cnjs: int
    cnjs_processados: int
    cnjs_sucesso: int
    cnjs_erro: int
    resultados: List[ResultadoProcessamento]
    created_at: datetime
    updated_at: datetime
    iniciado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439013",
                "user_id": "507f1f77bcf86cd799439011",
                "cliente_id": "507f1f77bcf86cd799439012",
                "cliente_nome": "Agibank",
                "servico": "buscar_documentos",
                "cnjs": ["0001234-56.2024.8.00.0000"],
                "status": "concluido",
                "total_cnjs": 1,
                "cnjs_processados": 1,
                "cnjs_sucesso": 1,
                "cnjs_erro": 0,
                "resultados": [
                    {
                        "cnj": "0001234-56.2024.8.00.0000",
                        "status": "concluido",
                        "documentos_encontrados": 3,
                    }
                ],
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T10:30:00",
            }
        }
