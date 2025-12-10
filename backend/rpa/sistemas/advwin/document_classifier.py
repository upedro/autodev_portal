"""
Classificador inteligente de documentos jurídicos
Analisa metadados e conteúdo de PDFs para classificar automaticamente

Autor: AutoDev
Data: 2025
"""

import os
import logging
from typing import Dict, Optional, List
from pathlib import Path
import re

logger = logging.getLogger(__name__)

# Tenta importar bibliotecas de PDF (instaladas opcionalmente)
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 não instalado. Extração de texto de PDF não disponível.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber não instalado. Extração avançada de PDF não disponível.")


class DocumentClassifier:
    """
    Classificador de documentos jurídicos baseado em:
    - Metadados (nome do arquivo, tipo)
    - Conteúdo do PDF (quando disponível)
    - Padrões e palavras-chave
    """

    # Categorias de documentos jurídicos
    CATEGORIAS = {
        "peticao_inicial": {
            "nome": "Petição Inicial",
            "palavras_chave": [
                "petição inicial", "exordial", "ação", "requer",
                "autor", "réu", "causa de pedir", "pedidos"
            ],
            "patterns": [
                r"peti[çc][ãa]o\s+inicial",
                r"exordial",
                r"distribui[çc][ãa]o"
            ]
        },
        "contestacao": {
            "nome": "Contestação",
            "palavras_chave": [
                "contestação", "defesa", "impugnação", "preliminares",
                "mérito", "nega", "contesta"
            ],
            "patterns": [
                r"contesta[çc][ãa]o",
                r"defesa",
                r"preliminar(es)?"
            ]
        },
        "sentenca": {
            "nome": "Sentença",
            "palavras_chave": [
                "sentença", "julgo", "procedente", "improcedente",
                "dispositivo", "fundamentação", "juiz"
            ],
            "patterns": [
                r"senten[çc]a",
                r"julgo\s+(im)?procedente",
                r"decisum"
            ]
        },
        "acordao": {
            "nome": "Acórdão",
            "palavras_chave": [
                "acórdão", "tribunal", "relator", "desembargador",
                "recurso", "voto", "ementa"
            ],
            "patterns": [
                r"ac[óo]rd[ãa]o",
                r"desembargador",
                r"tribunal"
            ]
        },
        "despacho": {
            "nome": "Despacho",
            "palavras_chave": [
                "despacho", "intime-se", "cumpra-se", "manifeste-se"
            ],
            "patterns": [
                r"despacho",
                r"intime-se",
                r"cumpra-se"
            ]
        },
        "decisao": {
            "nome": "Decisão Interlocutória",
            "palavras_chave": [
                "decisão", "defiro", "indefiro", "tutela", "liminar"
            ],
            "patterns": [
                r"decis[ãa]o",
                r"(in)?defiro",
                r"tutela"
            ]
        },
        "manifestacao": {
            "nome": "Manifestação",
            "palavras_chave": [
                "manifestação", "requer", "protesta", "vem"
            ],
            "patterns": [
                r"manifesta[çc][ãa]o",
                r"vem\s+.*\s+requerer"
            ]
        },
        "acordo": {
            "nome": "Acordo/Transação",
            "palavras_chave": [
                "acordo", "transação", "composição", "homologação"
            ],
            "patterns": [
                r"acordo",
                r"transa[çc][ãa]o",
                r"homologa[çc][ãa]o"
            ]
        },
        "procuracao": {
            "nome": "Procuração",
            "palavras_chave": [
                "procuração", "outorgante", "outorgado", "poderes"
            ],
            "patterns": [
                r"procura[çc][ãa]o",
                r"outorgante",
                r"poderes\s+para"
            ]
        },
        "certidao": {
            "nome": "Certidão",
            "palavras_chave": [
                "certidão", "certifico", "secretaria", "escrivão"
            ],
            "patterns": [
                r"certid[ãa]o",
                r"certifico\s+que"
            ]
        },
        "documento": {
            "nome": "Documento Geral",
            "palavras_chave": [],
            "patterns": []
        }
    }

    def __init__(self, use_ai: bool = False):
        """
        Inicializa o classificador

        Args:
            use_ai: Se True, tenta usar IA para classificação (requer API key)
        """
        self.use_ai = use_ai
        self.stats = {
            "total": 0,
            "com_texto": 0,
            "sem_texto": 0,
            "por_categoria": {}
        }

    def extrair_texto_pdf(self, caminho_pdf: str, max_paginas: int = 3) -> Optional[str]:
        """
        Extrai texto das primeiras páginas de um PDF

        Args:
            caminho_pdf: Caminho para o arquivo PDF
            max_paginas: Número máximo de páginas para extrair (padrão: 3)

        Returns:
            str: Texto extraído ou None se falhar
        """
        if not os.path.exists(caminho_pdf):
            logger.warning(f"Arquivo não encontrado: {caminho_pdf}")
            return None

        texto = None

        # Tenta usar pdfplumber primeiro (mais robusto)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(caminho_pdf) as pdf:
                    paginas_para_ler = min(len(pdf.pages), max_paginas)
                    texto = ""
                    for i in range(paginas_para_ler):
                        texto += pdf.pages[i].extract_text() or ""
                    return texto.strip() if texto else None
            except Exception as e:
                logger.debug(f"Erro ao extrair com pdfplumber: {e}")

        # Fallback para PyPDF2
        if PYPDF2_AVAILABLE and not texto:
            try:
                with open(caminho_pdf, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    paginas_para_ler = min(len(reader.pages), max_paginas)
                    texto = ""
                    for i in range(paginas_para_ler):
                        texto += reader.pages[i].extract_text() or ""
                    return texto.strip() if texto else None
            except Exception as e:
                logger.debug(f"Erro ao extrair com PyPDF2: {e}")

        return None

    def classificar_por_nome(self, nome_arquivo: str) -> Optional[str]:
        """
        Classifica documento baseado apenas no nome do arquivo

        Args:
            nome_arquivo: Nome do arquivo

        Returns:
            str: Categoria identificada ou None
        """
        nome_lower = nome_arquivo.lower()

        for categoria_id, categoria in self.CATEGORIAS.items():
            # Verifica padrões regex
            for pattern in categoria["patterns"]:
                if re.search(pattern, nome_lower, re.IGNORECASE):
                    return categoria_id

            # Verifica palavras-chave
            for palavra in categoria["palavras_chave"]:
                if palavra.lower() in nome_lower:
                    return categoria_id

        return None

    def classificar_por_conteudo(self, texto: str) -> Optional[str]:
        """
        Classifica documento baseado no conteúdo extraído

        Args:
            texto: Texto extraído do PDF

        Returns:
            str: Categoria identificada ou None
        """
        if not texto:
            return None

        texto_lower = texto.lower()
        scores = {}

        # Calcula score para cada categoria
        for categoria_id, categoria in self.CATEGORIAS.items():
            score = 0

            # Score por padrões regex
            for pattern in categoria["patterns"]:
                matches = len(re.findall(pattern, texto_lower, re.IGNORECASE))
                score += matches * 3  # Peso maior para padrões

            # Score por palavras-chave
            for palavra in categoria["palavras_chave"]:
                if palavra.lower() in texto_lower:
                    score += 1

            if score > 0:
                scores[categoria_id] = score

        # Retorna categoria com maior score
        if scores:
            return max(scores, key=scores.get)

        return None

    def classificar_documento(
        self,
        caminho_pdf: str,
        nome_arquivo: str,
        tipo_documento: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Classifica um documento usando múltiplas estratégias

        Args:
            caminho_pdf: Caminho do arquivo PDF
            nome_arquivo: Nome original do arquivo
            tipo_documento: Tipo já identificado (opcional)

        Returns:
            dict: Informações da classificação
                {
                    "categoria": str,
                    "nome_categoria": str,
                    "confianca": str (alta/media/baixa),
                    "metodo": str (nome/conteudo/tipo),
                    "texto_extraido": bool
                }
        """
        self.stats["total"] += 1

        resultado = {
            "categoria": "documento",  # Categoria padrão
            "nome_categoria": "Documento Geral",
            "confianca": "baixa",
            "metodo": "padrao",
            "texto_extraido": False
        }

        # Estratégia 1: Classificação por nome do arquivo
        categoria_nome = self.classificar_por_nome(nome_arquivo)
        if categoria_nome:
            resultado["categoria"] = categoria_nome
            resultado["nome_categoria"] = self.CATEGORIAS[categoria_nome]["nome"]
            resultado["confianca"] = "media"
            resultado["metodo"] = "nome"

        # Estratégia 2: Classificação por conteúdo do PDF
        try:
            texto = self.extrair_texto_pdf(caminho_pdf, max_paginas=2)
            if texto:
                self.stats["com_texto"] += 1
                resultado["texto_extraido"] = True

                categoria_conteudo = self.classificar_por_conteudo(texto)
                if categoria_conteudo:
                    resultado["categoria"] = categoria_conteudo
                    resultado["nome_categoria"] = self.CATEGORIAS[categoria_conteudo]["nome"]
                    resultado["confianca"] = "alta"
                    resultado["metodo"] = "conteudo"
            else:
                self.stats["sem_texto"] += 1
        except Exception as e:
            logger.debug(f"Erro ao classificar por conteúdo: {e}")
            self.stats["sem_texto"] += 1

        # Atualiza estatísticas
        cat = resultado["categoria"]
        self.stats["por_categoria"][cat] = self.stats["por_categoria"].get(cat, 0) + 1

        logger.debug(
            f"Classificação: {nome_arquivo} → "
            f"{resultado['nome_categoria']} "
            f"(confiança: {resultado['confianca']}, método: {resultado['metodo']})"
        )

        return resultado

    def classificar_lote(self, documentos: List[Dict]) -> List[Dict]:
        """
        Classifica um lote de documentos

        Args:
            documentos: Lista de dicionários com:
                {
                    "caminho_arquivo": str,
                    "nome_arquivo": str,
                    "tipo_documento": str (opcional)
                }

        Returns:
            list: Mesma lista com campo "classificacao" adicionado
        """
        logger.info(f"Classificando {len(documentos)} documento(s)...")

        for doc in documentos:
            classificacao = self.classificar_documento(
                caminho_pdf=doc.get("caminho_arquivo"),
                nome_arquivo=doc.get("nome_arquivo", ""),
                tipo_documento=doc.get("tipo_documento")
            )
            doc["classificacao"] = classificacao

        logger.info("Classificação concluída!")
        logger.info(f"Estatísticas:")
        logger.info(f"  - Total: {self.stats['total']}")
        logger.info(f"  - Com texto extraído: {self.stats['com_texto']}")
        logger.info(f"  - Sem texto: {self.stats['sem_texto']}")
        logger.info(f"  - Por categoria:")
        for cat, count in self.stats["por_categoria"].items():
            nome_cat = self.CATEGORIAS.get(cat, {}).get("nome", cat)
            logger.info(f"      • {nome_cat}: {count}")

        return documentos

    def get_stats(self) -> Dict:
        """Retorna estatísticas da classificação"""
        return self.stats.copy()


# Instância global
_classifier_instance: Optional[DocumentClassifier] = None


def get_classifier() -> DocumentClassifier:
    """Retorna instância singleton do classificador"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = DocumentClassifier()
    return _classifier_instance
