# Plano de Integração do RPA eLaw COGNA

## Análise do RPA Existente

### **Estrutura Atual do RPA**

**Sistema eLaw COGNA ([sistemas/elaw/cogna.py](sistemas/elaw/cogna.py)):**
- Classe `ElawCOGNA` com métodos completos
- Login, pesquisa de processos, acesso a anexos
- **JÁ IMPLEMENTADO**: Sistema de detecção de modo local vs Selenoid
- **JÁ IMPLEMENTADO**: Renomeação automática de arquivos baixados
- **JÁ IMPLEMENTADO**: Aguarda download completo e identifica tipo de documento

**Script de Teste ([robos/elaw/baixa_documentos_cogna.py](robos/elaw/baixa_documentos_cogna.py)):**
- Funções para criar driver local e Selenoid
- Testes completos do fluxo

---

## **PLANO DE INTEGRAÇÃO - Etapas Detalhadas**

### **ETAPA 1: Adaptar a Classe ElawCOGNA**

**Mudanças necessárias em `cogna.py`:**

1. **Remover lógica de Selenoid** (linhas 29-69, 117-154)
   - Remover `_detect_local_mode()`
   - Remover verificações de Selenoid
   - Sempre usar modo local

2. **Atualizar `__init__` para usar pasta local do projeto:**
   ```python
   def __init__(self, driver=None, usuario=None, senha=None, download_path=None):
       self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads")
       # Não precisa mais de is_local_mode
   ```

3. **Atualizar método de renomeação para mover arquivo:**
   - Ao invés de renomear no `Downloads` do usuário
   - Deve **mover** o arquivo renomeado para `temp_downloads/` do projeto

4. **Criar método que retorna o caminho final do arquivo:**
   ```python
   def get_arquivo_baixado_path(self) -> str:
       # Retorna o caminho do último arquivo baixado e renomeado
   ```

---

### **ETAPA 2: Criar Adaptador no `rpa_logic.py`**

**Substituir o placeholder por:**

```python
from sistemas.elaw.cogna import ElawCOGNA
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import shutil
import time

def download_document(process_number: str, client_name: str) -> Optional[str]:
    """
    Baixa documento usando o RPA eLaw COGNA

    Fluxo:
    1. Cria driver Chrome local
    2. Instancia ElawCOGNA
    3. Faz login
    4. Busca e baixa o documento
    5. Retorna caminho do arquivo em temp_downloads/

    Args:
        process_number: Número do processo
        client_name: Nome do cliente/robô

    Returns:
        Caminho do arquivo baixado em temp_downloads/
    """
    driver = None
    try:
        logger.info(f"Iniciando download para processo {process_number}")

        # 1. Criar driver
        driver = _criar_driver_local()

        # 2. Criar instância do sistema (passa pasta Downloads do usuário)
        elaw = ElawCOGNA(
            driver=driver,
            download_path=os.path.join(os.path.expanduser("~"), "Downloads")
        )

        # 3. Login
        logger.info("Entrando no sistema...")
        elaw.ENTRAR_NO_SISTEMA()

        logger.info("Fazendo login...")
        if not elaw.LOGIN():
            raise Exception("Falha no login")

        logger.info("Login realizado com sucesso")

        # 4. Baixar documento
        logger.info(f"Baixando documento do processo {process_number}")
        if not elaw.baixa_documento_anexo(process_number):
            raise Exception("Falha ao baixar documento")

        logger.info("Download concluído")

        # 5. Pegar arquivo baixado da pasta Downloads do usuário
        logger.info("Buscando arquivo baixado...")
        arquivo_baixado = _buscar_ultimo_arquivo_baixado()

        logger.info(f"Arquivo encontrado: {arquivo_baixado}")

        # 6. Mover para temp_downloads/
        temp_dir = os.path.join(os.getcwd(), "temp_downloads")
        os.makedirs(temp_dir, exist_ok=True)

        # Pega o nome do arquivo que já foi renomeado pelo sistema
        nome_arquivo = os.path.basename(arquivo_baixado)
        destino = os.path.join(temp_dir, nome_arquivo)

        logger.info(f"Movendo arquivo para: {destino}")
        shutil.move(arquivo_baixado, destino)

        logger.info(f"Arquivo salvo com sucesso em temp_downloads/")
        return destino

    except Exception as e:
        logger.error(f"Erro ao baixar documento: {e}")
        raise

    finally:
        if driver:
            logger.info("Fechando navegador...")
            driver.quit()


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

    # Anti-detecção
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Downloads
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    prefs = {
        "download.default_directory": downloads_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

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

    logger.info("Driver Chrome criado com sucesso")
    return driver


def _buscar_ultimo_arquivo_baixado(diretorio=None, timeout=60):
    """
    Busca o último arquivo baixado na pasta Downloads
    Aguarda download completar (sem arquivos .crdownload ou .tmp)

    Args:
        diretorio: Pasta de downloads (padrão: ~/Downloads)
        timeout: Tempo máximo de espera em segundos

    Returns:
        str: Caminho completo do arquivo baixado

    Raises:
        Exception: Se timeout for atingido sem encontrar arquivo
    """
    if not diretorio:
        diretorio = os.path.join(os.path.expanduser("~"), "Downloads")

    logger.info(f"Buscando último arquivo em: {diretorio}")
    tempo_inicial = time.time()

    # Pega lista de arquivos antes
    arquivos_antes = set(os.listdir(diretorio)) if os.path.exists(diretorio) else set()

    while time.time() - tempo_inicial < timeout:
        try:
            # Busca arquivos atuais
            arquivos_atuais = set(os.listdir(diretorio))

            # Verifica se há arquivos temporários (download em andamento)
            temp_files = [
                f for f in arquivos_atuais
                if f.endswith('.crdownload') or f.endswith('.tmp')
            ]

            if temp_files:
                logger.info(f"Download em andamento: {temp_files[0]}")
                time.sleep(1)
                continue

            # Busca novos arquivos
            novos_arquivos = arquivos_atuais - arquivos_antes

            if novos_arquivos:
                # Filtra apenas arquivos válidos
                arquivos_validos = [
                    f for f in novos_arquivos
                    if not f.endswith('.crdownload')
                    and not f.endswith('.tmp')
                    and not f.startswith('.')
                ]

                if arquivos_validos:
                    arquivo = sorted(arquivos_validos)[0]
                    caminho_completo = os.path.join(diretorio, arquivo)

                    # Verifica se o arquivo está completo (tamanho estável)
                    tamanho_inicial = os.path.getsize(caminho_completo)
                    time.sleep(2)
                    tamanho_final = os.path.getsize(caminho_completo)

                    if tamanho_inicial == tamanho_final:
                        logger.info(f"Arquivo baixado: {arquivo}")
                        return caminho_completo

            time.sleep(1)

        except Exception as e:
            logger.warning(f"Erro ao verificar downloads: {e}")
            time.sleep(1)

    raise Exception(f"Timeout ao aguardar download ({timeout}s)")
```

---

### **ETAPA 3: Atualizar `worker.py`**

**Não precisa de mudanças!** O worker já está preparado:
- Chama `download_document(process_number, client_name)`
- Pega o arquivo retornado
- Faz upload para storage (local ou Azure)

O método `process_task` no worker já faz:
```python
# 3. Executa a lógica RPA (download do documento)
local_file_path = download_document(process_number, client_name)

# 4. Upload para Azure/Local Storage
blob_url = azure_storage.upload_file(local_file_path, blob_name)

# 5. Atualiza status para 'completed' com file_path
TaskRepository.update_task_status(task_id, TaskStatus.COMPLETED, file_path=blob_url)
```

---

### **ETAPA 4: Adaptar Método de Renomeação no `cogna.py`**

**Modificar `_processar_renomeacao_documento`:**

```python
def _processar_renomeacao_documento(self, numero_processo: str, nome_documento: str):
    """
    Processa a renomeação do documento baixado: aguarda download,
    identifica tipo e renomeia.

    MODIFICAÇÃO: Agora move o arquivo para temp_downloads/ do projeto

    Args:
        numero_processo (str): Número do processo
        nome_documento (str): Nome do documento na tabela

    Returns:
        str: Caminho do arquivo em temp_downloads/ ou None
    """
    try:
        print("="*70)
        print("ETAPA 5: Processando renomeação do documento...")
        print("="*70)

        # Identifica o tipo do documento
        tipo_documento = self._identificar_tipo_documento(nome_documento)
        print(f"🏷️  Tipo identificado: {tipo_documento}")

        # Aguarda o download completar
        arquivo_baixado = self._aguardar_download_completo(timeout=60)

        if arquivo_baixado:
            # Renomeia o arquivo
            arquivo_renomeado = self._renomear_documento_baixado(
                arquivo_baixado,
                numero_processo,
                tipo_documento
            )

            if arquivo_renomeado:
                # NOVO: Move para temp_downloads/
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
                return arquivo_baixado
        else:
            print("⚠️ Não foi possível detectar o arquivo baixado")
            return None

    except Exception as e:
        print(f"❌ Erro ao processar renomeação: {e}")
        traceback.print_exc()
        return None
```

**Adicionar ao `__init__`:**
```python
def __init__(self, driver=None, usuario=None, senha=None, download_path=None):
    # ... código existente ...
    self._ultimo_arquivo_baixado = None  # NOVO: Para rastrear último arquivo
```

**Adicionar método getter:**
```python
def get_ultimo_arquivo_baixado(self) -> Optional[str]:
    """
    Retorna o caminho do último arquivo baixado e processado

    Returns:
        str: Caminho completo do arquivo ou None
    """
    return self._ultimo_arquivo_baixado
```

---

### **ETAPA 5: Copiar e Adaptar Classe ElawCOGNA**

**Estrutura de pastas:**
```
rpa-fluxlaw/
├── sistemas/
│   ├── __init__.py           # Criar vazio
│   └── elaw/
│       ├── __init__.py       # Criar vazio
│       └── cogna.py          # Copiar de D:\Files\Auryn\autodev\rpa-fluxlaw\sistemas\elaw\cogna.py
├── rpa_logic.py              # Atualizar com novo código
├── worker.py                 # Não precisa alterar
└── requirements.txt          # Descomentar selenium
```

**Passos:**
1. Criar pasta `sistemas/elaw/`
2. Criar arquivos `__init__.py` vazios
3. Copiar `cogna.py` para `sistemas/elaw/`
4. Aplicar modificações listadas acima

---

### **ETAPA 6: Atualizar `requirements.txt`**

```txt
# Descomentar as linhas:
selenium==4.18.1
webdriver-manager==4.0.1
```

---

### **ETAPA 7: Simplificar `cogna.py` - Remover Selenoid**

**Remover/Simplificar:**

1. **Remover método `_detect_local_mode` (linhas 31-69)**
   - Não é mais necessário

2. **Simplificar `__init__`:**
   ```python
   def __init__(self, driver=None, usuario=None, senha=None, download_path=None):
       self.url_producao = "https://kroton.elaw.com.br/processoList.elaw"
       self.driver = driver
       self.user = usuario if usuario else "lima.feigelson06"
       self.password = senha if senha else "@Ingrid74"
       self.url_processo = "https://kroton.elaw.com.br/processoList.elaw"
       self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads")
       self._ultimo_arquivo_baixado = None  # Para rastrear último arquivo baixado
   ```

3. **Atualizar método `ENTRAR_NO_SISTEMA`:**
   - Remover linhas que verificam Selenoid
   - Manter apenas a navegação para URL

4. **Atualizar `ACESSO_ABA_ANEXOS`:**
   - Sempre processar renomeação (remover verificação `if self.is_local_mode`)
   - Linhas 975, 1020, 1031, 1042, 1058, 1072, 1086: remover condição

---

### **ETAPA 8: Atualizar Imports no `rpa_logic.py`**

**Substituir todo o conteúdo do `rpa_logic.py` pelo código da ETAPA 2**

Adicionar imports no topo:
```python
import os
import time
import shutil
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Import da classe do sistema eLaw
from sistemas.elaw.cogna import ElawCOGNA

logger = logging.getLogger(__name__)
```

---

## **RESUMO DAS MUDANÇAS**

| Arquivo | Ação | Mudanças Principais |
|---------|------|---------------------|
| `cogna.py` | **Adaptar** | • Remover Selenoid<br>• Mover arquivos para `temp_downloads/`<br>• Simplificar `__init__`<br>• Adicionar `get_ultimo_arquivo_baixado()` |
| `rpa_logic.py` | **Substituir** | • Implementar `download_document()`<br>• Adicionar `_criar_driver_local()`<br>• Adicionar `_buscar_ultimo_arquivo_baixado()` |
| `worker.py` | **Nenhuma** | Já está preparado |
| `requirements.txt` | **Descomentar** | Habilitar Selenium e webdriver-manager |
| Estrutura | **Criar** | `sistemas/elaw/__init__.py` e `cogna.py` |

---

## **FLUXO COMPLETO APÓS INTEGRAÇÃO**

```
1. API recebe upload de planilha com process_numbers
   ↓
2. Tarefas criadas no MongoDB (status: pending)
   ↓
3. Celery Beat detecta tarefas pendentes (a cada 10 min)
   ↓
4. Worker chama process_task(task_id)
   ↓
5. process_task chama download_document(process_number, client_name)
   ↓
6. download_document:
   ├─ Cria driver Chrome local
   ├─ Instancia ElawCOGNA
   ├─ Faz login no eLaw
   ├─ Busca processo
   ├─ Acessa anexos
   ├─ Baixa documento (vai para ~/Downloads do usuário)
   ├─ Aguarda download completar
   ├─ Identifica tipo (inicial/subsídio/documento)
   ├─ Renomeia arquivo (ex: inicial_processo_0569584892017805.pdf)
   ├─ Move para temp_downloads/ do projeto
   └─ Retorna caminho: temp_downloads/inicial_processo_0569584892017805.pdf
   ↓
7. Worker pega arquivo de temp_downloads/
   ↓
8. Worker faz upload para downloads/client_name/process_number.pdf (ou Azure)
   ↓
9. Worker salva caminho no MongoDB (status: completed)
   ↓
10. Remove arquivo de temp_downloads/
```

---

## **TESTES APÓS INTEGRAÇÃO**

### **Teste 1: Verificar Estrutura**
```bash
# Verificar se pastas foram criadas
ls -la sistemas/elaw/
ls -la temp_downloads/
```

### **Teste 2: Testar Import**
```python
python -c "from sistemas.elaw.cogna import ElawCOGNA; print('OK')"
```

### **Teste 3: Testar RPA Isolado**
```python
from rpa_logic import download_document

# Testar download
arquivo = download_document("0569584-89.2017.8.05.0001", "cliente_teste")
print(f"Arquivo baixado: {arquivo}")
```

### **Teste 4: Testar Fluxo Completo**
```bash
# 1. Iniciar API
python main.py

# 2. Iniciar Worker (em outro terminal)
celery -A worker worker --beat --loglevel=info --pool=solo

# 3. Fazer upload de planilha
curl -X POST "http://localhost:8000/tasks/upload/cogna_teste" \
  -F "file=@planilha_teste.csv"

# 4. Aguardar processamento (10 min ou forçar manualmente)

# 5. Verificar status
curl http://localhost:8000/tasks/status/0569584-89.2017.8.05.0001
```

---

## **CHECKLIST DE IMPLEMENTAÇÃO**

- [ ] Criar pasta `sistemas/elaw/`
- [ ] Criar arquivos `__init__.py`
- [ ] Copiar `cogna.py` para `sistemas/elaw/`
- [ ] Remover código Selenoid de `cogna.py`
- [ ] Adicionar método `get_ultimo_arquivo_baixado()` em `cogna.py`
- [ ] Modificar `_processar_renomeacao_documento()` para mover arquivos
- [ ] Substituir conteúdo de `rpa_logic.py`
- [ ] Descomentar selenium em `requirements.txt`
- [ ] Executar `pip install -r requirements.txt`
- [ ] Testar imports
- [ ] Testar RPA isolado
- [ ] Testar fluxo completo via API

---

## **PRÓXIMOS PASSOS**

1. **Implementar as mudanças** seguindo este plano
2. **Testar cada etapa** individualmente
3. **Adicionar tratamento de erros** específicos do eLaw
4. **Criar logs detalhados** para debugging
5. **Documentar credenciais** do eLaw em arquivo seguro
6. **Configurar retry** para falhas de login/rede
7. **Adicionar mais sistemas** eLaw seguindo o mesmo padrão

---

## **OBSERVAÇÕES IMPORTANTES**

- ✅ O código já tem renomeação inteligente (identifica inicial/subsídio)
- ✅ O código já aguarda download completar
- ✅ A arquitetura está preparada para receber múltiplos sistemas
- ⚠️ Credenciais hardcoded devem ser movidas para variáveis de ambiente
- ⚠️ Testar com vários tipos de documentos
- ⚠️ Adicionar timeout configurável para downloads grandes
