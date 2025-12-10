"""
Lógica RPA para download de documentos

Este arquivo contém a implementação real do RPA para diferentes sistemas legais.
Sistemas suportados:
- eLaw COGNA
- Lexxy SuperSim
"""
import os
import time
import shutil
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Import das classes dos sistemas
from sistemas.elaw.cogna import ElawCOGNA
from sistemas.lexxy.supersim import LexxySuperSim
from settings import settings

logger = logging.getLogger(__name__)


def download_document(process_number: str, client_name: str) -> Optional[list]:
    """
    Baixa documentos usando o RPA eLaw COGNA

    Fluxo:
    1. Cria driver Chrome local
    2. Instancia ElawCOGNA
    3. Faz login
    4. Busca e baixa todos os documentos do processo
    5. Retorna lista de documentos com metadados

    Args:
        process_number: Número do processo
        client_name: Nome do cliente/robô

    Returns:
        Lista de dicionários com metadados dos documentos baixados:
        [
            {
                "numero_linha": int,
                "nome_arquivo": str,
                "tipo_documento": str,
                "caminho_arquivo": str,
                "nome_arquivo_final": str
            },
            ...
        ]

    Raises:
        Exception: Em caso de erro no processo
    """
    driver = None
    try:
        logger.info(f"Iniciando download para processo {process_number}")

        # 1. Criar driver Chrome local
        driver = _criar_driver_local()

        # 2. Criar instância do sistema eLaw (com credenciais do settings)
        elaw = ElawCOGNA(
            driver=driver,
            usuario=settings.ELAW_USERNAME,
            senha=settings.ELAW_PASSWORD,
            download_path=os.path.join(os.path.expanduser("~"), "Downloads")
        )

        # 3. Login
        logger.info("Entrando no sistema eLaw...")
        elaw.ENTRAR_NO_SISTEMA()

        logger.info("Fazendo login...")
        if not elaw.LOGIN():
            raise AuthenticationException("Falha no login do sistema eLaw")

        logger.info("Login realizado com sucesso")

        # 4. Baixar documentos (método retorna lista de documentos com metadados)
        logger.info(f"Baixando documentos do processo {process_number}")
        documentos = elaw.baixa_documento_anexo(process_number)

        if not documentos or len(documentos) == 0:
            raise DownloadException("Nenhum documento foi baixado")

        logger.info(f"Download concluído: {len(documentos)} documento(s) baixado(s)")

        # 5. Validar que os arquivos existem
        for doc in documentos:
            if not os.path.exists(doc['caminho_arquivo']):
                raise DownloadException(f"Arquivo não encontrado: {doc['nome_arquivo_final']}")

        logger.info("Todos os arquivos salvos com sucesso")
        return documentos

    except Exception as e:
        logger.error(f"Erro ao baixar documentos: {e}")
        raise

    finally:
        if driver:
            logger.info("Fechando navegador...")
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Erro ao fechar driver: {e}")


def _criar_driver_local():
    """
    Cria driver Chrome local para RPA

    Returns:
        WebDriver: Instância do Chrome WebDriver configurado
    """
    logger.info("Criando driver Chrome local...")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")

    # Anti-detecção de automação
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Suprime avisos desnecessários
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")

    # Configuração de downloads (pasta Downloads do usuário)
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    prefs = {
        "download.default_directory": downloads_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        # Remove indicadores de automação
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Remove propriedades que indicam automação
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

        logger.info("Driver Chrome criado com sucesso (modo stealth)")
        return driver

    except Exception as e:
        logger.error(f"Erro ao criar driver Chrome: {e}")
        raise


def download_document_lexxy(process_number: str, client_name: str) -> Optional[list]:
    """
    Baixa documentos usando o RPA Lexxy SuperSim

    Fluxo:
    1. Cria driver Chrome local
    2. Instancia LexxySuperSim
    3. Faz login
    4. Busca e baixa todos os documentos do processo
    5. Retorna lista de documentos com metadados

    Args:
        process_number: Número do processo
        client_name: Nome do cliente/robô

    Returns:
        Lista de dicionários com metadados dos documentos baixados:
        [
            {
                "numero_linha": int,
                "nome_arquivo": str,
                "tipo_documento": str,
                "caminho_arquivo": str,
                "nome_arquivo_final": str
            },
            ...
        ]

    Raises:
        Exception: Em caso de erro no processo
    """
    driver = None
    try:
        logger.info(f"Iniciando download Lexxy SuperSim para processo {process_number}")

        # 1. Criar driver Chrome local
        driver = _criar_driver_local()

        # 2. Criar instância do sistema Lexxy (com credenciais do settings)
        lexxy = LexxySuperSim(
            driver=driver,
            downloads_dir=os.path.join(os.path.expanduser("~"), "Downloads")
        )

        # 3. Login
        logger.info("Entrando no sistema Lexxy SuperSim...")
        lexxy.ENTRAR_NO_SISTEMA()

        logger.info("Fazendo login...")
        if not lexxy.LOGIN():
            raise AuthenticationException("Falha no login do sistema Lexxy SuperSim")

        logger.info("Login realizado com sucesso")

        # 4. Baixar documentos (método retorna lista de documentos com metadados)
        logger.info(f"Baixando documentos do processo {process_number}")
        documentos = lexxy.baixa_documento_anexo(process_number)

        if not documentos or len(documentos) == 0:
            raise DownloadException("Nenhum documento foi baixado")

        logger.info(f"Download concluído: {len(documentos)} documento(s) baixado(s)")

        # 5. Validar que os arquivos existem
        for doc in documentos:
            if not os.path.exists(doc['caminho_arquivo']):
                raise DownloadException(f"Arquivo não encontrado: {doc['nome_arquivo_final']}")

        logger.info("Todos os arquivos salvos com sucesso")
        return documentos

    except Exception as e:
        logger.error(f"Erro ao baixar documentos Lexxy: {e}")
        raise

    finally:
        if driver:
            logger.info("Fechando navegador...")
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Erro ao fechar driver: {e}")


def validate_process_number(process_number: str) -> bool:
    """
    Valida se o número do processo está no formato correto

    Args:
        process_number: Número do processo a ser validado

    Returns:
        True se o número é válido, False caso contrário
    """
    if not process_number:
        return False

    # Remove espaços em branco
    process_number = process_number.strip()

    # Verifica se tem comprimento mínimo
    if len(process_number) < 5:
        return False

    return True


# Exceções customizadas
class RPAException(Exception):
    """Exceção customizada para erros de RPA"""
    pass


class DocumentNotFoundException(RPAException):
    """Exceção quando o documento não é encontrado"""
    pass


class AuthenticationException(RPAException):
    """Exceção quando há erro de autenticação"""
    pass


class DownloadException(RPAException):
    """Exceção quando há erro no download"""
    pass
