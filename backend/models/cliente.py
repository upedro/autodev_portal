"""
Cliente models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .usuario import PyObjectId


class Cliente(BaseModel):
    """Client model - companies/organizations that have RPA services"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=2, max_length=50)  # Unique identifier
    ativo: bool = True
    descricao: Optional[str] = None
    config_rpa: Optional[Dict[str, Any]] = Field(
        default_factory=dict
    )  # RPA-specific config
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "nome": "Agibank",
                "codigo": "agibank",
                "ativo": True,
                "descricao": "Banco Agibank - Serviços jurídicos",
                "config_rpa": {
                    "portal_url": "https://portal.agibank.com.br",
                    "timeout": 30,
                },
            }
        }


class ClienteCreate(BaseModel):
    """Client creation schema"""

    nome: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=2, max_length=50)
    ativo: bool = True
    descricao: Optional[str] = None
    config_rpa: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Agibank",
                "codigo": "agibank",
                "ativo": True,
                "descricao": "Banco Agibank - Serviços jurídicos",
                "config_rpa": {"portal_url": "https://portal.agibank.com.br"},
            }
        }


class ClienteResponse(BaseModel):
    """Client response schema"""

    id: str
    nome: str
    codigo: str
    ativo: bool
    descricao: Optional[str] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "nome": "Agibank",
                "codigo": "agibank",
                "ativo": True,
                "descricao": "Banco Agibank - Serviços jurídicos",
                "created_at": "2024-01-01T00:00:00",
            }
        }
