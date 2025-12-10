"""
Modulo de automacao RPA para BCLegal - Cliente Loft
Sistema de login e navegacao no portal BCLegal usando autenticacao SSO
"""

import os
import time
import shutil
import logging
import zipfile
from typing import Optional
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException
)

# Configuracao do logger
logger = logging.getLogger(__name__)


class SeleniumHelper:
    """Helper class para operacoes comuns do Selenium com WebDriverWait"""

    def __init__(self, driver: WebDriver, default_timeout: int = 20):
        self.driver = driver
        self.default_timeout = default_timeout

    def wait_element(self, by: str, value: str, timeout: Optional[int] = None) -> Optional[WebDriver]:
        """Aguarda elemento estar presente no DOM"""
        try:
            timeout = timeout or self.default_timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.info(f"Timeout aguardando elemento: {by}={value}")
            return None

    def wait_element_visible(self, by: str, value: str, timeout: Optional[int] = None) -> Optional[WebDriver]:
        """Aguarda elemento estar visivel"""
        try:
            timeout = timeout or self.default_timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.info(f"Timeout aguardando visibilidade do elemento: {by}={value}")
            return None

    def wait_element_clickable(self, by: str, value: str, timeout: Optional[int] = None) -> Optional[WebDriver]:
        """Aguarda elemento estar clicavel"""
        try:
            timeout = timeout or self.default_timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.info(f"Timeout aguardando elemento clicavel: {by}={value}")
            return None

    def wait_url_contains(self, url_fragment: str, timeout: Optional[int] = None) -> bool:
        """Aguarda URL conter determinado fragmento"""
        try:
            timeout = timeout or self.default_timeout
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(url_fragment)
            )
            return True
        except TimeoutException:
            logger.info(f"Timeout aguardando URL conter: {url_fragment}")
            return False

    def wait_url_to_be(self, url: str, timeout: Optional[int] = None) -> bool:
        """Aguarda URL ser exatamente igual ao valor fornecido"""
        try:
            timeout = timeout or self.default_timeout
            WebDriverWait(self.driver, timeout).until(
                EC.url_to_be(url)
            )
            return True
        except TimeoutException:
            logger.info(f"Timeout aguardando URL ser: {url}")
            return False

    def element_exists(self, by: str, value: str, timeout: int = 5) -> bool:
        """Verifica se elemento existe no DOM"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def click_element(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        """Aguarda elemento ficar clicavel e clica nele"""
        try:
            element = self.wait_element_clickable(by, value, timeout)
            if element:
                element.click()
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao clicar no elemento {by}={value}: {str(e)}")
            return False

    def send_keys_to_element(self, by: str, value: str, text: str, timeout: Optional[int] = None, clear_first: bool = True) -> bool:
        """Aguarda elemento e envia texto para ele"""
        try:
            element = self.wait_element_visible(by, value, timeout)
            if element:
                if clear_first:
                    element.clear()
                element.send_keys(text)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar texto para elemento {by}={value}: {str(e)}")
            return False


class BCLegalLoft:
    """
    Classe RPA para automacao do sistema BCLegal - Cliente Loft

    Funcionalidades:
    - Login via SSO (Single Sign-On)
    - Login com usuario/senha tradicional
    - Autenticacao integrada
    - Navegacao no portal BCLegal
    """

    def __init__(self, usuario: str = "", senha: str = "", usar_auth_integrada: bool = False, download_path: str = None):
        """
        Inicializa a classe BCLegalLoft

        Args:
            usuario: Email ou username para login (default: tifany.oliveira)
            senha: Senha do usuario (default: Oliveir@)
            usar_auth_integrada: Se True, usa autenticacao integrada ao inves de usuario/senha
            download_path: Caminho para pasta de downloads (default: ~/Downloads)
        """
        self.driver: Optional[WebDriver] = None
        self.helper: Optional[SeleniumHelper] = None

        # Credenciais padrao
        self.usuario = usuario if usuario else "tifany.oliveira"
        self.senha = senha if senha else "Oliveir@"
        self.usar_auth_integrada = usar_auth_integrada

        # Pasta de downloads
        self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads")

        # URLs do sistema
        self.url_base = "https://loft.bclegal.io"
        self.url_sso = "https://loft.bclegal.io/pre-juridico"
        self.url_signin = f"{self.url_base}/signin-oidc"

        # Configuracoes de timeout
        self.timeout_default = 20
        self.timeout_login = 30
        self.timeout_page_load = 40

    def inicializar_driver(self, driver: WebDriver) -> bool:
        """
        Inicializa o driver do Selenium e o helper

        Args:
            driver: Instancia do WebDriver do Selenium

        Returns:
            bool: True se inicializado com sucesso, False caso contrario
        """
        try:
            self.driver = driver
            self.helper = SeleniumHelper(driver, self.timeout_default)
            logger.info("Driver BCLegal Loft inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar driver: {str(e)}")
            return False

    def acessar_portal(self) -> bool:
        """
        Acessa o portal BCLegal Loft

        Returns:
            bool: True se acessou com sucesso, False caso contrario
        """
        try:
            if not self.driver:
                logger.info("Driver nao inicializado. Execute inicializar_driver() primeiro.")
                return False

            logger.info(f"Acessando portal BCLegal Loft SSO...")
            self.driver.get(self.url_sso)

            # Aguarda pagina de login SSO carregar
            login_page_loaded = self.helper.wait_url_contains("sso.bclegal.io", self.timeout_page_load)

            if login_page_loaded:
                logger.info("Pagina de autenticacao SSO carregada")
                return True

            logger.error("Falha ao carregar pagina de autenticacao SSO")
            return False

        except WebDriverException as e:
            logger.error(f"Erro ao acessar portal: {str(e)}")
            return False

    def verificar_pagina_login(self) -> bool:
        """
        Verifica se esta na pagina de login

        Returns:
            bool: True se esta na pagina de login, False caso contrario
        """
        try:
            # Verifica titulo da pagina
            titulo_existe = self.helper.wait_element(
                By.ID,
                "kc-page-title",
                timeout=10
            )

            # Verifica formulario de login
            form_existe = self.helper.element_exists(By.ID, "kc-form-login")

            if titulo_existe and form_existe:
                logger.info("Pagina de login detectada com sucesso")
                return True

            logger.info("Pagina de login nao detectada")
            return False

        except Exception as e:
            logger.error(f"Erro ao verificar pagina de login: {str(e)}")
            return False

    def login_com_autenticacao_integrada(self) -> bool:
        """
        Realiza login usando autenticacao integrada (SSO)

        Returns:
            bool: True se login bem-sucedido, False caso contrario
        """
        try:
            logger.info("Iniciando login com autenticacao integrada...")

            # Aguarda botao de autenticacao integrada estar disponivel
            btn_auth_integrada = self.helper.wait_element_clickable(
                By.ID,
                "social-loft",
                timeout=self.timeout_login
            )

            if not btn_auth_integrada:
                logger.error("Botao de autenticacao integrada nao encontrado")
                return False

            logger.info("Clicando em 'Autenticacao Integrada'")
            btn_auth_integrada.click()

            # Aguarda redirecionamento ou conclusao do login
            login_concluido = self._verificar_login_concluido()

            if login_concluido:
                logger.info("Login com autenticacao integrada concluido com sucesso")
                return True

            logger.error("Falha no login com autenticacao integrada")
            return False

        except Exception as e:
            logger.info(f"Erro no login com autenticacao integrada: {str(e)}")
            return False

    def login_com_sof(self) -> bool:
        """
        Realiza login usando SOF (Softecnologia)

        Returns:
            bool: True se login bem-sucedido, False caso contrario
        """
        try:
            logger.info("Iniciando login com SOF...")

            # Aguarda botao SOF estar disponivel
            btn_sof = self.helper.wait_element_clickable(
                By.ID,
                "social-softecnologia",
                timeout=self.timeout_login
            )

            if not btn_sof:
                logger.error("Botao SOF nao encontrado")
                return False

            logger.info("Clicando em 'SOF'")
            btn_sof.click()

            # Aguarda redirecionamento ou conclusao do login
            login_concluido = self._verificar_login_concluido()

            if login_concluido:
                logger.info("Login com SOF concluido com sucesso")
                return True

            logger.error("Falha no login com SOF")
            return False

        except Exception as e:
            logger.info(f"Erro no login com SOF: {str(e)}")
            return False

    def login_com_usuario_senha(self) -> bool:
        """
        Realiza login usando usuario e senha tradicionais

        Returns:
            bool: True se login bem-sucedido, False caso contrario
        """
        try:
            if not self.usuario or not self.senha:
                logger.info("Usuario ou senha nao fornecidos")
                return False

            logger.info(f"Iniciando login com usuario/senha para: {self.usuario}")

            # Aguarda e preenche campo de usuario
            campo_usuario = self.helper.wait_element_visible(
                By.ID,
                "username",
                timeout=self.timeout_login
            )

            if not campo_usuario:
                logger.error("Campo de usuario nao encontrado")
                return False

            logger.info("Preenchendo campo de usuario")
            campo_usuario.clear()
            campo_usuario.send_keys(self.usuario)

            # Aguarda e preenche campo de senha
            campo_senha = self.helper.wait_element_visible(
                By.ID,
                "password",
                timeout=10
            )

            if not campo_senha:
                logger.error("Campo de senha nao encontrado")
                return False

            logger.info("Preenchendo campo de senha")
            campo_senha.clear()
            campo_senha.send_keys(self.senha)

            # Aguarda botao de login ficar habilitado e clica
            btn_login = self.helper.wait_element(
                By.ID,
                "kc-login",
                timeout=10
            )

            if not btn_login:
                logger.error("Botao de login nao encontrado")
                return False

            # Aguarda botao ficar habilitado (sem atributo disabled)
            WebDriverWait(self.driver, 10).until_not(
                EC.element_attribute_to_include((By.ID, "kc-login"), "disabled")
            )

            logger.info("Clicando em 'Sign In'")
            btn_login.click()

            # Aguarda conclusao do login
            login_concluido = self._verificar_login_concluido()

            if login_concluido:
                logger.info("Login com usuario/senha concluido com sucesso")
                return True

            logger.error("Falha no login com usuario/senha")
            return False

        except Exception as e:
            logger.info(f"Erro no login com usuario/senha: {str(e)}")
            return False

    def _verificar_login_concluido(self, timeout: Optional[int] = None) -> bool:
        """
        Verifica se o login foi concluido com sucesso

        Args:
            timeout: Timeout personalizado para verificacao

        Returns:
            bool: True se login concluido, False caso contrario
        """
        try:
            timeout = timeout or self.timeout_page_load

            # Aguarda redirecionamento para a aplicacao principal
            # (sai do dominio SSO e volta para bclegal.io)
            login_ok = self.helper.wait_url_contains("loft.bclegal.io", timeout)

            if login_ok:
                # Verifica se nao esta mais na pagina de login
                url_atual = self.driver.current_url
                if "sso.bclegal.io" not in url_atual:
                    logger.info(f"Login concluido. URL atual: {url_atual}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar login concluido: {str(e)}")
            return False

    def esta_logado(self) -> bool:
        """
        Verifica se o usuario esta logado no sistema

        Returns:
            bool: True se esta logado, False caso contrario
        """
        try:
            if not self.driver:
                return False

            url_atual = self.driver.current_url

            # Se nao esta na pagina de SSO, provavelmente esta logado
            if "sso.bclegal.io" not in url_atual and "loft.bclegal.io" in url_atual:
                logger.info("Usuario esta logado no sistema")
                return True

            logger.info("Usuario nao esta logado")
            return False

        except Exception as e:
            logger.error(f"Erro ao verificar se esta logado: {str(e)}")
            return False

    def fazer_login(self) -> bool:
        """
        Metodo principal de login - escolhe automaticamente o metodo apropriado

        Returns:
            bool: True se login bem-sucedido, False caso contrario
        """
        try:
            # Acessa o portal
            if not self.acessar_portal():
                return False

            # Verifica se esta na pagina de login
            if not self.verificar_pagina_login():
                # Pode ja estar logado
                if self.esta_logado():
                    logger.info("Usuario ja esta logado")
                    return True
                logger.info("Nao foi possivel detectar a pagina de login")
                return False

            # Escolhe metodo de login
            if self.usar_auth_integrada:
                return self.login_com_autenticacao_integrada()
            else:
                return self.login_com_usuario_senha()

        except Exception as e:
            logger.info(f"Erro no processo de login: {str(e)}")
            return False

    def logout(self) -> bool:
        """
        Realiza logout do sistema

        Returns:
            bool: True se logout bem-sucedido, False caso contrario
        """
        try:
            logger.info("Executando logout...")

            # Implementar logica de logout conforme necessario
            # Pode variar dependendo da interface do BCLegal

            # Por enquanto, apenas limpa cookies e volta para pagina inicial
            self.driver.delete_all_cookies()
            self.driver.get(self.url_base)

            logger.info("Logout executado")
            return True

        except Exception as e:
            logger.error(f"Erro ao fazer logout: {str(e)}")
            return False

    def navegar_para(self, url: str, aguardar_carregar: bool = True) -> bool:
        """
        Navega para uma URL especifica

        Args:
            url: URL de destino
            aguardar_carregar: Se True, aguarda a pagina carregar completamente

        Returns:
            bool: True se navegacao bem-sucedida, False caso contrario
        """
        try:
            logger.info(f"Navegando para: {url}")
            self.driver.get(url)

            if aguardar_carregar:
                # Aguarda o document.readyState ser "complete"
                WebDriverWait(self.driver, self.timeout_page_load).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )

            logger.info(f"Navegacao concluida. URL atual: {self.driver.current_url}")
            return True

        except Exception as e:
            logger.error(f"Erro ao navegar para {url}: {str(e)}")
            return False

    def aguardar_elemento(self, by: str, value: str, timeout: Optional[int] = None) -> Optional[WebDriver]:
        """
        Aguarda um elemento especifico aparecer na pagina

        Args:
            by: Tipo de seletor (By.ID, By.XPATH, etc)
            value: Valor do seletor
            timeout: Timeout personalizado

        Returns:
            WebElement se encontrado, None caso contrario
        """
        if self.helper:
            return self.helper.wait_element(by, value, timeout)
        return None

    def clicar_elemento(self, by: str, value: str, timeout: Optional[int] = None) -> bool:
        """
        Aguarda e clica em um elemento

        Args:
            by: Tipo de seletor (By.ID, By.XPATH, etc)
            value: Valor do seletor
            timeout: Timeout personalizado

        Returns:
            bool: True se clicou com sucesso, False caso contrario
        """
        if self.helper:
            return self.helper.click_element(by, value, timeout)
        return False

    def preencher_campo(self, by: str, value: str, text: str, timeout: Optional[int] = None) -> bool:
        """
        Aguarda e preenche um campo de texto

        Args:
            by: Tipo de seletor (By.ID, By.XPATH, etc)
            value: Valor do seletor
            text: Texto a ser preenchido
            timeout: Timeout personalizado

        Returns:
            bool: True se preencheu com sucesso, False caso contrario
        """
        if self.helper:
            return self.helper.send_keys_to_element(by, value, text, timeout)
        return False

    def acessar_gestao_despejos(self) -> bool:
        """
        Acessa a pagina de Gestao de Despejos (Pre-Juridico)

        Returns:
            bool: True se acessou com sucesso, False caso contrario
        """
        try:
            logger.info("Acessando Gestao de Despejos...")

            # Navega diretamente para a URL de pre-juridico
            url_gestao = f"{self.url_base}/pre-juridico"

            if not self.navegar_para(url_gestao, aguardar_carregar=True):
                logger.error("Falha ao navegar para Gestao de Despejos")
                return False

            # Aguarda o titulo da pagina estar presente
            titulo_pagina = self.helper.wait_element(
                By.XPATH,
                "/html/body/div[2]/div[1]/div/div[3]/div/ul/li/div/div/div/span",
                timeout=self.timeout_page_load
            )

            if titulo_pagina:
                texto_titulo = titulo_pagina.text
                logger.info(f"Pagina carregada: {texto_titulo}")

                if "LIMA E FEIGELSON ADVOGADOS ASSOCIADOS" in texto_titulo.upper() or "LIMA E FEIGELSON" in texto_titulo.upper():
                    logger.info("Acesso a Gestao de Despejos realizado com sucesso")
                    
                    gestao_despejos = self.helper.wait_element_clickable(By.XPATH, "/html/body/div[2]/div[2]/div[3]/div/ul/li/div[2]/div/ul/li[1]/div/a/span")
                    if gestao_despejos:
                        gestao_despejos.click()
                        return True

            logger.info("Nao foi possivel verificar se esta na pagina de Gestao de Despejos")
            return False

        except Exception as e:
            logger.error(f"Erro ao acessar Gestao de Despejos: {str(e)}")
            return False

    def buscar_contrato(self, numero_contrato: str) -> bool:
        """
        Busca um contrato especifico na Gestao de Despejos

        Args:
            numero_contrato: Numero do contrato a ser buscado (ex: 670122)

        Returns:
            bool: True se busca foi executada com sucesso, False caso contrario
        """
        try:
            logger.info(f"Buscando contrato: {numero_contrato}")

            # Aguarda o campo CodContrato estar disponivel
            campo_contrato = self.helper.wait_element_visible(
                By.ID,
                "CodContrato",
                timeout=self.timeout_default
            )

            if not campo_contrato:
                logger.error("Campo CodContrato nao encontrado")
                return False

            logger.info("Preenchendo campo de contrato...")
            campo_contrato.clear()
            campo_contrato.send_keys(numero_contrato)

            # Aguarda um momento para o campo processar o valor
            WebDriverWait(self.driver, 2).until(
                lambda _: campo_contrato.get_attribute("value") == numero_contrato
            )

            # Localiza e clica no botao Buscar
            # O botao tem type="Submit" e texto "Buscar"
            btn_buscar = self.helper.wait_element_clickable(
                By.XPATH,
                "//button[@type='Submit' and .//span[text()='Buscar']]",
                timeout=10
            )

            if not btn_buscar:
                logger.error("Botao Buscar nao encontrado")
                return False

            logger.info("Clicando no botao Buscar...")
            btn_buscar.click()

            # Aguarda a pagina processar a busca
            # Aguarda a grid de resultados estar presente
            grid_resultados = self.helper.wait_element(
                By.CLASS_NAME,
                "rz-data-grid",
                timeout=self.timeout_page_load
            )

            if grid_resultados:
                logger.info(f"Busca por contrato {numero_contrato} executada com sucesso")
                return True

            logger.error("Grid de resultados nao encontrada")
            return False

        except Exception as e:
            logger.error(f"Erro ao buscar contrato: {str(e)}")
            return False

    def verificar_resultado_busca(self, numero_contrato: str) -> bool:
        """
        Verifica se o contrato aparece nos resultados da busca

        Args:
            numero_contrato: Numero do contrato a verificar

        Returns:
            bool: True se contrato foi encontrado nos resultados, False caso contrario
        """
        try:
            logger.info(f"Verificando se contrato {numero_contrato} aparece nos resultados...")

            # Procura pelo badge com o numero do contrato na tabela
            # Os contratos aparecem em badges com classe rz-badge-success
            contrato_badge = self.helper.wait_element(
                By.XPATH,
                f"//span[contains(@class, 'rz-badge-success') and text()='{numero_contrato}']",
                timeout=10
            )

            if contrato_badge:
                logger.info(f"Contrato {numero_contrato} encontrado nos resultados!")
                return True

            logger.info(f"Contrato {numero_contrato} nao encontrado nos resultados")
            return False

        except Exception as e:
            logger.error(f"Erro ao verificar resultado da busca: {str(e)}")
            return False

    def acessa_informacoes_pasta(self) -> bool:
        """
        Clica em botão para acessar mais informações da pasta

        Returns:
            bool: True se a aba foi acessada, False caso contrario
        """
        try:
            logger.info(f"Iniciando busca por botão de mais informacoes da pasta")

            edit_button = self.helper.wait_element_clickable(By.XPATH, "/html/body/div[2]/div[3]/div/div/div[5]/div/div/div/table/tbody/tr/td[1]/span/button/span/i")
            if edit_button:
                logger.info("Botao de mais informações encontrado com sucesso.")
                self.driver.execute_script("arguments[0].click();", edit_button)
                logger.info("Botão de mais informações clicado com sucesso.")
                return True
                
            logger.info(f"Botão de mais informações nao encontrado nos resultados")
            return False

        except Exception as e:
            logger.error(f"Erro ao acessar mais informacoes da pasta: {str(e)}")
            return False

    def acessa_aba_documentos(self) -> bool:
        """
        Clica em botão para acessar documentos da pasta

        Returns:
            bool: True se os documentos foram acessados com sucesso, False caso contrario
        """
        try:
            logger.info(f"Iniciando busca por aba de documentos da pasta")

            doc_button = self.helper.wait_element_clickable(By.XPATH, "/html/body/div[1]/div[1]/div/form/div[1]/div[1]/div/ul/li[5]/a")
            if doc_button:
                logger.info("Aba de documentos da pasta encontrado com sucesso.")
                self.driver.execute_script("arguments[0].click();", doc_button)
                logger.info("Aba de documentos da pasta clicado com sucesso.")
                return True

            logger.info(f"Aba de documentos da pasta nao encontrado nos resultados")
            return False

        except Exception as e:
            logger.error(f"Erro ao acessar aba de documentos da pasta: {str(e)}")
            return False

    def fechar_janela_documentos(self) -> bool:
        """
        Fecha a janela de documentos da pasta

        Returns:
            bool: True se fechou com sucesso, False caso contrario
        """
        try:
            logger.info("Fechando janela de documentos...")

            # Aguarda o botao de fechar estar clicavel
            btn_fechar = self.helper.wait_element_clickable(
                By.XPATH,
                "/html/body/div[1]/div[1]/div/form/div[2]/div/div/button[5]",
                timeout=10
            )

            if not btn_fechar:
                logger.error("Botao de fechar janela nao encontrado")
                return False

            # Aguarda o botao estar habilitado
            WebDriverWait(self.driver, 10).until(
                lambda _: btn_fechar.is_displayed() and btn_fechar.is_enabled()
            )

            # Clica no botao de fechar
            logger.info("Clicando no botao de fechar janela...")
            self.driver.execute_script("arguments[0].click();", btn_fechar)

            # Aguarda a janela fechar (verifica se o elemento nao esta mais visivel)
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div/form"))
            )

            logger.info("Janela de documentos fechada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao fechar janela de documentos: {str(e)}")
            # Tenta click normal como fallback
            try:
                btn_fechar.click()
                logger.info("Janela fechada com click normal")
                return True
            except Exception as e2:
                logger.error(f"Erro no fallback de fechar janela: {str(e2)}")
                return False

    def busca_e_baixa_documentos(self, numero_processo: str) -> list:
        """
        Seleciona todos os documentos e faz download,
        renomeando-os seguindo o padrão do COGNA.

        Args:
            numero_processo: Número do processo/contrato para renomear arquivos

        Returns:
            list: Lista de dicionários com metadados dos documentos baixados
        """
        try:
            logger.info("=" * 80)
            logger.info(f"Iniciando download de TODOS os documentos para processo: {numero_processo}")
            logger.info("=" * 80)

            # Lista para armazenar metadados dos documentos
            documentos_metadados = []

            # Snapshot dos arquivos antes do download
            arquivos_antes = set(os.listdir(self.download_path)) if os.path.exists(self.download_path) else set()

            # Etapa 1: Aguardar a tabela de documentos carregar
            logger.info("[ETAPA 1/3] Aguardando tabela de documentos carregar...")
            tabela_documentos = self.helper.wait_element(
                By.XPATH,
                "//div[contains(@class, 'rz-data-grid') and contains(@class, 'rz-datatable-scrollable')]",
                timeout=self.timeout_page_load
            )

            if not tabela_documentos:
                logger.error("Tabela de documentos nao encontrada")
                return []

            logger.info("Tabela de documentos carregada com sucesso")

            # Etapa 2: Clicar em "Selecionar Todos"
            logger.info("[ETAPA 2/3] Clicando em 'Selecionar Todos'...")

            btn_selecionar_todos = self.helper.wait_element_clickable(
                By.XPATH,
                "/html/body/div[1]/div[1]/div/form/div[1]/div[1]/div/div/div/div[2]/div[3]/div[2]/button[1]/span/span",
                timeout=10
            )

            if not btn_selecionar_todos:
                logger.error("Botao 'Selecionar Todos' nao encontrado")
                return []

            # Scroll até o botão
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn_selecionar_todos)
            time.sleep(1)

            # Clica no botão
            try:
                btn_selecionar_todos.click()
                logger.info("Botao 'Selecionar Todos' clicado com sucesso")
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", btn_selecionar_todos)
                logger.info("Botao 'Selecionar Todos' clicado com JavaScript")

            time.sleep(2)  # Aguarda seleção

            # Etapa 3: Clicar em "Download Selecionados"
            logger.info("[ETAPA 3/3] Clicando em 'Download Selecionados'...")

            btn_download = self.helper.wait_element_clickable(
                By.XPATH,
                "/html/body/div[1]/div[1]/div/form/div[1]/div[1]/div/div/div/div[2]/div[3]/div[2]/button[3]/span/span",
                timeout=10
            )

            if not btn_download:
                logger.error("Botao 'Download Selecionados' nao encontrado")
                return []

            # Scroll até o botão
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn_download)
            time.sleep(1)

            # Clica no botão
            try:
                btn_download.click()
                logger.info("Botao 'Download Selecionados' clicado com sucesso")
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", btn_download)
                logger.info("Botao 'Download Selecionados' clicado com JavaScript")

            # Aguarda downloads completarem
            logger.info("Aguardando downloads completarem (15 segundos)...")
            time.sleep(15)

            # Identifica novos arquivos
            logger.info("Identificando arquivos baixados...")
            arquivos_atuais = set(os.listdir(self.download_path)) if os.path.exists(self.download_path) else set()
            novos_arquivos = arquivos_atuais - arquivos_antes

            logger.info(f"Novos arquivos baixados: {len(novos_arquivos)}")

            # Cria pasta temp_downloads
            temp_dir = os.path.join(os.getcwd(), "temp_downloads")
            os.makedirs(temp_dir, exist_ok=True)

            # Limpa o número do processo
            numero_limpo = numero_processo.replace(".", "").replace("-", "").replace(" ", "")

            # Processa arquivos baixados
            arquivos_para_processar = []

            for arquivo in sorted(novos_arquivos):
                if arquivo.endswith(".crdownload") or arquivo.endswith(".tmp"):
                    continue

                caminho_arquivo = os.path.join(self.download_path, arquivo)

                # Verifica se é um arquivo ZIP
                if arquivo.lower().endswith('.zip'):
                    logger.info(f"Arquivo ZIP detectado: {arquivo}")
                    logger.info("Descompactando ZIP...")

                    try:
                        # Cria pasta temporária para extração
                        extract_dir = os.path.join(self.download_path, f"extract_{numero_limpo}")
                        os.makedirs(extract_dir, exist_ok=True)

                        # Descompacta o ZIP
                        with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                            logger.info(f"ZIP descompactado em: {extract_dir}")

                        # Lista arquivos extraídos
                        for root, dirs, files in os.walk(extract_dir):
                            for file in files:
                                # Ignora arquivos ocultos e de sistema
                                if not file.startswith('.') and not file.startswith('__MACOSX'):
                                    arquivo_extraido = os.path.join(root, file)
                                    arquivos_para_processar.append((file, arquivo_extraido))

                        logger.info(f"Total de arquivos extraídos: {len(arquivos_para_processar)}")

                        # Remove o ZIP após extração
                        os.remove(caminho_arquivo)
                        logger.info("Arquivo ZIP removido após extração")

                    except Exception as e:
                        logger.error(f"Erro ao descompactar ZIP: {e}")
                        # Se falhar, trata como arquivo normal
                        arquivos_para_processar.append((arquivo, caminho_arquivo))

                else:
                    # Arquivo não é ZIP, adiciona diretamente
                    arquivos_para_processar.append((arquivo, caminho_arquivo))

            # Renomeia e move todos os arquivos
            logger.info(f"Processando {len(arquivos_para_processar)} arquivo(s)...")

            for idx, (nome_original, caminho_original) in enumerate(arquivos_para_processar, start=1):
                try:
                    nome_base, extensao = os.path.splitext(nome_original)

                    # Limpa o nome original preservando o teor do documento
                    # Remove caracteres especiais, mantém apenas alfanuméricos, espaços, hífens e underscores
                    import re
                    nome_limpo = re.sub(r'[^\w\s\-]', '', nome_base)
                    nome_limpo = nome_limpo.replace(' ', '_')
                    nome_limpo = re.sub(r'_+', '_', nome_limpo)  # Remove underscores duplicados
                    nome_limpo = nome_limpo.strip('_')  # Remove underscores no início e fim

                    # Padrão: numerodoprocesso_nomeoriginal.extensao
                    novo_nome = f"{numero_limpo}_{nome_limpo}{extensao}"
                    caminho_novo = os.path.join(temp_dir, novo_nome)

                    # Move o arquivo
                    shutil.move(caminho_original, caminho_novo)
                    logger.info(f"[{idx}/{len(arquivos_para_processar)}] Arquivo processado: {novo_nome}")

                    # Adiciona metadados
                    documentos_metadados.append({
                        "numero_linha": idx,
                        "nome_arquivo": nome_original,
                        "tipo_documento": nome_limpo,  # Usa o nome original limpo como tipo
                        "caminho_arquivo": caminho_novo,
                        "nome_arquivo_final": novo_nome
                    })

                except Exception as e:
                    logger.warning(f"Erro ao processar arquivo '{nome_original}': {e}")

            # Limpa pasta de extração se existir
            extract_dir = os.path.join(self.download_path, f"extract_{numero_limpo}")
            if os.path.exists(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                    logger.info("Pasta de extração temporária removida")
                except Exception as e:
                    logger.warning(f"Erro ao remover pasta temporária: {e}")

            logger.info("=" * 80)
            logger.info(f"Download concluído! {len(documentos_metadados)} documento(s) processado(s)")
            logger.info("=" * 80)

            return documentos_metadados

        except Exception as e:
            logger.error(f"Erro ao buscar e baixar documentos: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []       




    def baixa_documento_anexo(self, numero_processo: str, pasta: str = None, codigo_pasta: str = None) -> list:
        """
        Executa o fluxo completo de baixa de documentos:
        1. Acessa Gestão de Despejos
        2. Busca o contrato
        3. Verifica resultado
        4. Acessa informações da pasta
        5. Acessa aba de documentos
        6. Baixa e renomeia todos os documentos

        Args:
            numero_processo (str): Número do processo/contrato
            pasta (str, optional): Pasta/folder no ADVWin para armazenamento
            codigo_pasta (str, optional): Código da pasta no ADVWin (codigo_comp)

        Returns:
            list: Lista de dicionários com metadados dos documentos baixados
        """
        try:
            logger.info(f"Iniciando fluxo de baixa de documentos para contrato: {numero_processo}")

            # 1. Acessar Gestão de Despejos
            if not self.acessar_gestao_despejos():
                logger.error("Erro ao acessar Gestão de Despejos")
                return []
            logger.info("Gestão de Despejos acessada")

            # 2. Buscar contrato
            if not self.buscar_contrato(numero_processo):
                logger.error(f"Erro ao buscar contrato {numero_processo}")
                return []
            logger.info(f"Contrato {numero_processo} encontrado")

            # 3. Verificar resultado
            if not self.verificar_resultado_busca(numero_processo):
                logger.error(f"Erro ao verificar resultado do contrato {numero_processo}")
                return []
            logger.info(f"Resultado verificado")

            # 4. Acessar informações da pasta
            if not self.acessa_informacoes_pasta():
                logger.error("Erro ao acessar informações da pasta")
                return []
            logger.info("Informações da pasta acessadas")

            # 5. Acessar aba de documentos
            if not self.acessa_aba_documentos():
                logger.error("Erro ao acessar aba de documentos")
                return []
            logger.info("Aba de documentos acessada")

            time.sleep(3)  # Aguarda aba carregar

            # 6. Baixar e renomear documentos
            documentos = self.busca_e_baixa_documentos(numero_processo)

            if not documentos or len(documentos) == 0:
                logger.error(f"Nenhum documento foi baixado do contrato {numero_processo}")
                return []

            # Adiciona pasta e codigo_pasta em cada documento (se fornecidos)
            if pasta or codigo_pasta:
                for doc in documentos:
                    if pasta:
                        doc["pasta"] = pasta
                    if codigo_pasta:
                        doc["codigo_pasta"] = codigo_pasta

            logger.info(f"Fluxo de baixa de documentos concluído!")
            logger.info(f"Total de documentos baixados: {len(documentos)}")

            return documentos

        except Exception as e:
            logger.error(f"Erro geral no fluxo de baixa de documentos do contrato {numero_processo}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def limpar_filtros_busca(self) -> bool:
        """
        Limpa os filtros de busca na Gestao de Despejos

        Returns:
            bool: True se limpou com sucesso, False caso contrario
        """
        try:
            logger.info("Limpando filtros de busca...")

            # Limpa campo de contrato
            campo_contrato = self.helper.wait_element_visible(
                By.ID,
                "CodContrato",
                timeout=10
            )

            if campo_contrato:
                campo_contrato.clear()
                logger.error("Campo de contrato limpo")

            # Limpa campo de palavra-chave
            campo_palavra_chave = self.helper.wait_element_visible(
                By.ID,
                "PesquisaTexto",
                timeout=5
            )

            if campo_palavra_chave:
                campo_palavra_chave.clear()
                logger.error("Campo de palavra-chave limpo")

            logger.info("Filtros de busca limpos com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao limpar filtros de busca: {str(e)}")
            return False


# Exemplo de uso
if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # Configuracao do logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configuracao do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Cria instancia do driver
    driver = webdriver.Chrome(options=chrome_options)

    # Cria instancia do BCLegal Loft com credenciais padrao
    # usuario: tifany.oliveira, senha: Oliveir@
    bclegal = BCLegalLoft()

    # Inicializa driver
    if bclegal.inicializar_driver(driver):
        # Faz login
        if bclegal.fazer_login():
            logger.info("Login realizado com sucesso!")

            # Acessa Gestao de Despejos
            if bclegal.acessar_gestao_despejos():
                logger.info("Gestao de Despejos acessada!")

                # Busca contrato 670122
                if bclegal.buscar_contrato("670122"):
                    logger.info("Busca executada com sucesso!")

        else:
            logger.error("Falha no login")

    # Fecha o navegador (comentado para debug)
    # driver.quit()
