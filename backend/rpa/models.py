"""
Modelos de dados para o projeto RPA
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class TaskStatus(str, Enum):
    """Status possíveis de uma tarefa"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PyObjectId(ObjectId):
    """Wrapper para ObjectId do MongoDB funcionar com Pydantic"""
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


class DocumentInfo(BaseModel):
    """Modelo de informações de um documento baixado"""
    numero_linha: int = Field(..., description="Número da linha na tabela")
    nome_arquivo_original: str = Field(..., description="Nome original do arquivo")
    tipo_documento: str = Field(..., description="Tipo do documento extraído da tabela")
    nome_arquivo_final: str = Field(..., description="Nome final do arquivo renomeado")
    blob_url: str = Field(..., description="URL do arquivo no Azure Blob Storage")
    pasta: Optional[str] = Field(None, description="Pasta/folder no ADVWin")
    codigo_pasta: Optional[str] = Field(None, description="Código da pasta no ADVWin (codigo_comp)")


class TaskBase(BaseModel):
    """Modelo base da tarefa"""
    process_number: str = Field(..., description="Número do processo (CNJ)")
    client_name: str = Field(..., description="Nome do cliente/robô")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Status da tarefa")
    file_path: Optional[str] = Field(None, description="URL/caminho do primeiro arquivo no Azure (compatibilidade)")
    documents: Optional[list[DocumentInfo]] = Field(None, description="Lista de todos os documentos baixados")
    total_documents: Optional[int] = Field(None, description="Total de documentos baixados")
    # Campos para integração com ADVWin
    pasta: Optional[str] = Field(None, description="Pasta/folder no ADVWin")
    codigo_pasta: Optional[str] = Field(None, description="Código da pasta no ADVWin (codigo_comp)")


class TaskCreate(TaskBase):
    """Modelo para criação de tarefa"""
    pass


class TaskInDB(TaskBase):
    """Modelo da tarefa no banco de dados"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class TaskResponse(BaseModel):
    """Modelo de resposta da API"""
    id: str
    process_number: str
    client_name: str
    status: TaskStatus
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskStatusResponse(BaseModel):
    """Modelo de resposta do status de uma tarefa"""
    process_number: str
    status: TaskStatus
    file_path: Optional[str] = None
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UploadResponse(BaseModel):
    """Modelo de resposta do upload"""
    message: str
    tasks_created: int
    client_name: str
