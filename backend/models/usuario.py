"""
User models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class Usuario(BaseModel):
    """User model"""

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    senha_hash: str
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "email": "joao@example.com",
                "ativo": True,
            }
        }


class UsuarioCreate(BaseModel):
    """User creation schema"""

    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "email": "joao@example.com",
                "senha": "senha123",
            }
        }


class UsuarioLogin(BaseModel):
    """User login schema"""

    email: EmailStr
    senha: str

    class Config:
        json_schema_extra = {
            "example": {"email": "joao@example.com", "senha": "senha123"}
        }


class UsuarioResponse(BaseModel):
    """User response schema (without password)"""

    id: str
    nome: str
    email: str
    ativo: bool
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "nome": "João Silva",
                "email": "joao@example.com",
                "ativo": True,
                "created_at": "2024-01-01T00:00:00",
            }
        }
