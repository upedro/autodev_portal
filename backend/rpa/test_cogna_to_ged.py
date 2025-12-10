#!/usr/bin/env python
"""
Script de teste end-to-end: eLaw Cogna → ADVWin GED

Este script:
1. Baixa documentos do eLaw Cogna para um processo específico
2. Classifica automaticamente os documentos
3. Envia para ADVWin GED via API com nomes categorizados
4. Gera relatório completo do processo

Autor: AutoDev
Data: 2025
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sistemas.elaw.cogna import ElawCOGNA
from sistemas.advwin import get_ged_helper

# Configuração de logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

downloads_dir = os.path.join(BASE_DIR, "downloads_teste_cogna")
os.makedirs(downloads_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"test_cogna_to_ged_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Número do processo para teste - AJUSTE CONFORME NECESSÁRIO
NUMERO_PROCESSO_TESTE = "0000000-00.0000.0.00.0000"  # ← ALTERE AQUI


def criar_driver_local():
    """Cria um driver Chrome local com configurações otimizadas"""
    logger.info("Criando driver Chrome local...")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")

    # Configuração de downloads
    prefs = {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Modo stealth para evitar detecção de bot
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Configurações anti-detecção
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        logger.info("✓ Driver Chrome local criado com sucesso")
        return driver
    except Exception as e:
        logger.error(f"Erro ao criar driver Chrome local: {e}")
        raise


def test_cogna_download():
    """
    Etapa 1: Baixa documentos do eLaw Cogna

    Returns:
        list: Lista de documentos baixados ou None em caso de erro
    """
    logger.info("")
    logger.info("#" * 80)
    logger.info("# ETAPA 1: DOWNLOAD DE DOCUMENTOS - ELAW COGNA")
    logger.info("#" * 80)
    logger.info(f"# Processo: {NUMERO_PROCESSO_TESTE}")
    logger.info("#" * 80)
    logger.info("")

    driver = None

    try:
        # Cria driver local
        driver = criar_driver_local()

        # Cria instância do eLaw Cogna
        logger.info("Inicializando eLaw Cogna...")
        cogna = ElawCOGNA(driver=driver, download_path=downloads_dir)

        # Acessa o sistema
        logger.info("Acessando o sistema...")
        cogna.ENTRAR_NO_SISTEMA()
        logger.info("✓ Sistema acessado")

        # Faz login
        logger.info("Realizando login no eLaw Cogna...")
        if not cogna.LOGIN():
            logger.error("✗ FALHA - Erro ao realizar login!")
            return None

        logger.info("✓ Login realizado com sucesso")

        # Confirma login (se necessário)
        try:
            cogna.CONFIRM_LOGIN()
        except:
            pass  # Pode não ser necessário em todos os casos

        # Baixa documentos e anexos
        logger.info(f"Baixando documentos do processo {NUMERO_PROCESSO_TESTE}...")
        documentos = cogna.baixa_documento_anexo(NUMERO_PROCESSO_TESTE)

        if not documentos or len(documentos) == 0:
            logger.error("✗ FALHA - Nenhum documento foi baixado!")
            return None

        logger.info("=" * 80)
        logger.info("✓ DOWNLOAD CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 80)
        logger.info(f"Total de documentos baixados: {len(documentos)}")
        logger.info("")
        logger.info("Documentos:")
        for idx, doc in enumerate(documentos, start=1):
            logger.info(f"  [{idx}] {doc.get('nome_arquivo_final')} - {doc.get('tipo_documento', 'N/A')}")
        logger.info("=" * 80)

        return documentos

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO durante download: {e}")
        logger.error("=" * 80)
        import traceback
        logger.error(traceback.format_exc())
        return None

    finally:
        if driver:
            logger.info("Fechando navegador...")
            try:
                driver.quit()
            except:
                pass


def test_ged_upload(documentos):
    """
    Etapa 2: Envia documentos para ADVWin GED com classificação automática

    Args:
        documentos: Lista de documentos baixados do Cogna

    Returns:
        dict: Resultado do envio ou None em caso de erro
    """
    logger.info("")
    logger.info("#" * 80)
    logger.info("# ETAPA 2: CLASSIFICAÇÃO E ENVIO PARA ADVWIN GED")
    logger.info("#" * 80)
    logger.info(f"# Processo: {NUMERO_PROCESSO_TESTE}")
    logger.info(f"# Documentos: {len(documentos)}")
    logger.info("#" * 80)
    logger.info("")

    try:
        # Obtém instância do helper GED (com classificador ativado por padrão)
        logger.info("Inicializando ADVWin API com classificador automático...")
        ged_helper = get_ged_helper()

        # Configurações de envio
        tabela_or = "Pastas"

        # IMPORTANTE: Ajuste estes valores conforme seu caso
        # - codigo_or = código da pasta no ADVWin
        # - id_or = número do processo (pode ser None se não souber)
        codigo_or = "00016-000407"  # ← AJUSTE: Código da pasta no ADVWin
        id_or = NUMERO_PROCESSO_TESTE  # ← Número do processo

        logger.info(f"Configurações:")
        logger.info(f"  - Tabela: {tabela_or}")
        logger.info(f"  - Código: {codigo_or}")
        logger.info(f"  - ID: {id_or}")
        logger.info(f"  - Classificação automática: ATIVADA ✓")
        logger.info("")

        # Confirma o envio
        print("=" * 80)
        print("ATENÇÃO: Os documentos serão:")
        print("  1. Classificados automaticamente (Petição, Sentença, etc.)")
        print("  2. Renomeados com a categoria identificada")
        print("  3. Enviados para o ADVWin GED")
        print("")
        print(f"Processo: {NUMERO_PROCESSO_TESTE}")
        print(f"Quantidade: {len(documentos)} documento(s)")
        print("=" * 80)
        resposta = input("Deseja prosseguir com o envio? (s/N): ").strip().lower()

        if resposta != 's':
            logger.info("Envio cancelado pelo usuário")
            return None

        logger.info("")
        logger.info("Iniciando classificação e envio para GED...")

        # Envia documentos (classificação automática acontece aqui)
        resultado = ged_helper.enviar_documentos_ged(
            documentos=documentos,
            numero_processo=NUMERO_PROCESSO_TESTE,
            tabela_or=tabela_or,
            codigo_or=codigo_or,
            id_or=id_or
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("RESULTADO DO ENVIO PARA GED")
        logger.info("=" * 80)

        if 'total' in resultado:
            logger.info(f"Total: {resultado.get('total', 0)}")
            logger.info(f"✓ Sucesso: {resultado.get('sucesso', 0)}")
            logger.info(f"✗ Falha: {resultado.get('falha', 0)}")
        elif 'erro' in resultado:
            logger.error(f"✗ Erro: {resultado.get('erro', 'Erro desconhecido')}")
        else:
            logger.warning("⚠ Resultado em formato inesperado")

        logger.info("=" * 80)

        # Mostra detalhes se disponível
        if resultado.get('detalhes'):
            logger.info("")
            logger.info("Detalhes por arquivo:")
            for detalhe in resultado['detalhes']:
                arquivo = detalhe.get('arquivo', 'arquivo desconhecido')
                resultado_upload = detalhe.get('resultado', {})
                status = "✓" if resultado_upload.get('sucesso') else "✗"
                logger.info(f"  {status} {arquivo}")
                if not resultado_upload.get('sucesso'):
                    erro = resultado_upload.get('erro', 'Erro desconhecido')
                    logger.info(f"     Erro: {erro}")

        logger.info("=" * 80)

        # Retorna sucesso se pelo menos um documento foi enviado
        sucesso = resultado.get('sucesso', 0) > 0 if 'sucesso' in resultado else False

        return resultado if sucesso else None

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"✗ ERRO durante envio para GED: {e}")
        logger.error("=" * 80)
        import traceback
        logger.error(traceback.format_exc())
        return None


def cleanup_temp_files(documentos):
    """
    Remove arquivos temporários após o envio

    Args:
        documentos: Lista de documentos para limpar
    """
    logger.info("")
    logger.info("Limpando arquivos temporários...")

    removidos = 0
    for doc in documentos:
        caminho = doc.get('caminho_arquivo')
        if caminho and os.path.exists(caminho):
            try:
                os.remove(caminho)
                removidos += 1
                logger.debug(f"Arquivo removido: {caminho}")
            except Exception as e:
                logger.warning(f"Erro ao remover {caminho}: {e}")

    logger.info(f"✓ {removidos} arquivo(s) temporário(s) removido(s)")


def main():
    """Função principal - executa o teste end-to-end"""

    logger.info("")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  TESTE END-TO-END: ELAW COGNA → ADVWIN GED".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")
    logger.info(f"Processo de teste: {NUMERO_PROCESSO_TESTE}")
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Log: {log_filename}")
    logger.info("")

    # ETAPA 1: Download do Cogna
    documentos = test_cogna_download()

    if not documentos:
        logger.error("")
        logger.error("╔" + "═" * 78 + "╗")
        logger.error("║" + " " * 78 + "║")
        logger.error("║" + "  ✗ FALHA - Download não concluído".center(78) + "║")
        logger.error("║" + " " * 78 + "║")
        logger.error("╚" + "═" * 78 + "╝")
        logger.error("")
        return False

    # ETAPA 2: Classificação e Envio para GED
    resultado_ged = test_ged_upload(documentos)

    if not resultado_ged:
        logger.warning("")
        logger.warning("╔" + "═" * 78 + "╗")
        logger.warning("║" + " " * 78 + "║")
        logger.warning("║" + "  ⚠ PARCIAL - Download OK, GED cancelado/falhou".center(78) + "║")
        logger.warning("║" + " " * 78 + "║")
        logger.warning("╚" + "═" * 78 + "╝")
        logger.warning("")
        return False

    # Limpeza (opcional)
    print("")
    resposta = input("Deseja remover arquivos temporários? (s/N): ").strip().lower()
    if resposta == 's':
        cleanup_temp_files(documentos)

    # RESULTADO FINAL
    logger.info("")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  ✓ TESTE END-TO-END CONCLUÍDO COM SUCESSO!".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")
    logger.info("RESUMO:")
    logger.info(f"  • Processo: {NUMERO_PROCESSO_TESTE}")
    logger.info(f"  • Documentos baixados: {len(documentos)}")
    logger.info(f"  • Classificados e enviados: {resultado_ged['sucesso']}")
    logger.info(f"  • Falhas: {resultado_ged['falha']}")
    logger.info("")
    logger.info(f"Log completo salvo em: {log_filename}")
    logger.info("")

    return True


if __name__ == "__main__":
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("Teste interrompido pelo usuário (Ctrl+C)")
        logger.warning("")
        sys.exit(1)
    except Exception as e:
        logger.error("")
        logger.error("╔" + "═" * 78 + "╗")
        logger.error("║" + " " * 78 + "║")
        logger.error("║" + "  ✗ ERRO FATAL".center(78) + "║")
        logger.error("║" + " " * 78 + "║")
        logger.error("╚" + "═" * 78 + "╝")
        logger.error("")
        logger.error(f"Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
