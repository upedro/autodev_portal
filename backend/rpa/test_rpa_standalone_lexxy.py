#!/usr/bin/env python
"""
Teste Standalone do RPA Lexxy SuperSim - Executa FORA do Worker

Este script testa o fluxo completo do RPA sem depender do Celery/Worker.
Pode ser executado diretamente com: python test_rpa_standalone_lexxy.py

Autor: AutoDev
Data: 2025-11-18
"""

import sys
import os
import time
import logging
from datetime import datetime

# Adiciona a raiz do projeto ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sistemas.lexxy.supersim import LexxySuperSim
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Configuracao de logs
log_dir = os.path.join(current_dir, "logs_standalone_lexxy")
os.makedirs(log_dir, exist_ok=True)

downloads_dir = os.path.join(current_dir, "downloads_standalone_lexxy")
os.makedirs(downloads_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"test_standalone_lexxy_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("TEST_RPA_STANDALONE_LEXXY")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Numero do processo de teste
NUMERO_PROCESSO_TESTE = "00016683620258173120"


def criar_driver_local():
    """Cria um driver Chrome local com configuracoes otimizadas"""
    logger.info("Criando driver Chrome local...")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")

    # Opcoes para evitar deteccao de automacao
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Suprime avisos e erros desnecessarios
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")

    # Configuracao de downloads
    prefs = {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        # Permite multiplos downloads automaticos
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Remove propriedades do navigator que indicam automacao
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en']
                });
            """
        })

        logger.info("Driver Chrome local criado com sucesso (modo stealth)")
        return driver
    except Exception as e:
        logger.error(f"Erro ao criar driver Chrome local: {e}")
        raise


def test_login_simples():
    """
    Teste 1: Testa apenas o login no sistema

    Returns:
        bool: True se o login foi bem-sucedido
    """
    logger.info("="*70)
    logger.info("TESTE 1: LOGIN SIMPLES")
    logger.info("="*70)

    driver = None

    try:
        # Cria driver
        driver = criar_driver_local()

        # Cria instancia do Lexxy SuperSim
        lexxy = LexxySuperSim(driver=driver, downloads_dir=downloads_dir)

        # Entra no sistema
        logger.info("Acessando o sistema...")
        lexxy.ENTRAR_NO_SISTEMA()
        logger.info("Sistema acessado")

        # Faz login
        logger.info("Realizando login...")
        if lexxy.LOGIN():
            logger.info("="*70)
            logger.info("SUCESSO - Login realizado com sucesso!")
            logger.info("="*70)
            time.sleep(5)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error(f"ERRO durante teste de login: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador...")
            time.sleep(3)
            driver.quit()


def test_acessar_processos():
    """
    Teste 2: Testa login + acesso a processos

    Returns:
        bool: True se acessou a lista de processos
    """
    logger.info("="*70)
    logger.info("TESTE 2: LOGIN + ACESSAR PROCESSOS")
    logger.info("="*70)

    driver = None

    try:
        # Cria driver
        driver = criar_driver_local()

        # Cria instancia do Lexxy SuperSim
        lexxy = LexxySuperSim(driver=driver, downloads_dir=downloads_dir)

        # Login
        logger.info("Realizando login...")
        lexxy.ENTRAR_NO_SISTEMA()
        if not lexxy.LOGIN():
            logger.error("Falha no login")
            return False

        logger.info("Login realizado com sucesso")
        time.sleep(3)

        # Acessa processos
        logger.info("Acessando lista de processos...")
        if lexxy.ACESSAR_PROCESSOS():
            logger.info("="*70)
            logger.info("SUCESSO - Lista de processos acessada!")
            logger.info("="*70)
            time.sleep(5)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao acessar lista de processos!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error(f"ERRO durante teste de acesso a processos: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador...")
            time.sleep(3)
            driver.quit()


def test_buscar_processo():
    """
    Teste 3: Testa login + busca de processo

    Returns:
        bool: True se encontrou o processo
    """
    logger.info("="*70)
    logger.info("TESTE 3: LOGIN + BUSCAR PROCESSO")
    logger.info("="*70)

    driver = None

    try:
        # Cria driver
        driver = criar_driver_local()

        # Cria instancia do Lexxy SuperSim
        lexxy = LexxySuperSim(driver=driver, downloads_dir=downloads_dir)

        # Login
        logger.info("Realizando login...")
        lexxy.ENTRAR_NO_SISTEMA()
        if not lexxy.LOGIN():
            logger.error("Falha no login")
            return False

        logger.info("Login realizado com sucesso")
        time.sleep(3)

        # Acessa processos
        logger.info("Acessando lista de processos...")
        if not lexxy.ACESSAR_PROCESSOS():
            logger.error("Falha ao acessar lista de processos")
            return False

        logger.info("Lista de processos acessada")
        time.sleep(2)

        # Busca processo
        logger.info(f"Buscando processo: {NUMERO_PROCESSO_TESTE}")
        if lexxy.BUSCAR_PROCESSO(NUMERO_PROCESSO_TESTE):
            logger.info("="*70)
            logger.info("SUCESSO - Processo encontrado!")
            logger.info("="*70)
            time.sleep(5)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Processo nao encontrado!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error(f"ERRO durante teste de busca de processo: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador...")
            time.sleep(3)
            driver.quit()


def test_baixa_documento():
    """
    Teste 4: Testa o fluxo completo de baixa de documentos

    Returns:
        bool: True se baixou os documentos com sucesso
    """
    logger.info("="*70)
    logger.info("TESTE 4: FLUXO COMPLETO - BAIXA DE DOCUMENTOS")
    logger.info("="*70)

    driver = None

    try:
        # Cria driver
        driver = criar_driver_local()

        # Cria instancia do Lexxy SuperSim
        lexxy = LexxySuperSim(driver=driver, downloads_dir=downloads_dir)

        # Login
        logger.info("Realizando login...")
        lexxy.ENTRAR_NO_SISTEMA()
        if not lexxy.LOGIN():
            logger.error("Falha no login")
            return False

        logger.info("Login realizado com sucesso")
        time.sleep(3)

        # Executa fluxo completo de baixa de documentos
        logger.info(f"Iniciando fluxo de baixa de documentos para processo: {NUMERO_PROCESSO_TESTE}")
        documentos = lexxy.baixa_documento_anexo(NUMERO_PROCESSO_TESTE)

        if documentos and len(documentos) > 0:
            logger.info("="*70)
            logger.info(f"SUCESSO - {len(documentos)} documento(s) baixado(s) com sucesso!")
            logger.info("="*70)

            # Lista os documentos baixados
            for i, doc in enumerate(documentos, 1):
                logger.info(f"Documento {i}:")
                logger.info(f"  - Nome original: {doc['nome_arquivo']}")
                logger.info(f"  - Nome final: {doc['nome_arquivo_final']}")
                logger.info(f"  - Tipo: {doc['tipo_documento']}")
                logger.info(f"  - Caminho: {doc['caminho_arquivo']}")

            time.sleep(10)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Nenhum documento foi baixado!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error(f"ERRO durante teste de baixa de documento: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador...")
            time.sleep(3)
            driver.quit()


def main():
    """Menu principal de testes"""
    logger.info("")
    logger.info("#"*70)
    logger.info("# TESTE STANDALONE - RPA LEXXY SUPERSIM")
    logger.info("# (Executa FORA do Worker)")
    logger.info("#"*70)
    logger.info("")
    logger.info(f"Processo de teste: {NUMERO_PROCESSO_TESTE}")
    logger.info(f"Pasta de downloads: {downloads_dir}")
    logger.info(f"Pasta de logs: {log_dir}")
    logger.info("")

    logger.info("Escolha o teste a executar:")
    logger.info("1 - Teste de Login Simples")
    logger.info("2 - Teste de Login + Acessar Processos")
    logger.info("3 - Teste de Login + Buscar Processo")
    logger.info("4 - Teste Completo: Baixa de Documentos")
    logger.info("5 - Executar TODOS os testes")
    logger.info("")

    opcao = input("Digite sua opcao (1-5): ").strip()
    logger.info(f"Opcao selecionada: {opcao}")
    logger.info("")

    resultados = []

    if opcao == "1":
        sucesso = test_login_simples()
        resultados.append(("Login Simples", sucesso))

    elif opcao == "2":
        sucesso = test_acessar_processos()
        resultados.append(("Login + Acessar Processos", sucesso))

    elif opcao == "3":
        sucesso = test_buscar_processo()
        resultados.append(("Login + Buscar Processo", sucesso))

    elif opcao == "4":
        sucesso = test_baixa_documento()
        resultados.append(("Baixa de Documentos", sucesso))

    elif opcao == "5":
        logger.info("Executando TODOS os testes...")
        logger.info("")

        logger.info("Executando Teste 1...")
        sucesso1 = test_login_simples()
        resultados.append(("1. Login Simples", sucesso1))
        logger.info("")

        logger.info("Executando Teste 2...")
        sucesso2 = test_acessar_processos()
        resultados.append(("2. Login + Acessar Processos", sucesso2))
        logger.info("")

        logger.info("Executando Teste 3...")
        sucesso3 = test_buscar_processo()
        resultados.append(("3. Login + Buscar Processo", sucesso3))
        logger.info("")

        logger.info("Executando Teste 4...")
        sucesso4 = test_baixa_documento()
        resultados.append(("4. Baixa de Documentos", sucesso4))

    else:
        logger.error("Opcao invalida! Execute novamente.")
        sys.exit(1)

    # Mostra resumo dos resultados
    logger.info("")
    logger.info("#"*70)
    logger.info("# RESUMO DOS TESTES")
    logger.info("#"*70)

    todos_passaram = True
    for nome_teste, sucesso in resultados:
        status = "PASSOU" if sucesso else "FALHOU"
        logger.info(f"{nome_teste}: {status}")
        if not sucesso:
            todos_passaram = False

    logger.info("#"*70)
    if todos_passaram:
        logger.info("# RESULTADO FINAL: TODOS OS TESTES PASSARAM!")
    else:
        logger.error("# RESULTADO FINAL: ALGUNS TESTES FALHARAM!")
    logger.info("#"*70)
    logger.info("")
    logger.info(f"Log completo salvo em: {log_filename}")
    logger.info("")

    sys.exit(0 if todos_passaram else 1)


if __name__ == "__main__":
    main()
