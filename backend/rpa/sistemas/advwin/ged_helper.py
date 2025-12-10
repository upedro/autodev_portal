"""
Helper para facilitar o envio de documentos GED para ADVWin
após o download pelos RPAs

Autor: AutoDev
Data: 2025
"""

import logging
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from .advwin_api import ADVWinAPI
from .document_classifier import get_classifier

logger = logging.getLogger(__name__)


def sanitizar_nome_categoria(categoria: str) -> str:
    """
    Sanitiza o nome da categoria para uso em nome de arquivo

    Args:
        categoria: Nome da categoria (ex: "Petição Inicial")

    Returns:
        str: Nome sanitizado (ex: "PeticaoInicial")
    """
    # Remove acentos e caracteres especiais
    nome = categoria

    # Mapa de substituições de acentos
    acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'É': 'E', 'Ê': 'E',
        'Í': 'I',
        'Ó': 'O', 'Õ': 'O', 'Ô': 'O',
        'Ú': 'U', 'Ü': 'U',
        'Ç': 'C'
    }

    for acento, substituto in acentos.items():
        nome = nome.replace(acento, substituto)

    # Remove espaços, barras e caracteres especiais
    nome = re.sub(r'[^a-zA-Z0-9]', '', nome)

    return nome


class GEDHelper:
    """
    Helper para envio de documentos GED para ADVWin
    Simplifica a integração com os workers RPA
    """

    def __init__(self, usar_classificador: bool = True):
        """
        Inicializa o helper com cliente ADVWin API

        Args:
            usar_classificador: Se True, classifica automaticamente documentos
        """
        self.api: Optional[ADVWinAPI] = None
        self._authenticated = False
        self.usar_classificador = usar_classificador
        self.classifier = get_classifier() if usar_classificador else None

    def _ensure_authentication(self) -> bool:
        """
        Garante que o cliente está autenticado

        Returns:
            bool: True se autenticado, False caso contrário
        """
        if self._authenticated and self.api and self.api.token:
            return True

        try:
            logger.info("Inicializando cliente ADVWin API...")
            self.api = ADVWinAPI()

            logger.info("Autenticando na API ADVWin...")
            if self.api.login():
                self._authenticated = True
                logger.info("✓ Autenticação realizada com sucesso")
                return True
            else:
                logger.error("✗ Falha na autenticação ADVWin")
                return False

        except Exception as e:
            logger.error(f"Erro ao autenticar na API ADVWin: {e}")
            return False

    def enviar_documentos_ged(
        self,
        documentos: List[Dict[str, Any]],
        numero_processo: str,
        tabela_or: str = "Pastas",
        codigo_or: Optional[str] = None,
        id_or: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia uma lista de documentos para o GED do ADVWin

        Args:
            documentos: Lista de dicionários com informações dos documentos
                Formato esperado:
                [
                    {
                        "caminho_arquivo": "/path/to/file.pdf",
                        "nome_arquivo_final": "123456_Documento.pdf",
                        "tipo_documento": "Petição Inicial",
                        "numero_linha": 1
                    }
                ]
            numero_processo: Número do processo (será usado como código se codigo_or não for fornecido)
            tabela_or: Tabela de destino no ADVWin (Pastas, Agenda, Debite, Clientes)
            codigo_or: Código de referência (se None, usa numero_processo)
            id_or: ID para movimentação (opcional)

        Returns:
            dict: Resumo do envio com estatísticas e detalhes
        """
        logger.info("="*80)
        logger.info("INICIANDO ENVIO DE DOCUMENTOS PARA ADVWIN GED")
        logger.info("="*80)
        logger.info(f"Processo: {numero_processo}")
        logger.info(f"Tabela: {tabela_or}")
        logger.info(f"Total de documentos: {len(documentos)}")
        logger.info("="*80)

        # Usa o número do processo como código se não fornecido
        if not codigo_or:
            # Remove pontos, traços e espaços do número do processo
            codigo_or = numero_processo.replace(".", "").replace("-", "").replace(" ", "")
            logger.info(f"Código gerado automaticamente: {codigo_or}")

        # Garante autenticação
        if not self._ensure_authentication():
            return {
                "sucesso": False,
                "erro": "Falha na autenticação com ADVWin API",
                "total": len(documentos),
                "enviados": 0,
                "falhas": len(documentos)
            }

        # Classifica documentos se habilitado
        if self.usar_classificador and self.classifier:
            logger.info("Classificando documentos automaticamente...")
            documentos = self.classifier.classificar_lote(documentos)

        # Prepara lista de arquivos para envio
        arquivos_para_envio = []

        for doc in documentos:
            # Extrai informações do documento
            caminho_original = doc.get("caminho_arquivo")
            nome_final = doc.get("nome_arquivo_final", "documento.pdf")
            tipo_doc = doc.get("tipo_documento", "Documento")
            numero_linha = doc.get("numero_linha", 0)

            # Informações de classificação (se disponível)
            classificacao = doc.get("classificacao", {})
            categoria = classificacao.get("nome_categoria", tipo_doc)
            confianca = classificacao.get("confianca", "desconhecida")

            if not caminho_original:
                logger.warning(f"Documento sem caminho_arquivo: {doc}")
                continue

            # Renomeia arquivo com categoria
            # Formato: numero_processo_CategoriaSanitizada.pdf
            # Exemplo: 50130622420258215001_PeticaoInicial.pdf
            path_obj = Path(caminho_original)
            categoria_sanitizada = sanitizar_nome_categoria(categoria)

            # Extrai número do processo do nome do arquivo original
            # Assume que o nome começa com número do processo
            nome_original = path_obj.stem
            match = re.match(r'^(\d+)', nome_original)
            numero_processo_limpo = match.group(1) if match else numero_processo.replace(".", "").replace("-", "").replace(" ", "")

            # Novo nome: numero_processo_Categoria.pdf
            novo_nome = f"{numero_processo_limpo}_{categoria_sanitizada}.pdf"
            novo_caminho = path_obj.parent / novo_nome

            # Copia arquivo com novo nome (mantém original)
            try:
                shutil.copy2(caminho_original, novo_caminho)
                caminho_para_envio = str(novo_caminho)
                logger.debug(f"Arquivo renomeado: {path_obj.name} → {novo_nome}")
            except Exception as e:
                logger.warning(f"Erro ao renomear arquivo: {e}. Usando nome original.")
                caminho_para_envio = caminho_original
                novo_nome = nome_final

            # Monta a descrição do documento com categoria classificada
            descricao = f"{categoria} - Documentos baixados via RPA Autodev"
            if len(descricao) > 250:
                descricao = descricao[:247] + "..."

            # Monta observação com informações de classificação
            observacao_parts = [
                f"Documento baixado automaticamente pelo RPA FluxLaw",
                f"Arquivo original: {doc.get('nome_arquivo', nome_final)}",
                f"Nome final: {novo_nome}",
                f"Linha: {numero_linha}",
                f"Tipo original: {tipo_doc}"
            ]

            # Adiciona informações de classificação
            if classificacao:
                metodo = classificacao.get("metodo", "desconhecido")
                observacao_parts.append(f"Classificação: {categoria} (método: {metodo}, confiança: {confianca})")

            observacao = "\n".join(observacao_parts)

            arquivos_para_envio.append({
                "caminho": caminho_para_envio,
                "descricao": descricao,
                "observacao": observacao,
                "metadata": doc  # Preserva metadados originais
            })

        if not arquivos_para_envio:
            logger.error("Nenhum arquivo válido para envio!")
            return {
                "sucesso": False,
                "erro": "Nenhum arquivo válido para envio",
                "total": len(documentos),
                "enviados": 0,
                "falhas": len(documentos)
            }

        # Envia os documentos usando a API
        logger.info(f"Enviando {len(arquivos_para_envio)} documento(s)...")

        resultado = self.api.upload_multiplos_ged(
            arquivos=arquivos_para_envio,
            tabela_or=tabela_or,
            codigo_or=codigo_or,
            id_or=id_or
        )

        # Adiciona informações do processo ao resultado
        resultado["numero_processo"] = numero_processo
        resultado["tabela_or"] = tabela_or
        resultado["codigo_or"] = codigo_or

        logger.info("="*80)
        logger.info("RESUMO DO ENVIO PARA ADVWIN GED")
        logger.info("="*80)
        logger.info(f"Total: {resultado['total']}")
        logger.info(f"✓ Sucesso: {resultado['sucesso']}")
        logger.info(f"✗ Falha: {resultado['falha']}")
        logger.info("="*80)

        return resultado

    def enviar_documento_unico_ged(
        self,
        caminho_arquivo: str,
        numero_processo: str,
        tipo_documento: str = "Documento",
        tabela_or: str = "Pastas",
        codigo_or: Optional[str] = None,
        id_or: Optional[str] = None,
        observacao_extra: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia um único documento para o GED do ADVWin

        Args:
            caminho_arquivo: Caminho completo do arquivo
            numero_processo: Número do processo
            tipo_documento: Tipo do documento
            tabela_or: Tabela de destino
            codigo_or: Código de referência (se None, usa numero_processo)
            id_or: ID para movimentação (opcional)
            observacao_extra: Observação adicional (opcional)

        Returns:
            dict: Resultado do envio
        """
        # Usa o número do processo como código se não fornecido
        if not codigo_or:
            codigo_or = numero_processo.replace(".", "").replace("-", "").replace(" ", "")

        # Garante autenticação
        if not self._ensure_authentication():
            return {
                "sucesso": False,
                "erro": "Falha na autenticação com ADVWin API"
            }

        # Monta descrição
        descricao = "Documentos baixados via RPA Autodev e inserido via API."
        if len(descricao) > 250:
            descricao = descricao[:247] + "..."

        # Monta observação
        observacao = (
            f"Documento enviado automaticamente pelo RPA FluxLaw\n"
            f"Tipo: {tipo_documento}\n"
            f"Processo: {numero_processo}"
        )

        if observacao_extra:
            observacao += f"\n\n{observacao_extra}"

        # Envia o documento
        resultado = self.api.upload_ged(
            file_path=caminho_arquivo,
            tabela_or=tabela_or,
            codigo_or=codigo_or,
            descricao=descricao,
            id_or=id_or,
            observacao=observacao
        )

        return resultado


# Instância global do helper para reutilização
_ged_helper_instance: Optional[GEDHelper] = None


def get_ged_helper() -> GEDHelper:
    """
    Retorna uma instância singleton do GEDHelper

    Returns:
        GEDHelper: Instância do helper
    """
    global _ged_helper_instance

    if _ged_helper_instance is None:
        _ged_helper_instance = GEDHelper()

    return _ged_helper_instance
