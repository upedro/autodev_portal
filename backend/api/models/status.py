"""
Status constants for the document request workflow
Simplified version adapted from RPA project
"""
from enum import Enum


class SolicitacaoStatus(str, Enum):
    """Status for document request workflow"""

    # Initial states
    PENDENTE = "pendente"                    # Request created, waiting to be processed
    EM_EXECUCAO = "em_execucao"             # Worker is processing the request

    # Success states
    CONCLUIDO = "concluido"                  # Documents found and uploaded successfully

    # Error states
    ERRO = "erro"                            # Unrecoverable error
    DOCUMENTOS_NAO_ENCONTRADOS = "documentos_nao_encontrados"  # No documents found

    # Additional states for future use
    AGUARDANDO_RECHECK = "aguardando_recheck"  # Waiting for recheck after document request
    CANCELADO = "cancelado"                    # Request cancelled by user


class EventoTipo(str, Enum):
    """Event types for event-driven architecture"""

    NOVA_SOLICITACAO = "NOVA_SOLICITACAO"
    BUSCAR_DOCUMENTOS = "BUSCAR_DOCUMENTOS"
    DOCUMENTOS_ENCONTRADOS = "DOCUMENTOS_ENCONTRADOS"
    DOCUMENTOS_NAO_ENCONTRADOS = "DOCUMENTOS_NAO_ENCONTRADOS"
    UPLOAD_CONCLUIDO = "UPLOAD_CONCLUIDO"
    ERRO_PROCESSAMENTO = "ERRO_PROCESSAMENTO"
    SOLICITACAO_CONCLUIDA = "SOLICITACAO_CONCLUIDA"
