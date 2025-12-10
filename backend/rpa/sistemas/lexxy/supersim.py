import os
import time
import logging
import shutil
import traceback
import zipfile
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "logs"))
downloads_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "downloads", "lexxy_supersim"))
os.makedirs(log_dir, exist_ok=True)
os.makedirs(downloads_dir, exist_ok=True)

log_filename = os.path.join(
    log_dir, f"lexxy_supersim_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("RPA_LEXXY")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class useSeleniumHelper:
    """Classe auxiliar para operacoes Selenium comuns"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.logger = logging.getLogger("RPA_LEXXY.Helper")

    def f_el(self, by: str, value: str):
        """Encontra um elemento unico"""
        try:
            element = self.driver.find_element(by, value)
            return element
        except NoSuchElementException:
            self.logger.warning(f"Elemento nao encontrado: {by}={value}")
            return None

    def f_els(self, by: str, value: str):
        """Encontra multiplos elementos"""
        try:
            elements = self.driver.find_elements(by, value)
            return elements
        except NoSuchElementException:
            return None

    def check_elemento_existe(self, by: str, value: str) -> bool:
        """Verifica se um elemento existe na pagina"""
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def aguardar_elemento(self, by: str, value: str, timeout: int = 10) -> bool:
        """Aguarda ate que um elemento esteja presente na pagina"""
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True if elemento else False
        except TimeoutException:
            self.logger.warning(f"Timeout aguardando elemento: {by}={value}")
            return False

    def aguardar_elemento_clicavel(self, by: str, value: str, timeout: int = 10) -> bool:
        """Aguarda ate que um elemento seja clicavel"""
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return True if elemento else False
        except TimeoutException:
            self.logger.warning(f"Timeout aguardando elemento clicavel: {by}={value}")
            return False


class LexxySuperSim:
    """Classe para automacao do sistema Lexxy SuperSim"""

    def __init__(self, driver: Optional[WebDriver] = None, downloads_dir  = None) -> None:
        """
        Inicializa a classe LexxySuperSim

        Args:
            driver: WebDriver do Selenium (opcional). Se nao fornecido, sera criado automaticamente.
        """
        self.url_producao = "https://app.lexxy.com.br/login"
        self.driver = driver
        self.helper = None
        self.logger = logging.getLogger("RPA_LEXXY.LexxySuperSim")
        self.downloads_dir = downloads_dir

        self.user = os.getenv("LEXXY_USER", "")
        self.password = os.getenv("LEXXY_PASSWORD", "")

        if not self.user or not self.password:
            raise ValueError(
                "Credenciais nao encontradas! "
                "Configure LEXXY_USER e LEXXY_PASSWORD no arquivo .env"
            )

    def criar_driver_local(self) -> WebDriver:
        """
        Cria uma instancia local do Chrome WebDriver

        Returns:
            WebDriver configurado
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")

            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)

            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

            self.logger.info("WebDriver Chrome inicializado com sucesso")
            self.logger.info(f"Diretorio de downloads: {downloads_dir}")
            return driver

        except Exception as e:
            self.logger.error(f"Erro ao inicializar o WebDriver: {e}")
            self.logger.error("Verifique se o Google Chrome esta instalado.")
            raise

    def criar_driver_selenoid(self, session_name: str = "Lexxy SuperSim") -> WebDriver:
        """
        Cria uma instancia remota do Chrome via Selenoid

        Args:
            session_name: Nome da sessao no Selenoid

        Returns:
            WebDriver configurado
        """
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

        selenoid_servers = [
            "http://autodevti.ddns.net/wd/hub",
            "http://201.54.10.172:44/wd/hub",
        ]

        for server_url in selenoid_servers:
            try:
                self.logger.info(f"Tentando conectar ao Selenoid: {server_url}")
                driver = webdriver.Remote(
                    command_executor=server_url,
                    options=chrome_options,
                )

                session_id = driver.session_id
                self.logger.info(f"Sessao '{session_name}' criada: {session_id}")
                self.logger.info(f"Servidor: {server_url}")
                return driver

            except WebDriverException as e:
                self.logger.error(f"Falha ao conectar: {server_url}")
                self.logger.error(f"Erro: {str(e)}")

                if server_url == selenoid_servers[-1]:
                    raise Exception(
                        "Nao foi possivel conectar a nenhum servidor Selenoid disponivel."
                    )
                self.logger.info("Tentando proximo servidor...")
                continue

    def ENTRAR_NO_SISTEMA(self, usar_selenoid: bool = False, session_name: str = "Lexxy SuperSim"):
        """
        Inicializa o WebDriver e acessa a pagina de login

        Args:
            usar_selenoid: Se True, usa Selenoid remoto. Se False, usa Chrome local.
            session_name: Nome da sessao (apenas para Selenoid)
        """
        try:
            if usar_selenoid:
                self.driver = self.criar_driver_selenoid(session_name)
            else:
                if self.driver is None:
                    self.driver = self.criar_driver_local()

            self.helper = useSeleniumHelper(self.driver)

            self.logger.info(f"Acessando: {self.url_producao}")
            self.driver.get(self.url_producao)
            time.sleep(3)

            self.logger.info("Sistema acessado com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao entrar no sistema: {e}")
            raise

    def LOGIN(self) -> bool:
        """
        Realiza o login no sistema Lexxy

        Returns:
            True se login foi bem-sucedido, False caso contrario
        """
        try:
            self.logger.info("Iniciando processo de login...")

            if not self.helper.aguardar_elemento(By.CLASS_NAME, "sign-in__form", timeout=15):
                self.logger.error("Formulario de login nao encontrado")
                return False

            self.logger.info("Formulario de login encontrado")

            input_email = self.helper.f_el(By.ID, "e-mail")
            if not input_email:
                self.logger.error("Campo de email nao encontrado")
                return False

            input_email.clear()
            input_email.send_keys(self.user)
            self.logger.info(f"Email preenchido: {self.user}")
            time.sleep(1)

            input_senha = self.helper.f_el(By.ID, "password")
            if not input_senha:
                self.logger.error("Campo de senha nao encontrado")
                return False

            input_senha.clear()
            input_senha.send_keys(self.password)
            self.logger.info("Senha preenchida")
            time.sleep(1)

            btn_entrar = self.helper.f_el(By.CSS_SELECTOR, "button[type='submit']")
            if not btn_entrar:
                self.logger.error("Botao de entrar nao encontrado")
                return False

            self.logger.info("Clicando no botao Entrar...")
            btn_entrar.click()
            time.sleep(5)

            return self.CONFIRM_LOGIN()

        except Exception as e:
            self.logger.error(f"Erro durante o login: {e}")
            return False

    def CONFIRM_LOGIN(self) -> bool:
        """
        Confirma se o login foi realizado com sucesso

        Returns:
            True se logado, False caso contrario
        """
        try:
            self.logger.info("Verificando se login foi bem-sucedido...")

            time.sleep(3)

            url_atual = self.driver.current_url
            self.logger.info(f"URL atual: {url_atual}")

            if "login" not in url_atual.lower():
                self.logger.info("Login realizado com sucesso!")
                return True

            if self.helper.check_elemento_existe(By.CLASS_NAME, "error") or \
               self.helper.check_elemento_existe(By.CLASS_NAME, "alert-danger"):
                self.logger.error("Erro de autenticacao detectado")
                return False

            self.logger.warning("Ainda na pagina de login - verifique as credenciais")
            return False

        except Exception as e:
            self.logger.error(f"Erro ao confirmar login: {e}")
            return False

    def ACESSAR_PROCESSOS(self) -> bool:
        """
        Acessa a pagina de processos clicando no card de Processos

        Returns:
            True se acessou com sucesso, False caso contrario
        """
        try:
            self.logger.info("Acessando pagina de processos...")

            time.sleep(2)

            cards = self.helper.f_els(By.CLASS_NAME, "initial-page__card")
            if not cards:
                self.logger.error("Cards da pagina inicial nao encontrados")
                return False

            self.logger.info(f"Encontrados {len(cards)} cards na pagina inicial")

            card_processos = None
            for card in cards:
                try:
                    header = card.find_element(By.CLASS_NAME, "initial-page__card-header")
                    h2 = header.find_element(By.TAG_NAME, "h2")
                    if h2.text == "Processos":
                        card_processos = card
                        self.logger.info("Card de Processos encontrado")
                        break
                except NoSuchElementException:
                    continue

            if not card_processos:
                self.logger.error("Card de Processos nao encontrado")
                return False

            footer = card_processos.find_element(By.CLASS_NAME, "initial-page__card-footer")
            if not footer:
                self.logger.error("Footer do card de Processos nao encontrado")
                return False

            self.logger.info("Clicando no Ver mais do card de Processos...")
            footer.click()
            time.sleep(3)

            url_atual = self.driver.current_url
            self.logger.info(f"URL apos clicar em Processos: {url_atual}")

            if "processo" in url_atual.lower() or url_atual != self.url_producao:
                self.logger.info("Pagina de processos acessada com sucesso!")
                return True
            else:
                self.logger.warning("URL nao mudou apos clicar em Processos")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao acessar processos: {e}")
            import traceback
            traceback.print_exc()
            return False

    def BUSCAR_PROCESSO(self, numero_processo: str) -> bool:
        """
        Busca um processo especifico pelo numero e clica no botao de opcoes

        Args:
            numero_processo: Numero do processo sem formatacao (ex: 00016683620258173120)

        Returns:
            True se encontrou e clicou, False caso contrario
        """
        try:
            self.logger.info(f"Buscando processo: {numero_processo}")

            time.sleep(2)

            input_busca = self.helper.f_el(By.CSS_SELECTOR, "input[placeholder='Busca']")
            if not input_busca:
                self.logger.error("Campo de busca nao encontrado")
                return False

            self.logger.info("Campo de busca encontrado")
            input_busca.clear()
            input_busca.send_keys(numero_processo)
            self.logger.info(f"Numero do processo digitado: {numero_processo}")
            time.sleep(3)

            container = self.helper.f_el(By.CLASS_NAME, "lawsuit-list__container-items")
            if not container:
                self.logger.error("Container de processos nao encontrado")
                return False

            self.logger.info("Container de processos encontrado")

            items = container.find_elements(By.CLASS_NAME, "list-item")
            if not items:
                self.logger.warning("Nenhum processo encontrado na lista")
                return False

            self.logger.info(f"Encontrados {len(items)} processos na lista")

            # Normaliza o numero do processo (remove pontos, tracos e espacos)
            numero_normalizado = numero_processo.replace(".", "").replace("-", "").replace(" ", "")
            self.logger.info(f"Numero normalizado para busca: {numero_normalizado}")

            processo_encontrado = None
            for item in items:
                try:
                    link = item.find_element(By.CLASS_NAME, "list-item__value--link")
                    titulo = link.get_attribute("title")

                    if titulo:
                        # Normaliza o titulo tambem
                        titulo_normalizado = titulo.replace(".", "").replace("-", "").replace(" ", "")
                        self.logger.debug(f"Comparando: {numero_normalizado} com {titulo_normalizado}")

                        # Compara os numeros normalizados
                        if numero_normalizado in titulo_normalizado or titulo_normalizado in numero_normalizado:
                            processo_encontrado = item
                            self.logger.info(f"Processo encontrado: {titulo}")
                            break
                except NoSuchElementException:
                    continue

            if not processo_encontrado:
                self.logger.error(f"Processo {numero_processo} nao encontrado na lista")
                self.logger.error(f"Numero normalizado buscado: {numero_normalizado}")
                return False

            botao_opcoes = processo_encontrado.find_element(By.CLASS_NAME, "list-item-action__trigger")
            if not botao_opcoes:
                self.logger.error("Botao de opcoes nao encontrado")
                return False

            self.logger.info("Clicando no botao de opcoes do processo...")
            botao_opcoes.click()
            time.sleep(2)

            self.logger.info("Botao de opcoes clicado com sucesso!")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao buscar processo: {e}")
            import traceback
            traceback.print_exc()
            return False

    def VER_DETALHES(self) -> bool:
        """
        Clica em Ver Detalhes no menu dropdown que aparece apos clicar nos 3 pontos

        Returns:
            True se clicou com sucesso, False caso contrario
        """
        try:
            self.logger.info("Procurando opcao Ver Detalhes no dropdown...")

            time.sleep(2)

            menu_items = self.helper.f_els(By.CSS_SELECTOR, "div[role='menuitem']")
            if not menu_items:
                self.logger.error("Menu dropdown nao encontrado")
                return False

            self.logger.info(f"Encontrados {len(menu_items)} itens no menu")

            item_ver_detalhes = None
            for item in menu_items:
                try:
                    texto = item.text
                    if "Ver Detalhes" in texto:
                        item_ver_detalhes = item
                        self.logger.info("Opcao Ver Detalhes encontrada")
                        break
                except:
                    continue

            if not item_ver_detalhes:
                dropdown_items = self.helper.f_els(By.CLASS_NAME, "dropdown__content__item")
                if dropdown_items:
                    self.logger.info(f"Tentando alternativa: {len(dropdown_items)} items encontrados")
                    for item in dropdown_items:
                        try:
                            texto = item.text
                            if "Ver Detalhes" in texto or "Detalhes" in texto:
                                item_ver_detalhes = item
                                self.logger.info("Opcao Ver Detalhes encontrada via classe alternativa")
                                break
                        except:
                            continue

            if not item_ver_detalhes:
                self.logger.error("Opcao Ver Detalhes nao encontrada no menu")
                return False

            self.logger.info("Clicando em Ver Detalhes...")
            item_ver_detalhes.click()
            time.sleep(3)

            url_atual = self.driver.current_url
            self.logger.info(f"URL apos clicar em Ver Detalhes: {url_atual}")

            if url_atual != self.url_producao:
                self.logger.info("Pagina de detalhes acessada com sucesso!")
                return True
            else:
                self.logger.warning("URL nao mudou apos clicar em Ver Detalhes")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao clicar em Ver Detalhes: {e}")
            import traceback
            traceback.print_exc()
            return False

    def ACESSAR_ANEXOS(self) -> bool:
        """
        Clica na aba Anexos na pagina de detalhes do processo

        Returns:
            True se acessou com sucesso, False caso contrario
        """
        try:
            self.logger.info("Procurando aba Anexos...")

            time.sleep(2)

            tabs_container = self.helper.f_el(By.CLASS_NAME, "outlined-tabs")
            if not tabs_container:
                self.logger.error("Container de abas nao encontrado")
                return False

            self.logger.info("Container de abas encontrado")

            botoes = tabs_container.find_elements(By.CLASS_NAME, "outlined-tabs__item")
            if not botoes:
                self.logger.error("Nenhuma aba encontrada no container")
                return False

            self.logger.info(f"Encontradas {len(botoes)} abas")

            botao_anexos = None
            for idx, botao in enumerate(botoes):
                try:
                    span = botao.find_element(By.TAG_NAME, "span")
                    texto = span.text
                    self.logger.info(f"Aba {idx}: {texto}")

                    if texto.strip().upper() == "ANEXOS":
                        botao_anexos = botao
                        self.logger.info("Aba Anexos encontrada")
                        break
                except Exception as e:
                    self.logger.warning(f"Erro ao ler aba {idx}: {e}")
                    continue

            if not botao_anexos:
                self.logger.error("Aba Anexos nao encontrada")
                return False

            self.logger.info("Clicando na aba Anexos...")
            botao_anexos.click()
            time.sleep(3)

            url_atual = self.driver.current_url
            self.logger.info(f"URL apos clicar em Anexos: {url_atual}")

            if "anexos" in url_atual.lower():
                self.logger.info("Pagina de anexos acessada com sucesso!")
                return True
            else:
                self.logger.warning("URL nao contem 'anexos'")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao acessar anexos: {e}")
            import traceback
            traceback.print_exc()
            return False

    def BAIXAR_DOCUMENTOS(self, numero_processo: str) -> list:
        """
        Seleciona todos os anexos, clica no botão principal para baixar,
        aguarda a conclusão e renomeia os arquivos baixados.

        Args:
            numero_processo: Numero do processo para nomear os arquivos.

        Returns:
            list: Lista de dicionários com metadados dos documentos baixados, ou lista vazia em caso de erro.
            Cada documento tem a estrutura:
            {
                "numero_linha": int,
                "nome_arquivo": str,
                "tipo_documento": str,
                "caminho_arquivo": str,
                "nome_arquivo_final": str
            }
        """
        try:
            self.logger.info("Iniciando processo de download e renomeação de documentos...")
            wait = WebDriverWait(self.driver, 20)
            downloads_dir = self.downloads_dir # Pega o caminho da pasta de downloads do objeto self

            # Lista para armazenar metadados dos documentos
            documentos_metadados = []

            # 1. ENCONTRAR E SELECIONAR TODOS OS ANEXOS
            try:
                anexos = wait.until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "attachment"))
                )
            except TimeoutException:
                self.logger.warning("Nenhum anexo encontrado na página. Nenhuma ação necessária.")
                return [] # Retorna lista vazia

            self.logger.info(f"Encontrados {len(anexos)} anexos. Selecionando todos...")

            # Armazena snapshot dos arquivos antes do download
            arquivos_antes = set(os.listdir(downloads_dir)) if os.path.exists(downloads_dir) else set()

            documentos_a_baixar = 0
            for idx, anexo in enumerate(anexos, 1):
                try:
                    # Rola até o anexo para garantir visibilidade
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", anexo)
                    time.sleep(0.2) # Pausa para estabilizar a rolagem

                    checkbox = anexo.find_element(By.CSS_SELECTOR, "input[type='checkbox']")

                    if not checkbox.is_selected():
                        # Clique via JS é mais robusto para checkboxes customizados
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        documentos_a_baixar += 1
                        self.logger.info(f"Checkbox {idx} selecionado.")

                except Exception as e:
                    self.logger.error(f"Não foi possível selecionar o anexo {idx}: {e}")
                    continue

            if documentos_a_baixar == 0:
                self.logger.warning("Nenhum documento foi selecionado ou precisava ser baixado.")
                return [] # Retorna lista vazia

            self.logger.info(f"Seleção finalizada. {documentos_a_baixar} documentos marcados para download.")

            # 2. CLICAR NO BOTÃO PRINCIPAL DE DOWNLOAD
            try:
                self.logger.info("Procurando o botão principal 'Baixar selecionados'...")
                download_button_xpath = "//button[contains(text(), 'Baixar selecionados')]"

                botao_principal = wait.until(
                    EC.element_to_be_clickable((By.XPATH, download_button_xpath))
                )

                # Rola até o botão para garantir que está visível
                self.logger.info("Rolando até o botão de download...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_principal)
                time.sleep(1)  # Aguarda a rolagem

                self.logger.info("Botão de download encontrado e habilitado. Clicando...")
                try:
                    botao_principal.click()
                except ElementClickInterceptedException:
                    self.logger.warning("Clique interceptado, tentando via JavaScript...")
                    self.driver.execute_script("arguments[0].click();", botao_principal)

            except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e:
                self.logger.error(f"Não foi possível clicar no botão 'Baixar selecionados': {e}. Tentando com JS.")
                try:
                    botao_js = self.driver.find_element(By.XPATH, download_button_xpath)
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_js)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", botao_js)
                except Exception as js_e:
                    self.logger.error(f"Clique via JS no botão de download também falhou: {js_e}")
                    return []

            # 3. AGUARDAR E RENOMEAR ARQUIVOS
            self.logger.info(f"Comando de download enviado. Aguardando a conclusão de {documentos_a_baixar} arquivos...")
            time.sleep(15)

            self.logger.info("Iniciando processo de renomeação e movimentação...")
            arquivos_atuais = set(os.listdir(downloads_dir)) if os.path.exists(downloads_dir) else set()
            novos_arquivos = arquivos_atuais - arquivos_antes

            self.logger.info(f"Novos arquivos baixados: {len(novos_arquivos)}")

            # Cria pasta temp_downloads se não existir
            temp_dir = os.path.join(os.getcwd(), "temp_downloads")
            os.makedirs(temp_dir, exist_ok=True)

            # Limpa o número do processo (remove pontos, traços e espaços)
            numero_limpo = numero_processo.replace(".", "").replace("-", "").replace(" ", "")

            # Lista para armazenar todos os arquivos a serem processados (pode incluir arquivos extraídos de ZIP)
            arquivos_para_processar = []

            # Primeiro, verifica se há arquivos ZIP para descompactar
            for arquivo in sorted(novos_arquivos):
                if arquivo.endswith(".crdownload") or arquivo.endswith(".tmp"):
                    continue

                # Para evitar renomear arquivos que já foram renomeados em execuções anteriores
                if arquivo.startswith("LEXXY_SUPERSIM_") or arquivo.startswith(numero_limpo):
                    continue

                caminho_arquivo = os.path.join(downloads_dir, arquivo)

                # Se for ZIP, descompacta
                if arquivo.lower().endswith('.zip'):
                    try:
                        self.logger.info(f"Arquivo ZIP detectado: {arquivo}. Descompactando...")

                        # Cria pasta temporária para extração
                        extract_dir = os.path.join(downloads_dir, f"extract_{numero_limpo}")
                        os.makedirs(extract_dir, exist_ok=True)

                        # Descompacta o ZIP
                        with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                            self.logger.info(f"ZIP descompactado em: {extract_dir}")

                        # Lista arquivos extraídos
                        for root, dirs, files in os.walk(extract_dir):
                            for file in files:
                                # Ignora arquivos ocultos e de sistema
                                if not file.startswith('.') and not file.startswith('__MACOSX'):
                                    arquivo_extraido = os.path.join(root, file)
                                    arquivos_para_processar.append((file, arquivo_extraido))

                        self.logger.info(f"Total de arquivos extraídos: {len(arquivos_para_processar)}")

                        # Remove o ZIP após extração
                        os.remove(caminho_arquivo)
                        self.logger.info("Arquivo ZIP removido após extração")

                    except Exception as e:
                        self.logger.error(f"Erro ao descompactar ZIP: {e}")
                        # Se falhar, trata como arquivo normal
                        arquivos_para_processar.append((arquivo, caminho_arquivo))

                else:
                    # Arquivo não é ZIP, adiciona diretamente
                    arquivos_para_processar.append((arquivo, caminho_arquivo))

            # Renomeia e move todos os arquivos
            self.logger.info(f"Processando {len(arquivos_para_processar)} arquivo(s)...")

            for idx, (nome_original, caminho_original) in enumerate(arquivos_para_processar, start=1):
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

                try:
                    # Move o arquivo para temp_downloads com o novo nome
                    shutil.move(caminho_original, caminho_novo)
                    self.logger.info(f"[{idx}/{len(arquivos_para_processar)}] Arquivo processado: {novo_nome}")

                    # Adiciona metadados à lista
                    documentos_metadados.append({
                        "numero_linha": idx,
                        "nome_arquivo": nome_original,
                        "tipo_documento": nome_limpo,  # Usa o nome original limpo como tipo
                        "caminho_arquivo": caminho_novo,
                        "nome_arquivo_final": novo_nome
                    })

                except Exception as e:
                    self.logger.warning(f"Erro ao processar arquivo '{nome_original}': {e}")

            # Limpa pasta de extração se existir
            extract_dir = os.path.join(downloads_dir, f"extract_{numero_limpo}")
            if os.path.exists(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                    self.logger.info("Pasta de extração temporária removida")
                except Exception as e:
                    self.logger.warning(f"Erro ao remover pasta temporária: {e}")

            self.logger.info("=" * 80)
            self.logger.info(f"Download concluído! {len(documentos_metadados)} documento(s) processado(s)")
            self.logger.info("=" * 80)

            return documentos_metadados

        except Exception as e:
            self.logger.error(f"Erro fatal na função de baixar documentos: {e}")
            traceback.print_exc()
            return []

    def baixa_documento_anexo(self, numero_processo: str, pasta: str = None, codigo_pasta: str = None):
        """
        Executa o fluxo completo de baixa de documentos anexos:
        1. Acessa processos
        2. Busca o processo
        3. Acessa detalhes
        4. Acessa anexos
        5. Baixa e renomeia documentos

        Args:
            numero_processo (str): Número do processo (com ou sem pontuação)
            pasta (str, optional): Pasta/folder no ADVWin para armazenamento
            codigo_pasta (str, optional): Código da pasta no ADVWin (codigo_comp)

        Returns:
            list: Lista de dicionários com metadados dos documentos baixados, ou lista vazia em caso de erro
            Cada documento tem a estrutura:
            {
                "numero_linha": int,
                "nome_arquivo": str,
                "tipo_documento": str,
                "caminho_arquivo": str,
                "nome_arquivo_final": str,
                "pasta": str (opcional),
                "codigo_pasta": str (opcional)
            }
        """
        try:
            self.logger.info(f"Iniciando fluxo de baixa de documentos para o processo: {numero_processo}")

            # 1. Acessar lista de processos
            if not self.ACESSAR_PROCESSOS():
                self.logger.error(f"Erro ao acessar lista de processos!")
                return []
            self.logger.info("Lista de processos acessada")

            # 2. Buscar processo
            if not self.BUSCAR_PROCESSO(numero_processo):
                self.logger.error(f"Erro ao buscar o processo {numero_processo}")
                return []
            self.logger.info(f"Processo {numero_processo} encontrado")

            # 3. Ver detalhes do processo
            if not self.VER_DETALHES():
                self.logger.error(f"Erro ao acessar detalhes do processo {numero_processo}")
                return []
            self.logger.info(f"Detalhes do processo {numero_processo} acessados")

            # 4. Acessar aba de anexos
            if not self.ACESSAR_ANEXOS():
                self.logger.error(f"Erro ao acessar anexos do processo {numero_processo}")
                return []
            self.logger.info(f"Anexos do processo {numero_processo} acessados")

            # 5. Baixar e renomear documentos
            documentos = self.BAIXAR_DOCUMENTOS(numero_processo)

            if not documentos or len(documentos) == 0:
                self.logger.error(f"Nenhum documento foi baixado do processo {numero_processo}")
                return []

            # Adiciona pasta e codigo_pasta em cada documento (se fornecidos)
            if pasta or codigo_pasta:
                for doc in documentos:
                    if pasta:
                        doc["pasta"] = pasta
                    if codigo_pasta:
                        doc["codigo_pasta"] = codigo_pasta

            self.logger.info(f"Fluxo de baixa de documentos concluído com sucesso!")
            self.logger.info(f"Total de documentos baixados: {len(documentos)}")

            return documentos

        except Exception as e:
            self.logger.error(f"Erro geral no fluxo de baixa de documentos do processo {numero_processo}: {e}")
            traceback.print_exc()
            return []

    def LOGOUT(self):
        """Realiza logout e fecha o navegador"""
        try:
            if self.driver:
                self.logger.info("Fechando navegador...")
                self.driver.quit()
                self.logger.info("Navegador fechado")
        except Exception as e:
            self.logger.error(f"Erro ao fechar navegador: {e}")

    def __enter__(self):
        """Suporte para context manager (with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automatico ao sair do context manager"""
        self.LOGOUT()


# Exemplo de uso
if __name__ == "__main__":
    """
    Exemplo de uso da classe LexxySuperSim
    """
    try:
        NUMERO_PROCESSO_TESTE = "00016683620258173120"

        with LexxySuperSim() as lexxy:
            lexxy.ENTRAR_NO_SISTEMA(usar_selenoid=False)

            if lexxy.LOGIN():
                logger.info("Login realizado com sucesso!")

                if lexxy.ACESSAR_PROCESSOS():
                    logger.info("Pagina de processos acessada!")

                    if lexxy.BUSCAR_PROCESSO(NUMERO_PROCESSO_TESTE):
                        logger.info("Processo encontrado!")

                        if lexxy.VER_DETALHES():
                            logger.info("Detalhes acessados!")

                            if lexxy.ACESSAR_ANEXOS():
                                logger.info("Anexos acessados!")

                                if lexxy.BAIXAR_DOCUMENTOS(NUMERO_PROCESSO_TESTE):
                                    logger.info("Automacao concluida com sucesso!")
                                    time.sleep(5)
                                else:
                                    logger.error("Falha ao baixar documentos")
                            else:
                                logger.error("Falha ao acessar anexos")
                        else:
                            logger.error("Falha ao abrir detalhes")
                    else:
                        logger.error("Falha ao buscar processo")
                else:
                    logger.error("Falha ao acessar processos")
            else:
                logger.error("Falha no login")

    except Exception as e:
        logger.error(f"Erro na execucao: {e}")
        import traceback
        traceback.print_exc()
