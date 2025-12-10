#!/usr/bin/env python
"""
Script de teste para verificar o login e baixa de documentos no sistema eLaw COGNA
Autor: AutoDev
Data: 2025
"""

import sys
import os
import time
import logging
from datetime import datetime

# Pega o diretório do script atual (...\robos\elaw)
current_dir = os.path.dirname(__file__)

# Sobe um nível para a pasta 'robos' (...\robos)
parent_dir = os.path.dirname(current_dir)

# Sobe mais um nível para a RAIZ do projeto (...\rpa-fluxlaw)
project_root = os.path.dirname(parent_dir)

# Adiciona a RAIZ ao sys.path
sys.path.insert(0, project_root)

# Agora esta linha vai funcionar
from sistemas.elaw.elaw_cogna import ElawCOGNA
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

downloads_dir = os.path.join(BASE_DIR, "downloads_teste")
os.makedirs(downloads_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"test_elaw_cogna_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("TEST_ELAW_COGNA")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

SELENOID_PRIMARY = "http://autodevti.ddns.net/wd/hub"
SELENOID_FALLBACK = "http://201.54.10.172:44/wd/hub"

# Número do processo de teste
NUMERO_PROCESSO_TESTE = "‌0569584-89.2017.8.05.0001"


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

    # Suprime avisos e erros desnecessarios do Google Cloud Messaging
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
        # Remove indicadores de automacao
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
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


def criar_driver_selenoid(session_name="eLaw COGNA - Teste Automatico"):
    """Cria um driver Chrome usando Selenoid"""
    logger.info("Criando driver Chrome via Selenoid...")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.set_capability(
        "selenoid:options",
        {
            "enableVNC": True,
            "enableVideo": False,
            "name": session_name,
        },
    )

    selenoid_servers = [SELENOID_PRIMARY, SELENOID_FALLBACK]

    for server_url in selenoid_servers:
        try:
            logger.info(f"Tentando conectar ao servidor Selenoid: {server_url}")
            driver = webdriver.Remote(
                command_executor=server_url,
                options=chrome_options,
            )
            session_id = driver.session_id
            logger.info(f"Driver Selenoid criado com sucesso no servidor {server_url}")
            logger.info(f"Session ID: {session_id}")
            return driver
        except WebDriverException as e:
            logger.warning(f"Falha ao conectar ao servidor {server_url}: {str(e)}")
            if server_url == selenoid_servers[-1]:
                logger.error("Todos os servidores Selenoid falharam")
                raise Exception("Nao foi possivel conectar a nenhum servidor Selenoid disponivel")
            logger.info("Tentando proximo servidor...")
            continue


def test_login_e_baixa_documentos_local():
    """Testa o login e baixa de documentos no sistema eLaw COGNA usando Chrome local"""
    logger.info("="*70)
    logger.info("TESTE COMPLETO - SISTEMA ELAW COGNA (CHROME LOCAL)")
    logger.info("="*70)

    driver = None

    try:
        logger.info("Iniciando teste com Chrome local...")

        # Cria driver local
        driver = criar_driver_local()

        # Cria instancia do eLaw COGNA passando o driver
        # usuario: lima.feigelson05, senha: Control@
        elaw = ElawCOGNA(driver=driver)

        logger.info("="*70)
        logger.info("ETAPA 1: Acessando o sistema eLaw...")
        logger.info("="*70)

        # Entra no sistema
        elaw.ENTRAR_NO_SISTEMA()
        logger.info("Sistema acessado")

        logger.info("="*70)
        logger.info("ETAPA 2: Realizando login...")
        logger.info("="*70)

        # Faz login
        if not elaw.LOGIN():
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login!")
            logger.error("="*70)
            return False

        logger.info("="*70)
        logger.info("SUCESSO - Login realizado com sucesso!")
        logger.info("="*70)

        # Aguarda para visualizacao
        time.sleep(3)

        logger.info("="*70)
        logger.info(f"ETAPA 3: Iniciando fluxo de baixa de documentos para processo {NUMERO_PROCESSO_TESTE}...")
        logger.info("="*70)

        # Executa fluxo completo de baixa de documentos
        if elaw.baixa_documento_anexo(NUMERO_PROCESSO_TESTE):
            logger.info("="*70)
            logger.info("SUCESSO - Fluxo de baixa de documentos concluido!")
            logger.info("="*70)
            logger.info("Aguardando 15 segundos para visualizacao...")
            time.sleep(15)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro no fluxo de baixa de documentos!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error("="*70)
        logger.error(f"ERRO durante execucao: {e}")
        logger.error("="*70)
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador em 5 segundos...")
            time.sleep(5)
            driver.quit()


def test_login_e_baixa_documentos_selenoid():
    """Testa o login e baixa de documentos no sistema eLaw COGNA usando Selenoid"""
    logger.info("="*70)
    logger.info("TESTE COMPLETO - SISTEMA ELAW COGNA (SELENOID)")
    logger.info("="*70)

    driver = None

    try:
        logger.info("Iniciando teste com Selenoid...")

        # Cria driver Selenoid
        driver = criar_driver_selenoid("eLaw COGNA - Teste Automatico")

        # Cria instancia do eLaw COGNA passando o driver
        elaw = ElawCOGNA(driver=driver)

        logger.info("="*70)
        logger.info("ETAPA 1: Acessando o sistema eLaw via Selenoid...")
        logger.info("="*70)

        # Entra no sistema
        elaw.ENTRAR_NO_SISTEMA()
        logger.info("Sistema acessado via Selenoid")

        logger.info("="*70)
        logger.info("ETAPA 2: Realizando login via Selenoid...")
        logger.info("="*70)

        # Faz login
        if not elaw.LOGIN():
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login via Selenoid!")
            logger.error("="*70)
            return False

        logger.info("="*70)
        logger.info("SUCESSO - Login realizado com sucesso via Selenoid!")
        logger.info("="*70)

        # Aguarda para visualizacao
        time.sleep(3)

        logger.info("="*70)
        logger.info(f"ETAPA 3: Iniciando fluxo de baixa de documentos para processo {NUMERO_PROCESSO_TESTE} via Selenoid...")
        logger.info("="*70)

        # Executa fluxo completo de baixa de documentos
        if elaw.baixa_documento_anexo(NUMERO_PROCESSO_TESTE):
            logger.info("="*70)
            logger.info("SUCESSO - Fluxo de baixa de documentos concluido via Selenoid!")
            logger.info("="*70)
            logger.info("Aguardando 15 segundos para visualizacao...")
            time.sleep(15)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro no fluxo de baixa de documentos via Selenoid!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error("="*70)
        logger.error(f"ERRO durante execucao com Selenoid: {e}")
        logger.error("="*70)
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador em 5 segundos...")
            time.sleep(5)
            driver.quit()


def test_acesso_rapido():
    """Teste rapido apenas para verificar login"""
    logger.info("="*70)
    logger.info("TESTE RAPIDO - LOGIN ELAW COGNA")
    logger.info("="*70)

    driver = None

    try:
        logger.info("Iniciando teste rapido com Chrome local...")

        # Cria driver local
        driver = criar_driver_local()

        # Cria instancia do eLaw COGNA passando o driver
        elaw = ElawCOGNA(driver=driver)

        # Entra no sistema
        elaw.ENTRAR_NO_SISTEMA()
        logger.info("Sistema acessado")

        # Faz login
        if elaw.LOGIN():
            logger.info("="*70)
            logger.info("SUCESSO - Login realizado!")
            logger.info("="*70)
            logger.info("Aguardando 10 segundos para visualizacao...")
            time.sleep(10)
            return True
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login!")
            logger.error("="*70)
            return False

    except Exception as e:
        logger.error("="*70)
        logger.error(f"ERRO durante execucao: {e}")
        logger.error("="*70)
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Fechando navegador...")
            driver.quit()


if __name__ == "__main__":
    """
    Executa os testes
    """
    logger.info("")
    logger.info("#"*70)
    logger.info("# SUITE DE TESTES - ELAW COGNA RPA")
    logger.info("#"*70)
    logger.info("")
    logger.info(f"Numero do processo de teste: {NUMERO_PROCESSO_TESTE}")
    logger.info("")

    logger.info("Escolha o tipo de teste:")
    logger.info("1 - Teste completo com Chrome Local (Login + Baixa de Documentos)")
    logger.info("2 - Teste completo com Selenoid (Login + Baixa de Documentos)")
    logger.info("3 - Teste rapido (Apenas Login)")
    logger.info("4 - Executar testes 1 e 2")
    logger.info("")

    opcao = input("Digite sua opcao (1, 2, 3 ou 4): ").strip()
    logger.info(f"Opcao selecionada: {opcao}")
    logger.info("")

    if opcao == "1":
        sucesso = test_login_e_baixa_documentos_local()
    elif opcao == "2":
        sucesso = test_login_e_baixa_documentos_selenoid()
    elif opcao == "3":
        sucesso = test_acesso_rapido()
    elif opcao == "4":
        logger.info("Executando teste com Chrome local primeiro...")
        logger.info("")
        sucesso1 = test_login_e_baixa_documentos_local()
        logger.info("")
        logger.info("Executando teste com Selenoid...")
        logger.info("")
        sucesso2 = test_login_e_baixa_documentos_selenoid()
        sucesso = sucesso1 and sucesso2
    else:
        logger.error("Opcao invalida! Execute novamente.")
        sys.exit(1)

    logger.info("")
    logger.info("#"*70)
    if sucesso:
        logger.info("# RESULTADO FINAL: TODOS OS TESTES PASSARAM!")
    else:
        logger.error("# RESULTADO FINAL: ALGUNS TESTES FALHARAM!")
    logger.info("#"*70)
    logger.info("")

    sys.exit(0 if sucesso else 1)
