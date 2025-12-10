"""
Módulo de integração com ADVWin API

Componentes:
- ADVWinAPI: Cliente para API do ADVWin
- GEDHelper: Helper para envio de documentos GED
- DocumentClassifier: Classificador inteligente de documentos
"""

from .advwin_api import ADVWinAPI
from .ged_helper import GEDHelper, get_ged_helper
from .document_classifier import DocumentClassifier, get_classifier

__all__ = [
    'ADVWinAPI',
    'GEDHelper',
    'get_ged_helper',
    'DocumentClassifier',
    'get_classifier'
]
