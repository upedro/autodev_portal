#!/usr/bin/env python
"""
Script de teste para o classificador de documentos
Testa a classificação automática de PDFs baseada em metadados e conteúdo

Autor: AutoDev
Data: 2025
"""

import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sistemas.advwin.document_classifier import DocumentClassifier, get_classifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_classificador_simples():
    """Testa classificação baseada apenas em nomes de arquivo"""
    logger.info("="*80)
    logger.info("TESTE 1: Classificação por Nome de Arquivo")
    logger.info("="*80)

    classifier = DocumentClassifier()

    # Testes com nomes de arquivo comuns
    testes = [
        "peticao_inicial.pdf",
        "contestacao_reu.pdf",
        "sentenca_1grau.pdf",
        "acordao_tjsp.pdf",
        "despacho_juiz.pdf",
        "decisao_liminar.pdf",
        "manifestacao_autor.pdf",
        "procuracao_poderes.pdf",
        "certidao_transito_julgado.pdf",
        "acordo_homologacao.pdf",
        "documento_generico.pdf"
    ]

    for nome in testes:
        categoria = classifier.classificar_por_nome(nome)
        if categoria:
            nome_categoria = classifier.CATEGORIAS[categoria]["nome"]
            logger.info(f"✓ {nome:40s} → {nome_categoria}")
        else:
            logger.info(f"✗ {nome:40s} → [Não identificado]")

    logger.info("="*80)


def test_classificador_com_pdfs():
    """Testa classificação com arquivos PDF reais"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 2: Classificação de PDFs Reais")
    logger.info("="*80)

    # Procura PDFs na pasta downloads_teste
    downloads_dir = Path("downloads_teste")

    if not downloads_dir.exists():
        logger.warning("Pasta downloads_teste não existe!")
        logger.info("Crie a pasta e adicione alguns PDFs para testar")
        return

    arquivos_pdf = list(downloads_dir.glob("*.pdf"))

    if not arquivos_pdf:
        logger.warning("Nenhum PDF encontrado em downloads_teste/")
        logger.info("Adicione alguns PDFs para testar a classificação")
        return

    logger.info(f"Encontrados {len(arquivos_pdf)} arquivo(s) PDF")
    logger.info("")

    classifier = DocumentClassifier()

    for pdf_path in arquivos_pdf[:10]:  # Limita a 10 para não demorar muito
        logger.info(f"Analisando: {pdf_path.name}")

        resultado = classifier.classificar_documento(
            caminho_pdf=str(pdf_path),
            nome_arquivo=pdf_path.name
        )

        logger.info(f"  ├─ Categoria: {resultado['nome_categoria']}")
        logger.info(f"  ├─ Confiança: {resultado['confianca']}")
        logger.info(f"  ├─ Método: {resultado['metodo']}")
        logger.info(f"  └─ Texto extraído: {'Sim' if resultado['texto_extraido'] else 'Não'}")
        logger.info("")

    # Mostra estatísticas
    logger.info("="*80)
    logger.info("ESTATÍSTICAS")
    logger.info("="*80)
    stats = classifier.get_stats()
    logger.info(f"Total de documentos: {stats['total']}")
    logger.info(f"Com texto extraído: {stats['com_texto']}")
    logger.info(f"Sem texto: {stats['sem_texto']}")
    logger.info("")
    logger.info("Documentos por categoria:")
    for cat, count in stats['por_categoria'].items():
        nome_cat = classifier.CATEGORIAS.get(cat, {}).get('nome', cat)
        logger.info(f"  • {nome_cat}: {count}")
    logger.info("="*80)


def test_classificador_lote():
    """Testa classificação em lote (simulando uso real)"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 3: Classificação em Lote (uso real)")
    logger.info("="*80)

    downloads_dir = Path("downloads_teste")

    if not downloads_dir.exists() or not list(downloads_dir.glob("*.pdf")):
        logger.warning("Pasta downloads_teste sem PDFs. Pulando teste.")
        return

    # Simula estrutura de documentos como vem do SuperSim
    documentos = []
    for idx, pdf_path in enumerate(list(downloads_dir.glob("*.pdf"))[:5], start=1):
        documentos.append({
            "numero_linha": idx,
            "nome_arquivo": pdf_path.name,
            "tipo_documento": pdf_path.stem,  # Nome sem extensão
            "caminho_arquivo": str(pdf_path),
            "nome_arquivo_final": pdf_path.name
        })

    logger.info(f"Classificando {len(documentos)} documento(s) em lote...")
    logger.info("")

    classifier = get_classifier()
    documentos_classificados = classifier.classificar_lote(documentos)

    logger.info("")
    logger.info("Resultados da classificação:")
    logger.info("-" * 80)

    for doc in documentos_classificados:
        class_info = doc.get("classificacao", {})
        logger.info(f"Arquivo: {doc['nome_arquivo']}")
        logger.info(f"  Classificação: {class_info.get('nome_categoria', 'N/A')}")
        logger.info(f"  Confiança: {class_info.get('confianca', 'N/A')}")
        logger.info(f"  Método: {class_info.get('metodo', 'N/A')}")
        logger.info("")

    logger.info("="*80)


def test_extracao_texto():
    """Testa apenas a extração de texto de PDFs"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 4: Extração de Texto")
    logger.info("="*80)

    downloads_dir = Path("downloads_teste")

    if not downloads_dir.exists():
        logger.warning("Pasta downloads_teste não existe!")
        return

    arquivos_pdf = list(downloads_dir.glob("*.pdf"))

    if not arquivos_pdf:
        logger.warning("Nenhum PDF encontrado")
        return

    classifier = DocumentClassifier()
    pdf_path = arquivos_pdf[0]

    logger.info(f"Extraindo texto de: {pdf_path.name}")
    logger.info("")

    texto = classifier.extrair_texto_pdf(str(pdf_path), max_paginas=1)

    if texto:
        logger.info("✓ Texto extraído com sucesso!")
        logger.info("")
        logger.info("Primeiras 500 caracteres:")
        logger.info("-" * 80)
        logger.info(texto[:500])
        logger.info("-" * 80)
        logger.info(f"Total de caracteres: {len(texto)}")
    else:
        logger.warning("✗ Não foi possível extrair texto do PDF")
        logger.info("Possíveis causas:")
        logger.info("  - PDF é uma imagem escaneada (sem texto)")
        logger.info("  - PDF está protegido")
        logger.info("  - Bibliotecas PyPDF2/pdfplumber não instaladas")

    logger.info("="*80)


def main():
    """Executa todos os testes"""
    logger.info("")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  TESTE DO CLASSIFICADOR DE DOCUMENTOS".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")

    try:
        # Teste 1: Classificação por nome
        test_classificador_simples()

        # Teste 2: Classificação com PDFs reais
        test_classificador_com_pdfs()

        # Teste 3: Classificação em lote
        test_classificador_lote()

        # Teste 4: Extração de texto
        test_extracao_texto()

        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + " " * 78 + "║")
        logger.info("║" + "  ✓ TODOS OS TESTES CONCLUÍDOS".center(78) + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info("")

        logger.info("OBSERVAÇÕES:")
        logger.info("  • Para melhor classificação, instale: pip install PyPDF2 pdfplumber")
        logger.info("  • A classificação melhora com texto extraído do PDF")
        logger.info("  • Documentos sem texto são classificados apenas pelo nome")
        logger.info("")

    except KeyboardInterrupt:
        logger.warning("\nTeste interrompido pelo usuário")
    except Exception as e:
        logger.error(f"\nErro durante testes: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
