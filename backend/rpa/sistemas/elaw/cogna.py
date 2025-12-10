import uuid
import sys
import traceback
import selenium
import pandas as pd
import time
import os
import glob
import shutil
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class ElawCOGNA:
    def __init__(self, driver=None, usuario=None, senha=None, download_path=None):
        """
        Inicializa a classe ElawCOGNA para automação do sistema eLaw

        Args:
            driver: Instância do WebDriver (Selenium)
            usuario: Usuário para login (opcional)
            senha: Senha para login (opcional)
            download_path: Pasta de downloads (padrão: ~/Downloads)
        """
        self.url_producao = "https://kroton.elaw.com.br/processoList.elaw"
        self.driver = driver
        self.user = usuario if usuario else "lima.feigelson06"
        self.password = senha if senha else "@Ingrid74"
        self.url_processo = "https://kroton.elaw.com.br/processoList.elaw"
        self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads")
        self._ultimo_arquivo_baixado = None  # Rastreia último arquivo baixado

    def _identificar_tipo_documento(self, nome_documento: str):
        """
        Identifica o tipo do documento baseado no nome.

        Args:
            nome_documento (str): Nome do documento a ser analisado

        Returns:
            str: Tipo do documento ('inicial', 'subsidio' ou 'documento')
        """
        nome_lower = nome_documento.lower()

        # Palavras-chave para identificar inicial
        palavras_inicial = ['inicial', 'petição inicial', 'peticao inicial', 'pi']

        # Palavras-chave para identificar subsídio
        palavras_subsidio = ['subsídio', 'subsidio', 'subsid', 'subsí']

        # Verifica se é inicial
        for palavra in palavras_inicial:
            if palavra in nome_lower:
                return 'inicial'

        # Verifica se é subsídio
        for palavra in palavras_subsidio:
            if palavra in nome_lower:
                return 'subsidio'

        # Se não identificar, retorna 'documento'
        return 'documento'

    def _aguardar_download_completo(self, timeout=60, arquivos_antes=None):
        """
        Aguarda o download ser concluído verificando se há arquivos temporários.

        Args:
            timeout (int): Tempo máximo de espera em segundos
            arquivos_antes (set): Lista de arquivos que já existiam antes do clique (opcional)

        Returns:
            str: Caminho do arquivo baixado ou None se não encontrado
        """
        try:
            print(f"⏳ Aguardando download completar no diretório: {self.download_path}")

            # Se não foi passado arquivos_antes, pega agora
            if arquivos_antes is None:
                arquivos_antes = set(os.listdir(self.download_path)) if os.path.exists(self.download_path) else set()

            print(f"📊 Arquivos antes do download: {len(arquivos_antes)}")

            # Pega timestamp
            tempo_inicial = time.time()

            # Aguarda pelo menos 2 segundos para o download iniciar
            time.sleep(2)

            while time.time() - tempo_inicial < timeout:
                try:
                    arquivos_atuais = set(os.listdir(self.download_path))

                    # Verifica se há arquivos temporários (download em andamento)
                    temp_files = [f for f in arquivos_atuais if f.endswith('.crdownload') or f.endswith('.tmp')]

                    if temp_files:
                        print(f"  ⏳ Download em andamento: {temp_files[0]}")
                        time.sleep(1)
                        continue

                    # Verifica se há novos arquivos
                    novos_arquivos = arquivos_atuais - arquivos_antes

                    if novos_arquivos:
                        # Filtra apenas arquivos válidos (não temporários)
                        arquivos_validos = [f for f in novos_arquivos
                                          if not f.endswith('.crdownload')
                                          and not f.endswith('.tmp')
                                          and not f.startswith('.')]

                        if arquivos_validos:
                            arquivo_baixado = sorted(arquivos_validos)[0]
                            caminho_completo = os.path.join(self.download_path, arquivo_baixado)
                            print(f"✅ Download concluído: {arquivo_baixado}")
                            return caminho_completo

                except Exception as e:
                    print(f"  ⚠️ Erro ao verificar downloads: {e}")

                time.sleep(1)

            print(f"⚠️ Timeout ao aguardar download ({timeout}s)")
            print(f"📊 Total de arquivos no diretório: {len(os.listdir(self.download_path)) if os.path.exists(self.download_path) else 0}")
            return None

        except Exception as e:
            print(f"❌ Erro ao aguardar download: {e}")
            return None

    def _renomear_documento_baixado(self, caminho_arquivo: str, numero_processo: str, tipo_documento: str, numero_linha: int = None):
        """
        Renomeia o documento baixado com o padrão: numerodoprocesso_tipodocumento_numerolinha.extensao

        Args:
            caminho_arquivo (str): Caminho completo do arquivo baixado
            numero_processo (str): Número do processo
            tipo_documento (str): Tipo do documento (inicial, subsidio, documento)
            numero_linha (int): Número da linha na tabela (opcional)

        Returns:
            str: Caminho do arquivo renomeado ou None em caso de erro
        """
        try:
            if not caminho_arquivo or not os.path.exists(caminho_arquivo):
                print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
                return None

            # Limpa o número do processo (remove pontos, traços e espaços)
            numero_limpo = numero_processo.replace(".", "").replace("-", "").replace(" ", "")

            # Pega a extensão do arquivo original
            _, extensao = os.path.splitext(caminho_arquivo)

            # Monta o novo nome com o padrão: numerodoprocesso_tipodocumento_numerolinha
            if numero_linha is not None:
                novo_nome = f"{numero_limpo}_{tipo_documento}_{numero_linha:02d}{extensao}"
            else:
                novo_nome = f"{numero_limpo}_{tipo_documento}{extensao}"

            # Monta o caminho completo do novo arquivo
            diretorio = os.path.dirname(caminho_arquivo)
            novo_caminho = os.path.join(diretorio, novo_nome)

            # Renomeia o arquivo
            if os.path.exists(novo_caminho):
                print(f"⚠️ Arquivo já existe: {novo_nome}")
                # Adiciona timestamp para evitar sobrescrever
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if numero_linha is not None:
                    novo_nome = f"{numero_limpo}_{tipo_documento}_{numero_linha:02d}_{timestamp}{extensao}"
                else:
                    novo_nome = f"{numero_limpo}_{tipo_documento}_{timestamp}{extensao}"
                novo_caminho = os.path.join(diretorio, novo_nome)

            os.rename(caminho_arquivo, novo_caminho)
            print(f"✅ Arquivo renomeado: {novo_nome}")
            return novo_caminho

        except Exception as e:
            print(f"❌ Erro ao renomear arquivo: {e}")
            traceback.print_exc()
            return None

    def _processar_renomeacao_documento(self, numero_processo: str, tipo_documento: str, numero_linha: int = None, arquivos_antes: set = None):
        """
        Processa a renomeação do documento baixado: aguarda download,
        renomeia e move para temp_downloads/.

        Args:
            numero_processo (str): Número do processo
            tipo_documento (str): Tipo do documento (extraído da coluna "Tipo de Documento" da tabela)
            numero_linha (int): Número da linha na tabela (opcional)
            arquivos_antes (set): Set de arquivos que existiam antes do clique (opcional)

        Returns:
            str: Caminho do arquivo em temp_downloads/ ou None em caso de erro
        """
        try:
            print("="*70)
            print("ETAPA 5: Processando renomeação e movendo documento...")
            print("="*70)

            # Tipo do documento já vem da coluna da tabela
            print(f"🏷️  Tipo do documento: {tipo_documento}")

            # Fecha novas abas/janelas que possam ter sido abertas (PDF viewer, etc)
            try:
                janela_principal = self.driver.current_window_handle
                todas_janelas = self.driver.window_handles

                if len(todas_janelas) > 1:
                    print(f"🔄 Detectadas {len(todas_janelas)} janelas/abas abertas, fechando extras...")
                    for janela in todas_janelas:
                        if janela != janela_principal:
                            self.driver.switch_to.window(janela)
                            self.driver.close()
                    self.driver.switch_to.window(janela_principal)
                    print("✅ Abas extras fechadas, voltando para janela principal")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Erro ao gerenciar janelas: {e}")

            # Aguarda o download completar, passando o snapshot dos arquivos antes
            arquivo_baixado = self._aguardar_download_completo(timeout=60, arquivos_antes=arquivos_antes)

            if arquivo_baixado:
                # Renomeia o arquivo
                arquivo_renomeado = self._renomear_documento_baixado(
                    arquivo_baixado,
                    numero_processo,
                    tipo_documento,
                    numero_linha
                )

                if arquivo_renomeado:
                    # Move para temp_downloads/
                    temp_dir = os.path.join(os.getcwd(), "temp_downloads")
                    os.makedirs(temp_dir, exist_ok=True)

                    nome_final = os.path.basename(arquivo_renomeado)
                    destino_final = os.path.join(temp_dir, nome_final)

                    # Move o arquivo
                    shutil.move(arquivo_renomeado, destino_final)

                    print(f"✅ Documento processado e movido com sucesso!")
                    print(f"   📁 Arquivo: {destino_final}")

                    # Salva o caminho para retornar depois
                    self._ultimo_arquivo_baixado = destino_final
                    return destino_final
                else:
                    print("⚠️ Arquivo baixado mas não renomeado")
                    self._ultimo_arquivo_baixado = arquivo_baixado
                    return arquivo_baixado
            else:
                print("⚠️ Não foi possível detectar o arquivo baixado")
                return None

        except Exception as e:
            print(f"❌ Erro ao processar renomeação: {e}")
            traceback.print_exc()
            return None

    def ENTRAR_NO_SISTEMA(self):
        try:
            chrome_options = Options()

            # 2. Apontar o Selenium para o navegador que está rodando na porta 9222
            # Esta é a linha mágica:
            chrome_options.debugger_address = "localhost:9222"

            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
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

            # Navega para a URL de login
            self.driver.get(self.url_producao)
            time.sleep(3)

        except Exception as e:
            print(f"❌ Erro ao inicializar o WebDriver: {e}")
            print("   Verifique se o Google Chrome está instalado.")
            print(
                "   O Selenium tentará baixar o driver correto, mas precisa do Chrome."
            )
            raise

    def LOGIN(self):
        """
        Realiza o login no sistema eLaw COGNA

        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário
        """
        try:
            print("Procurando tela de login...")
            print(f"URL atual antes do login: {self.driver.current_url}")

            # Aguarda a tela de login carregar
            login_screen = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "logo-container"))
            )
            print("✅ Tela de login encontrada")

            # Verifica se há campo de domínio/empresa
            try:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                print(f"Total de campos input encontrados: {len(all_inputs)}")
                for idx, inp in enumerate(all_inputs):
                    inp_id = inp.get_attribute("id")
                    inp_name = inp.get_attribute("name")
                    inp_type = inp.get_attribute("type")
                    inp_placeholder = inp.get_attribute("placeholder")
                    print(f"  Campo {idx}: id='{inp_id}', name='{inp_name}', type='{inp_type}', placeholder='{inp_placeholder}'")
            except Exception as e:
                print(f"Erro ao listar campos: {e}")

            # Localiza campos de login
            input_username = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            input_password = self.driver.find_element(By.ID, "password")

            print(f"Preenchendo usuário: {self.user}")
            input_username.clear()
            input_username.send_keys(self.user)
            time.sleep(2)

            print("Preenchendo senha...")
            input_password.clear()
            input_password.send_keys(self.password)
            time.sleep(2)

            # Clica no botão de login
            print("Clicando em entrar...")
            btn_entrar = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnAcessarRedirect"))
            )
            btn_entrar.click()
            
            # self.driver.get(self.url_processo)

            print("Aguardando sistema carregar...")
            # time.sleep(10)

            # Verifica URL após login
            print(f"URL atual após clicar em entrar: {self.driver.current_url}")
            print(f"Título da página: {self.driver.title}")

            # Verifica se há mensagem de erro
            try:
                page_source = self.driver.page_source
                if "ERRO" in self.driver.title.upper() or "ERRO" in page_source.upper():
                    print("❌ DETECTADO: Página de erro após login!")
                    print(f"Título completo: {self.driver.title}")

                    # Tenta capturar mensagem de erro
                    try:
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        print(f"Conteúdo da página de erro:")
                        print("=" * 70)
                        print(body_text)
                        print("=" * 70)
                    except:
                        pass

                    # Verifica se há mensagem de erro específica
                    try:
                        error_messages = self.driver.find_elements(By.CLASS_NAME, "ui-messages-error")
                        if error_messages:
                            print("Mensagens de erro encontradas:")
                            for msg in error_messages:
                                print(f"  - {msg.text}")
                    except:
                        pass

                    # Tenta fazer screenshot
                    try:
                        screenshot_path = f"erro_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Screenshot salvo em: {screenshot_path}")
                    except:
                        pass

                    return False
            except:
                pass

            # time.sleep(10)

            return self.CONFIRM_LOGIN()

        except Exception as e:
            print(f"❌ Erro ao realizar login: {e}")
            print(f"URL atual no erro: {self.driver.current_url}")
            traceback.print_exc()
            return False

    def CONFIRM_LOGIN(self):
        """
        Confirma se o login foi realizado com sucesso

        Returns:
            bool: True se está logado, False caso contrário
        """
        try:
            print("Verificando se o login foi bem-sucedido...")

            # Tenta encontrar o logo da empresa (indica que está logado)
            imgTopoLogoEmpresa = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "imgTopoLogoEmpresa"))
            )

            if imgTopoLogoEmpresa:
                print("✅ Login confirmado! Usuário está logado no sistema.")
                return True
            else:
                print("❌ Elemento de confirmação não encontrado!")
                return False

        except Exception as e:
            print(f"❌ Não foi possível confirmar o login: {e}")
            print(f"URL atual: {self.driver.current_url}")
            return False

    def ACESSO_LISTA_PROCESSOS(self):
        try:
            contencioso = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/ul/li[3]/a/i")
            contencioso.click()
            time.sleep(2)
            contencioso = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/div[2]/div/div[1]/form/ul/li[1]")
            contencioso.click()
            time.sleep(3)
            # self.driver.get(self.url_processo)
            return True
        except Exception as e:
            print(f"❌ Erro ao acessar lista de processos: {e}")
            traceback.print_exc()
            return False

    def PESQUISA_PROCESSO(self, numero_processo: str):
        try:
            print(f"🔍 Pesquisando processo: {str(numero_processo)}")
            print(f"  URL atual: {self.driver.current_url}")

            # Aguarda e clica no dropdown de tipo de pesquisa com XPath mais robusto
            try:
                select_tipo_pesquisa = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//span[contains(@class, 'k-dropdown-wrap')]//span[@class='k-icon k-i-arrow-60-down']"
                    ))
                )
                print("  Abrindo dropdown de tipo de pesquisa...")
                select_tipo_pesquisa.click()
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Tentando XPath alternativo para dropdown: {e}")
                select_tipo_pesquisa = self.driver.find_element(
                    By.XPATH,
                    "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[1]/table/tbody/tr/td[1]/div/div/div[1]/table/tbody/tr/td[1]/span/table[1]/tbody/tr/td[1]/div/div[3]/span"
                )
                select_tipo_pesquisa.click()
                time.sleep(2)

            # Seleciona "Processo" no dropdown com wait
            try:
                li_processo = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//li[text()='Processo']"))
                )
                print("  Selecionando 'Processo' no dropdown...")
                li_processo.click()
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Tentando XPath alternativo para opção Processo: {e}")
                li_processo = self.driver.find_element(By.XPATH, "/html/body/div[8]/div/ul/li[3]")
                li_processo.click()
                time.sleep(2)

            # Preenche campo de busca com limpeza robusta
            input_processo = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "tabSearchTab:txtSearch"))
            )
            print(f"  Preenchendo campo de busca com: {str(numero_processo)}")

            # Limpeza robusta do campo
            input_processo.click()
            input_processo.clear()

            # Usa Ctrl+A e Delete para garantir limpeza completa
            input_processo.send_keys(Keys.CONTROL + "a")
            input_processo.send_keys(Keys.DELETE)

            # Preenche o número do processo
            input_processo.send_keys(str(numero_processo))

            # DEBUG: Verifica valor no campo antes de pesquisar
            valor_campo = input_processo.get_attribute("value")
            print(f"  📝 Valor no campo: '{valor_campo}'")

            # CORREÇÃO CRÍTICA: Clicar no botão Pesquisar ao invés de pressionar ENTER
            # O sistema não processa a busca com ENTER, precisa clicar no botão
            print("  Clicando no botão 'Pesquisar'...")
            try:
                # Tenta encontrar botão por texto "Pesquisar"
                btn_pesquisar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Pesquisar')]"))
                )
                print(f"  🎯 Botão encontrado: {btn_pesquisar.text}")
                btn_pesquisar.click()
                print("  ✓ Botão 'Pesquisar' clicado")
            except Exception as e:
                print(f"  ⚠️ Tentando localizar botão por ícone: {e}")
                # Fallback: tenta encontrar por ícone de lupa
                btn_pesquisar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'k-button')]//span[contains(@class, 'k-icon')]"))
                )
                btn_pesquisar.click()
                print("  ✓ Botão 'Pesquisar' clicado (via ícone)")

            print("  ⏳ Aguardando resultados carregarem (4 segundos)...")
            time.sleep(4)  # Aguarda resultados carregarem


            # DEBUG: Verifica estado da tabela de resultados
            try:
                tbody = self.driver.find_element(By.ID, "dtProcessoResults_data")
                print(f"  📊 Tabela de resultados encontrada")
                print(f"  📊 HTML da tabela (primeiras 500 chars): {tbody.get_attribute('innerHTML')[:500]}")
            except Exception as e:
                print(f"  ⚠️ Não foi possível acessar tabela de resultados: {e}")

            print("✅ Pesquisa executada com sucesso")
            return True
        except Exception as e:
            print(f"❌ Erro ao pesquisar processo: {e}")
            traceback.print_exc()
            return False

    def CONFERE_PROCESSO_ENCONTRADO(self):
        try:
            print("🔎 Verificando se processo foi encontrado...")

            # Aguarda tabela de resultados carregar
            tbody_processo = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "dtProcessoResults_data"))
            )

            # Verifica se há linhas na tabela (resultados)
            try:
                # Busca primeira linha de resultado dentro do tbody
                tr_processo = tbody_processo.find_element(By.XPATH, ".//tr[@data-ri='0']")

                if tr_processo and tr_processo.is_displayed():
                    print("✅ Processo encontrado!")
                    return True
                else:
                    print("❌ Processo não encontrado (sem resultados)!")
                    return False
            except Exception as e:
                # Se não encontrar tr com data-ri, tenta buscar qualquer tr
                try:
                    tr_processo = tbody_processo.find_element(By.TAG_NAME, "tr")
                    texto_tr = tr_processo.text.strip()

                    # Verifica se é uma mensagem de "nenhum resultado"
                    if "nenhum" in texto_tr.lower() or "não encontrado" in texto_tr.lower():
                        print(f"❌ Processo não encontrado: {texto_tr}")
                        return False

                    if tr_processo and tr_processo.is_displayed():
                        print("✅ Processo encontrado!")
                        return True
                    else:
                        print("❌ Processo não encontrado!")
                        return False
                except:
                    print(f"❌ Nenhum resultado encontrado na busca")
                    return False

        except Exception as e:
            print(f"❌ Erro ao conferir processo encontrado: {e}")
            traceback.print_exc()
            return False

    def ACESSO_PROCESSO(self):
        try:
            btn_acesso_processo = self.driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[2]/span/div/div[3]/table/tbody/tr/td[1]/button[1]/span[1]",
            )
            if btn_acesso_processo:
                btn_acesso_processo.click()
                return True
            else:
                print("Botão de acesso ao processo não encontrado!")
                return False
        except:
            print("Erro ao acessar processo!")
            return False

    def VERIFICA_SE_ENTROU_PAGINA_PROCESSO(self, numero_processo: str):
        try:
            check_url = self.driver.current_url
            if check_url == "https://kroton.elaw.com.br/processoView.elaw":
                print("Acesso ao processo realizado com sucesso!")
            else:
                print("Acesso ao processo não realizado!")

            # Remove pontos e traços do número de referência
            numero_limpo = numero_processo.replace(".", "").replace("-", "")

            # Aguarda a página carregar
            time.sleep(2)

            # Estratégia 1: Procura no HTML da página (mais rápido)
            try:
                page_source = self.driver.page_source

                if numero_processo in page_source or numero_limpo in page_source:
                    print(f"✅ Processo {numero_processo} confirmado na página!")
                    return True
            except Exception as e1:
                print(f"Estratégia 1 falhou: {e1}")

            # Estratégia 2: Procura por elementos contendo o número
            try:
                elementos = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{numero_processo}')]")
                if len(elementos) > 0:
                    print(f"✅ Processo {numero_processo} encontrado em {len(elementos)} elementos!")
                    return True
            except Exception as e2:
                print(f"Estratégia 2 falhou: {e2}")

            # Estratégia 3: XPath específico (original - fallback)
            try:
                td_processo = self.driver.find_element(
                    By.XPATH,
                    "/html/body/div[1]/div[3]/div[1]/div[4]/div[2]/form[2]/table/tbody/tr[2]/td[4]",
                )
                processo_numero = td_processo.text.replace(".", "").replace("-", "")

                if processo_numero == numero_limpo:
                    print("✅ Processo encontrado via XPath específico!")
                    return True
            except Exception as e3:
                print(f"Estratégia 3 (XPath) falhou: {e3}")

            print(f"❌ Processo {numero_processo} não encontrado na página!")
            return False
        except Exception as e:
            print(f"Erro ao verificar se entrou na página de processo: {e}")
            traceback.print_exc()
            return False

    def ACESSO_INCLUSAO_ANDAMENTOS(self):
        try:
            btn_acesso_inclusao_andamentos = self.driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div[3]/div[1]/div[5]/div/div/div/div[2]/span/span/form/div/div[2]/table/tbody/tr/td/button/span[2]",
            )
            if btn_acesso_inclusao_andamentos:
                btn_acesso_inclusao_andamentos.click()
                time.sleep(3)
                return True
            else:
                print("Botão de acesso ao inclusão de andamentos não encontrado!")
                return False
        except:
            print("Erro ao acessar inclusão de andamentos!")
            return False

    def VERIFICA_SE_ENTROU_PAGINA_ANDAMENTOS(self):
        try:
            check_url_andamentos = self.driver.current_url
            if check_url_andamentos == "https://kroton.elaw.com.br/andamentoEdit.elaw":
                print("Acesso ao inclusão de andamentos realizado com sucesso!")
                check_elemento_andamentos = self.driver.find_element(
                    By.XPATH,
                    "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[2]/table/tbody/tr[1]/td/div/div/div/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/div/label",
                )
                if check_elemento_andamentos:
                    print("Elemento de andamentos encontrado!")
                    return True
                else:
                    print("Elemento de andamentos não encontrado!")
            else:
                print("Acesso ao inclusão de andamentos não realizado!")
                return False
        except:
            print("Erro ao verificar se entrou na página de inclusão de andamentos!")
            return False

    def buscarSelecionarXPATH(self, XPATH_PAI, XPATH, termo, wait1, wait2, name):
        try:
            time.sleep(3)

            # Aguarda o elemento pai estar clicável
            pai = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, str(XPATH_PAI)))
            )
            print("pai", pai)

            if pai:
                pai.click()

                # Aguarda o elemento filho aparecer e estar clicável
                pai_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, str(XPATH)))
                )
                print("pai_input", pai_input)

                if pai_input:
                    # Limpa qualquer texto existente
                    pai_input.clear()
                    time.sleep(0.5)
                    pai_input.send_keys(str(termo))
                    time.sleep(wait1)
                    pai_input.send_keys(Keys.ENTER)
                    time.sleep(wait2)
                    return True
        except Exception as e:
            print(f"Erro detalhado em buscarSelecionarXPATH: {e}")
            print("Erro ao acessar campo :", name)
            # Tentar alternativa: usar JavaScript para clicar
            try:
                print("Tentando alternativa com JavaScript...")
                pai = self.driver.find_element(By.XPATH, str(XPATH_PAI))
                self.driver.execute_script("arguments[0].click();", pai)
                time.sleep(2)

                pai_input = self.driver.find_element(By.XPATH, str(XPATH))
                pai_input.clear()
                pai_input.send_keys(str(termo))
                time.sleep(wait1)
                pai_input.send_keys(Keys.ENTER)
                time.sleep(wait2)
                return True
            except Exception as e2:
                print(f"Erro na alternativa JavaScript: {e2}")
                return False

    def PREENCHE_TIPO_ANDAMENTO(self):
        try:
            self.buscarSelecionarXPATH(
                "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[2]/table/tbody/tr[1]/td/div/div/div/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/div/label",
                "/html/body/div[9]/div[1]/input",
                "Acompanhamento",
                5,
                5,
                "Andamento",
            )
            return True
        except Exception as e:
            print(e)
            print("Erro ao preencher tipo de andamento!")
            return False

    def PREECHE_DATA_ANDAMENTO(self, data_andamento: str):
        """Formato: dd/mm/yyyy"""
        try:
            input_data_andamento = self.driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[2]/table/tbody/tr[1]/td/div/div/div/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[2]/td[2]/span/input",
            )
            # apagar o texto
            if input_data_andamento:
                input_data_andamento.click()
                input_data_andamento.clear()
                time.sleep(1)
                input_data_andamento.send_keys(data_andamento)
                time.sleep(1)
                input_data_andamento.send_keys(Keys.ESCAPE)
                input_data_andamento.send_keys(Keys.TAB)
                return True
            else:
                print("Elemento de data de andamento não encontrado!")
                return False
        except:
            print("Erro ao preencher data de andamento!")
            return False

    def PREENCHE_ANDAMENTO(self, texto_andamento: str):
        text_area_andamento = self.driver.find_element(
            By.XPATH,
            "/html/body/div[1]/div[3]/div[1]/div/div[2]/form[2]/table/tbody/tr[1]/td/div/div/div/table/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/span/table[2]/tbody/tr[2]/td/textarea",
        )
        if text_area_andamento:
            text_area_andamento.send_keys(texto_andamento)
            return True
        else:
            print("Elemento de andamento não encontrado!")
            return False

    def SALVAR_ANDAMENTO(self):
        try:
            btn_salvar_andamento = self.driver.find_element(
                By.ID, "btnSalvarAndamentoProcesso"
            )
            if btn_salvar_andamento:
                btn_salvar_andamento.click()
                # time.sleep(3)
                return True
        except:
            print("Erro ao salvar andamento!")
            return False

    def VOLTAR_AO_INICIO(self):
        try:
            self.driver.get(self.url_processo)
            return True
        except:
            print("Erro ao voltar ao início!")
            return False

    def ACESSO_ABA_ANEXOS(self, numero_processo: str = None):
        """
        Acessa a aba de anexos, faz scroll até a tabela "Anexos do Processo",
        busca pelo documento "Documentos", seleciona e faz o download.
        Se estiver em modo local, renomeia o arquivo com tipo e número do processo.

        Args:
            numero_processo (str): Número do processo para renomeação do arquivo

        Returns:
            bool: True se conseguiu baixar o documento, False caso contrário
        """
        try:
            print("="*70)
            print("ETAPA 1: Acessando aba de anexos...")
            print("="*70)

            # Aguarda a página do processo estar carregada
            time.sleep(2)

            # Procura pelo link da aba de anexos usando JavaScript
            script = """
                var links = document.querySelectorAll('a[href*="tabViewProcesso:files"]');
                if (links.length > 0) {
                    links[0].click();
                    return true;
                }
                return false;
            """

            result = self.driver.execute_script(script)

            if result:
                print("✅ Aba de anexos acessada via JavaScript!")
                time.sleep(3)
            else:
                print("Tentando acessar aba de anexos via XPath...")

                # Tenta encontrar usando XPath como alternativa
                try:
                    aba_anexos = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'tabViewProcesso:files')]"))
                    )
                    aba_anexos.click()
                    print("✅ Aba de anexos acessada via XPath!")
                    time.sleep(3)
                except Exception as e:
                    print(f"❌ Erro ao acessar aba de anexos via XPath: {e}")
                    return False

            print("="*70)
            print("ETAPA 2: Procurando tabela 'Anexos do Processo' e fazendo scroll...")
            print("="*70)

            # Scroll até a tabela de anexos
            scroll_realizado = False
            try:
                # Estratégia 1: Procura pela tabela com ID específico
                try:
                    tabela_anexos = self.driver.find_element(By.ID, "tabViewProcesso:gedEFileDataTable:GedEFileViewDt")
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});", tabela_anexos)
                    print(f"✅ Scroll realizado até a tabela de anexos (via ID da tabela)")
                    scroll_realizado = True
                    
                except:
                    print("⚠️ Tabela não encontrada via ID, tentando por texto...")

                # Estratégia 2: Procura por título "Anexos do Processo"
                if not scroll_realizado:
                    elementos_anexos = self.driver.find_elements(
                        By.XPATH,
                        "//*[contains(text(), 'Anexos do Processo')]"
                    )

                    if len(elementos_anexos) > 0:
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});", elementos_anexos[0])
                        print(f"✅ Scroll realizado até 'Anexos do Processo' (via texto)")
                        scroll_realizado = True

                # Estratégia 3: Scroll gradual pela página
                if not scroll_realizado:
                    print("⚠️ Fazendo scroll gradual pela página...")
                    for _ in range(3):
                        self.driver.execute_script("window.scrollBy(0, 400);")
                        time.sleep(0.5)
                    print("✅ Scroll gradual concluído")

            except Exception as e:
                print(f"⚠️ Erro ao fazer scroll: {e}")
                # Continua mesmo assim

            print("="*70)
            print("ETAPA 3: Buscando tabela de documentos...")
            print("="*70)

            # Procura por todos os documentos da tabela e baixa cada um
            try:
                # Aguarda a tabela aparecer
                tabela_anexos = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "/html/body/div[1]/div[3]/div[1]/div[5]/div/div/div/div[6]/form[4]/div[3]/div[2]/div[1]/div/div/table[1]/tbody/tr[2]/td/div/div[2]/table"))
                )
                print(f"✅ Tabela de anexos encontrada!")

                # Busca o tbody dentro da tabela
                tbody = tabela_anexos.find_element(By.TAG_NAME, "tbody")
                print(f"✅ Tbody encontrado")

                # Busca todas as linhas (tr) dentro do tbody
                trs_tabela_anexos = tbody.find_elements(By.TAG_NAME, "tr")
                total_linhas = len(trs_tabela_anexos)
                print(f"📊 Total de linhas encontradas: {total_linhas}")

                if total_linhas == 0:
                    print("⚠️ Nenhuma linha encontrada na tabela!")
                    return False

                # Lista para armazenar os arquivos baixados
                arquivos_baixados = []

                # Percorre cada linha da tabela
                for idx, tr in enumerate(trs_tabela_anexos, start=1):
                    print("\n" + "="*70)
                    print(f"PROCESSANDO LINHA {idx}/{total_linhas}")
                    print("="*70)

                    try:
                        # Mostra o texto da linha
                        texto_linha = tr.text.strip()
                        print(f"📄 Texto da linha: {texto_linha[:100]}...")

                        # Pula linhas vazias ou cabeçalhos
                        if not texto_linha or "Tipo de Documento" in texto_linha:
                            print("⏭️  Pulando linha (vazia ou cabeçalho)")
                            continue

                        # Busca as células da linha para extrair informações
                        celulas = tr.find_elements(By.TAG_NAME, "td")
                        nome_arquivo = "arquivo"
                        tipo_documento = "documento"

                        if len(celulas) >= 5:
                            # Coluna 3: Nome do Arquivo (para referência/log)
                            nome_arquivo_raw = celulas[3].text.strip() if len(celulas) > 3 else f"arquivo_{idx}"
                            nome_arquivo = nome_arquivo_raw[:50] if nome_arquivo_raw else f"arquivo_{idx}"

                            # Coluna 4: Tipo de Documento (o que vamos usar na renomeação)
                            tipo_documento_raw = celulas[4].text.strip() if len(celulas) > 4 else "documento"
                            # Limpa o tipo de documento (remove caracteres especiais, espaços, etc)
                            tipo_documento = tipo_documento_raw.replace("/", "_").replace(" ", "_").replace("-", "_").lower()

                            print(f"📝 Nome do arquivo: {nome_arquivo}")
                            print(f"🏷️  Tipo de documento: {tipo_documento_raw}")
                        else:
                            print(f"⚠️ Linha com {len(celulas)} colunas, esperado >= 5")
                            nome_arquivo = f"arquivo_{idx}"
                            tipo_documento = "documento"

                        # Scroll até a linha
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tr)
                        time.sleep(0.5)

                        # IMPORTANTE: Captura snapshot dos arquivos ANTES do clique
                        arquivos_antes_clique = set(os.listdir(self.download_path)) if os.path.exists(self.download_path) else set()

                        # Procura por elemento clicável na linha (link, botão, ícone)
                        elementos_clicaveis = tr.find_elements(By.XPATH, ".//a | .//button | .//span[@onclick] | .//i[@onclick]")

                        print(f"🔍 Encontrados {len(elementos_clicaveis)} elementos clicáveis na linha")

                        download_realizado = False

                        # Tenta clicar em cada elemento clicável
                        for elem_idx, elemento in enumerate(elementos_clicaveis):
                            try:
                                # Verifica atributos do elemento
                                title = elemento.get_attribute("title") or ""
                                onclick = elemento.get_attribute("onclick") or ""
                                class_attr = elemento.get_attribute("class") or ""
                                tag_name = elemento.tag_name

                                print(f"  [{elem_idx}] Tag: {tag_name}, title='{title}', class='{class_attr[:30]}'")

                                # Se tem indícios de ser download/visualização, clica
                                if any(palavra in title.lower() for palavra in ["download", "baixar", "visualizar", "abrir"]) or \
                                   any(palavra in onclick.lower() for palavra in ["download", "file", "abrir", "visualizar"]) or \
                                   any(palavra in class_attr.lower() for palavra in ["download", "file", "document"]) or \
                                   tag_name.lower() == 'a':

                                    print(f"✅ Clicando no elemento [{elem_idx}]...")

                                    try:
                                        # Tenta clicar normalmente
                                        elemento.click()
                                    except:
                                        # Se falhar, tenta via JavaScript
                                        print("⚠️ Clique normal falhou, tentando via JavaScript...")
                                        self.driver.execute_script("arguments[0].click();", elemento)

                                    time.sleep(3)
                                    print("✅ Clique realizado com sucesso!")

                                    # Se tiver número do processo, renomeia e move para temp_downloads
                                    # Passa o snapshot dos arquivos antes do clique
                                    if numero_processo:
                                        arquivo = self._processar_renomeacao_documento(numero_processo, tipo_documento, idx, arquivos_antes_clique)
                                        if arquivo:
                                            # Armazena metadados do documento
                                            documento_info = {
                                                "numero_linha": idx,
                                                "nome_arquivo": nome_arquivo,
                                                "tipo_documento": tipo_documento,
                                                "caminho_arquivo": arquivo,
                                                "nome_arquivo_final": os.path.basename(arquivo)
                                            }
                                            arquivos_baixados.append(documento_info)
                                            print(f"✅ Arquivo {idx}/{total_linhas} processado com sucesso!")

                                    download_realizado = True
                                    break

                            except Exception as e:
                                print(f"  ⚠️ Erro ao processar elemento [{elem_idx}]: {e}")
                                continue

                        # Se não conseguiu baixar por nenhum elemento específico, tenta clicar na linha inteira
                        if not download_realizado:
                            print("⚠️ Tentando clicar na linha inteira...")
                            try:
                                tr.click()
                                time.sleep(3)

                                if numero_processo:
                                    arquivo = self._processar_renomeacao_documento(numero_processo, tipo_documento, idx, arquivos_antes_clique)
                                    if arquivo:
                                        # Armazena metadados do documento
                                        documento_info = {
                                            "numero_linha": idx,
                                            "nome_arquivo": nome_arquivo,
                                            "tipo_documento": tipo_documento,
                                            "caminho_arquivo": arquivo,
                                            "nome_arquivo_final": os.path.basename(arquivo)
                                        }
                                        arquivos_baixados.append(documento_info)
                                        print(f"✅ Arquivo {idx}/{total_linhas} processado com sucesso!")
                                        download_realizado = True
                            except Exception as e:
                                print(f"⚠️ Não foi possível clicar na linha: {e}")

                        if not download_realizado:
                            print(f"⚠️ Linha {idx} não gerou download")

                    except Exception as e:
                        print(f"❌ Erro ao processar linha {idx}: {e}")
                        traceback.print_exc()
                        continue

                # Resumo final
                print("\n" + "="*70)
                print("RESUMO DO PROCESSAMENTO")
                print("="*70)
                print(f"📊 Total de linhas processadas: {total_linhas}")
                print(f"✅ Arquivos baixados com sucesso: {len(arquivos_baixados)}")

                if len(arquivos_baixados) > 0:
                    print("\n📁 Arquivos baixados:")
                    for doc_info in arquivos_baixados:
                        print(f"   - Linha {doc_info['numero_linha']}: {doc_info['tipo_documento']} -> {doc_info['nome_arquivo_final']}")

                    # Salva a lista de documentos para ser acessada depois
                    self._documentos_baixados = arquivos_baixados
                    return arquivos_baixados
                else:
                    print("⚠️ Nenhum arquivo foi baixado")
                    return []

            except Exception as e:
                print(f"❌ Erro ao buscar tabela de documentos: {e}")
                traceback.print_exc()
                return []

        except Exception as e:
            print(f"❌ Erro geral em ACESSO_ABA_ANEXOS: {e}")
            traceback.print_exc()
            return []

    def baixa_documento_anexo(self, numero_processo: str, pasta: str = None, codigo_pasta: str = None):
        """
        Executa o fluxo completo de baixa de documentos anexos:
        1. Acessa lista de processos
        2. Pesquisa o processo
        3. Confere se foi encontrado
        4. Acessa o processo
        5. Verifica se entrou na página
        6. Acessa a aba de anexos
        7. Lista e baixa documentos

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
            print(f"Iniciando fluxo de baixa de documentos para o processo: {numero_processo}")

            # 1. Acessar lista de processos
            if not self.ACESSO_LISTA_PROCESSOS():
                print(f"❌ Erro ao acessar lista de processos!")
                return []
            print("✅ Lista de processos acessada")

            # 2. Pesquisar processo
            if not self.PESQUISA_PROCESSO(numero_processo):
                print(f"❌ Erro ao pesquisar o processo {numero_processo}")
                return []
            print(f"✅ Processo {numero_processo} pesquisado")

            # 3. Conferir se processo foi encontrado
            if not self.CONFERE_PROCESSO_ENCONTRADO():
                print(f"❌ Processo {numero_processo} não foi encontrado")
                return []
            print(f"✅ Processo {numero_processo} encontrado")

            # 4. Acessar processo
            if not self.ACESSO_PROCESSO():
                print(f"❌ Erro ao acessar o processo {numero_processo}")
                return []
            print(f"✅ Processo {numero_processo} acessado")

            # 5. Verificar se entrou na página do processo
            if not self.VERIFICA_SE_ENTROU_PAGINA_PROCESSO(numero_processo):
                print(f"❌ Erro ao verificar acesso à página do processo {numero_processo}")
                return []
            print(f"✅ Página do processo {numero_processo} verificada")

            # 6. Acessar aba de anexos e baixar documentos
            # Agora retorna a lista de documentos baixados com seus metadados
            documentos = self.ACESSO_ABA_ANEXOS(numero_processo=numero_processo)

            if not documentos or len(documentos) == 0:
                print(f"❌ Nenhum documento foi baixado do processo {numero_processo}")
                return []

            # Adiciona pasta e codigo_pasta em cada documento (se fornecidos)
            if pasta or codigo_pasta:
                for doc in documentos:
                    if pasta:
                        doc["pasta"] = pasta
                    if codigo_pasta:
                        doc["codigo_pasta"] = codigo_pasta

            print(f"✅ Aba de anexos acessada com sucesso!")
            print(f"✅ Fluxo de baixa de documentos concluído com sucesso para o processo: {numero_processo}")
            print(f"✅ Total de documentos baixados: {len(documentos)}")

            return documentos

        except Exception as e:
            print(f"❌ Erro geral no fluxo de baixa de documentos do processo {numero_processo}: {e}")
            traceback.print_exc()
            return []

    def INSERIR_ANDAMENTO_UNITARIO(
        self, numero_processo: str, data_andamento: str, texto_andamento: str
    ):
        """
        Executa o fluxo completo de inserção de andamento unitário:
        1. Pesquisa o processo
        2. Acessa o processo
        3. Entra na aba de andamentos
        4. Preenche os dados do andamento
        5. Salva o andamento
        6. Volta ao início

        Args:
            numero_processo (str): Número do processo a ser pesquisado
            texto_andamento (str): Texto do andamento (padrão: "Acompanhamento")
            tipo_andamento (str): Tipo do andamento (padrão: "Acompanhamento")

        Returns:
            bool: True se o andamento foi inserido com sucesso, False caso contrário
        """
        try:
            print(f"Iniciando inserção de andamento para o processo: {numero_processo}")

            if not self.ACESSO_LISTA_PROCESSOS():
                print(f"Erro ao acessar lista de processos!")
                return False

            # 1. Pesquisar o processo
            if not self.PESQUISA_PROCESSO(numero_processo):
                print(f"Erro ao pesquisar o processo {numero_processo}")
                return False

            # 2. Conferir se o processo foi encontrado
            if not self.CONFERE_PROCESSO_ENCONTRADO():
                print(f"Processo {numero_processo} não foi encontrado")
                return False

            # 3. Acessar o processo
            if not self.ACESSO_PROCESSO():
                print(f"Erro ao acessar o processo {numero_processo}")
                return False

            # 4. Verificar se entrou na página do processo
            if not self.VERIFICA_SE_ENTROU_PAGINA_PROCESSO(str(numero_processo)):
                print(
                    f"Erro ao verificar acesso à página do processo {str(numero_processo)}"
                )
                return False

            # 5. Acessar inclusão de andamentos
            if not self.ACESSO_INCLUSAO_ANDAMENTOS():
                print(
                    f"Erro ao acessar inclusão de andamentos do processo {str(numero_processo)}"
                )
                return False

            # 6. Verificar se entrou na página de andamentos
            if not self.VERIFICA_SE_ENTROU_PAGINA_ANDAMENTOS():
                print(
                    f"Erro ao verificar acesso à página de andamentos do processo {str(numero_processo)}"
                )
                return False

            # 9. Preencher texto do andamento (modificado para aceitar texto customizado)

            if not self.PREENCHE_ANDAMENTO(texto_andamento=texto_andamento):
                print(
                    f"Erro ao preencher texto do andamento do processo {str(numero_processo)}"
                )
                return False

                # 7. Preencher tipo de andamento
            if not self.PREENCHE_TIPO_ANDAMENTO():
                print(
                    f"Erro ao preencher tipo de andamento do processo {str(numero_processo)}"
                )
                return False

            # 8. Preencher data do andamento
            if not self.PREECHE_DATA_ANDAMENTO(data_andamento=data_andamento):
                print(
                    f"Erro ao preencher data do andamento do processo {str(numero_processo)}"
                )
                return False

            # 10. Salvar o andamento
            if not self.SALVAR_ANDAMENTO():
                print(f"Erro ao salvar andamento do processo {str(numero_processo)}")
                return False

            # 11. Voltar ao início
            if not self.VOLTAR_AO_INICIO():
                print(
                    f"Erro ao voltar ao início após inserir andamento do processo {str(numero_processo)}"
                )
                return False

            print(f"Andamento inserido com sucesso no processo: {str(numero_processo)}")
            return True

        except Exception as e:
            print(f"Erro geral ao inserir andamento no processo {str(numero_processo)}: {e}")
            # Tentar voltar ao início mesmo em caso de erro
            try:
                self.VOLTAR_AO_INICIO()
            except:
                pass
            return False

    def get_ultimo_arquivo_baixado(self):
        """
        Retorna o caminho do último arquivo baixado e processado

        Returns:
            str: Caminho completo do arquivo ou None
        """
        return self._ultimo_arquivo_baixado
