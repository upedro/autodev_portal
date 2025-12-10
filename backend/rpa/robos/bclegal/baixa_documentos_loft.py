#!/usr/bin/env python
"""
Script de teste para verificar o login no sistema BCLegal Loft
Autor: AutoDev
Data: 2025
"""

import sys
import os
import time
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sistemas.bclegal.bclegal_loft import BCLegalLoft
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

downloads_dir = os.path.join(BASE_DIR, "downloads_teste")
os.makedirs(downloads_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"test_bclegal_loft_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("TEST_BCLEGAL_LOFT")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

SELENOID_PRIMARY = "http://autodevti.ddns.net/wd/hub"
SELENOID_FALLBACK = "http://201.54.10.172:44/wd/hub"


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

    # Configuracao de downloads
    prefs = {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Driver Chrome local criado com sucesso")
        return driver
    except Exception as e:
        logger.error(f"Erro ao criar driver Chrome local: {e}")
        raise


def criar_driver_selenoid(session_name="BCLegal Loft - Teste Automatico"):
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


def test_login_local():
    """Testa o login no sistema BCLegal Loft usando Chrome local"""
    logger.info("="*70)
    logger.info("TESTE COMPLETO - SISTEMA BCLEGAL LOFT (CHROME LOCAL)")
    logger.info("="*70)

    driver = None

    try:
        logger.info("Iniciando teste com Chrome local...")

        # Cria driver local
        driver = criar_driver_local()

        # Cria instancia do BCLegal Loft com credenciais padrao
        # usuario: tifany.oliveira, senha: Oliveir@
        bclegal = BCLegalLoft()

        # Inicializa o driver
        if not bclegal.inicializar_driver(driver):
            logger.error("="*70)
            logger.error("FALHA - Erro ao inicializar driver!")
            logger.error("="*70)
            return False

        logger.info("Driver inicializado com sucesso")

        # Tenta fazer login
        resultado_login = bclegal.fazer_login()

        if resultado_login:
            logger.info("="*70)
            logger.info("SUCESSO - Login realizado com sucesso!")
            logger.info("="*70)

            # Verifica se esta logado
            if bclegal.esta_logado():
                logger.info("="*70)
                logger.info("SUCESSO - Usuario esta logado no sistema!")
                logger.info("="*70)
                logger.info(f"URL atual: {driver.current_url}")

                # Testa acesso a Gestao de Despejos
                logger.info("="*70)
                logger.info("Testando acesso a Gestao de Despejos...")
                logger.info("="*70)

                if bclegal.acessar_gestao_despejos():
                    logger.info("="*70)
                    logger.info("SUCESSO - Gestao de Despejos acessada!")
                    logger.info("="*70)

                    # Testa busca por contrato
                    numero_teste = "670122"
                    logger.info(f"Testando busca por contrato: {numero_teste}")

                    if bclegal.buscar_contrato(numero_teste):
                        logger.info("="*70)
                        logger.info(f"SUCESSO - Busca por contrato {numero_teste} executada!")
                        logger.info("="*70)
                        
                        
                        return True
                    else:
                        logger.error("="*70)
                        logger.error("FALHA - Erro ao buscar contrato!")
                        logger.error("="*70)
                        return False
                else:
                    logger.error("="*70)
                    logger.error("FALHA - Erro ao acessar Gestao de Despejos!")
                    logger.error("="*70)
                    return False
            else:
                logger.error("="*70)
                logger.error("FALHA - Usuario nao esta logado!")
                logger.error("="*70)
                return False
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login!")
            logger.error("="*70)
            return False

    except ValueError as e:
        logger.error("="*70)
        logger.error(f"ERRO - Problema com credenciais: {e}")
        logger.error("="*70)
        logger.error("DICA: Verifique se o arquivo .env existe e contem:")
        logger.error("      BCLEGAL_LOFT_USER=seu_email@dominio.com")
        logger.error("      BCLEGAL_LOFT_PASSWORD=sua_senha")
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


def test_login_selenoid():
    """Testa o login no sistema BCLegal Loft usando Selenoid"""
    logger.info("="*70)
    logger.info("TESTE COMPLETO - SISTEMA BCLEGAL LOFT (SELENOID)")
    logger.info("="*70)

    driver = None

    try:
        logger.info("Iniciando teste com Selenoid...")

        # Cria driver Selenoid
        driver = criar_driver_selenoid("BCLegal Loft - Teste Automatico")

        # Cria instancia do BCLegal Loft com credenciais padrao
        # usuario: tifany.oliveira, senha: Oliveir@
        bclegal = BCLegalLoft()

        # Inicializa o driver
        if not bclegal.inicializar_driver(driver):
            logger.error("="*70)
            logger.error("FALHA - Erro ao inicializar driver!")
            logger.error("="*70)
            return False

        logger.info("Driver inicializado com sucesso")

        # Tenta fazer login
        resultado_login = bclegal.fazer_login()

        if resultado_login:
            logger.info("="*70)
            logger.info("SUCESSO - Login realizado com sucesso via Selenoid!")
            logger.info("="*70)

            # Verifica se esta logado
            if bclegal.esta_logado():
                logger.info("="*70)
                logger.info("SUCESSO - Usuario esta logado no sistema via Selenoid!")
                logger.info("="*70)
                logger.info(f"URL atual: {driver.current_url}")

                # Testa acesso a Gestao de Despejos
                logger.info("="*70)
                logger.info("Testando acesso a Gestao de Despejos via Selenoid...")
                logger.info("="*70)

                if bclegal.acessar_gestao_despejos():
                    logger.info("="*70)
                    logger.info("SUCESSO - Gestao de Despejos acessada via Selenoid!")
                    logger.info("="*70)

                    # Testa busca por contrato
                    numero_teste = "670122"
                    logger.info(f"Testando busca por contrato: {numero_teste}")

                    if bclegal.buscar_contrato(numero_teste):
                        logger.info("="*70)
                        logger.info(f"SUCESSO - Busca por contrato {numero_teste} executada via Selenoid!")
                        logger.info("="*70)
                        
                        
                        
                        if bclegal.verificar_resultado_busca(numero_teste):
                            logger.info("="*70)
                            logger.info(f"SUCESSO - Contrato {numero_teste} verificado via Selenoid!")
                            logger.info("="*70)
                                  
                            if bclegal.acessa_informacoes_pasta():
                                logger.info("="*70)
                                logger.info(f"SUCESSO - Mais informações da pasta acessadas via Selenoid!")
                                logger.info("="*70)
                                                            
                                if bclegal.acessa_aba_documentos():
                                    logger.info("="*70)
                                    logger.info(f"SUCESSO - Aba de documentos da pasta acessada via Selenoid!")
                                    logger.info("="*70)

                                    # Aguarda a aba carregar completamente
                                    time.sleep(3)

                                    # Testa busca e download de documento
                                    tipo_documento = "PETICAO INICIAL"
                                    logger.info(f"Testando busca e download do documento: {tipo_documento}")

                                    if bclegal.busca_e_baixa_documentos(tipo_documento):
                                        logger.info("="*70)
                                        logger.info(f"SUCESSO - Documento {tipo_documento} baixado via Selenoid!")
                                        logger.info("="*70)

                                        # Aguarda o download completar
                                        time.sleep(5)

                                        return True
                                    else:
                                        logger.error("="*70)
                                        logger.error("FALHA - Erro ao buscar e baixar documento via Selenoid!")
                                        logger.error("="*70)
                                        return False
                                else:
                                    logger.error("="*70)
                                    logger.error("FALHA - Erro ao acessar aba de documentos via Selenoid!")
                                    logger.error("="*70)
                                    return False                               
                            else:
                                logger.error("="*70)
                                logger.error("FALHA - Erro ao buscar contrato via Selenoid!")
                                logger.error("="*70)
                                return False                              
                        else:
                            logger.error("="*70)
                            logger.error("FALHA - Erro ao buscar contrato via Selenoid!")
                            logger.error("="*70)
                            return False                        
                    else:
                        logger.error("="*70)
                        logger.error("FALHA - Erro ao buscar contrato via Selenoid!")
                        logger.error("="*70)
                        return False
                else:
                    logger.error("="*70)
                    logger.error("FALHA - Erro ao acessar Gestao de Despejos via Selenoid!")
                    logger.error("="*70)
                    return False
            else:
                logger.error("="*70)
                logger.error("FALHA - Usuario nao esta logado via Selenoid!")
                logger.error("="*70)
                return False
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login via Selenoid!")
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
            logger.info("Fechando navegador...")
            driver.quit()


def test_login_com_credenciais():
    """Testa o login usando usuario e senha ao inves de autenticacao integrada"""
    logger.info("="*70)
    logger.info("TESTE COM CREDENCIAIS - SISTEMA BCLEGAL LOFT")
    logger.info("="*70)

    driver = None

    try:
        # Solicita credenciais
        print("\n" + "="*70)
        print("TESTE COM USUARIO E SENHA")
        print("="*70)
        usuario = input("Digite o usuario/email: ").strip()
        senha = input("Digite a senha: ").strip()
        print("")

        if not usuario or not senha:
            logger.error("Usuario ou senha nao fornecidos!")
            return False

        logger.info("Iniciando teste com credenciais fornecidas...")

        # Cria driver local
        driver = criar_driver_local()

        # Cria instancia do BCLegal Loft com credenciais
        bclegal = BCLegalLoft(
            usuario=usuario,
            senha=senha,
            usar_auth_integrada=False
        )

        # Inicializa o driver
        if not bclegal.inicializar_driver(driver):
            logger.error("="*70)
            logger.error("FALHA - Erro ao inicializar driver!")
            logger.error("="*70)
            return False

        logger.info("Driver inicializado com sucesso")

        # Tenta fazer login
        resultado_login = bclegal.fazer_login()

        if resultado_login:
            logger.info("="*70)
            logger.info("SUCESSO - Login com credenciais realizado com sucesso!")
            logger.info("="*70)

            # Verifica se esta logado
            if bclegal.esta_logado():
                logger.info("="*70)
                logger.info("SUCESSO - Usuario esta logado no sistema!")
                logger.info("="*70)
                logger.info(f"URL atual: {driver.current_url}")
                logger.info("Aguardando 15 segundos para visualizacao...")
                
                return True
            else:
                logger.error("="*70)
                logger.error("FALHA - Usuario nao esta logado!")
                logger.error("="*70)
                return False
        else:
            logger.error("="*70)
            logger.error("FALHA - Erro ao realizar login com credenciais!")
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
    logger.info("# SUITE DE TESTES - BCLEGAL LOFT RPA")
    logger.info("#"*70)
    logger.info("")

    logger.info("Escolha o tipo de teste:")
    logger.info("1 - Teste com Chrome Local + Autenticacao Integrada (recomendado)")
    logger.info("2 - Teste com Selenoid + Autenticacao Integrada")
    logger.info("3 - Teste com Usuario/Senha (Chrome Local)")
    logger.info("4 - Executar testes 1 e 2")
    logger.info("")

    opcao = input("Digite sua opcao (1, 2, 3 ou 4): ").strip()
    logger.info(f"Opcao selecionada: {opcao}")
    logger.info("")

    if opcao == "1":
        sucesso = test_login_local()
    elif opcao == "2":
        sucesso = test_login_selenoid()
    elif opcao == "3":
        sucesso = test_login_com_credenciais()
    elif opcao == "4":
        logger.info("Executando teste com Chrome local primeiro...")
        logger.info("")
        sucesso1 = test_login_local()
        logger.info("")
        logger.info("Executando teste com Selenoid...")
        logger.info("")
        sucesso2 = test_login_selenoid()
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
