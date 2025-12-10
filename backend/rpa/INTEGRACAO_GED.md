# Integração ADVWin GED - Guia de Implementação

## 📋 Visão Geral

Este documento descreve como integrar o envio automático de documentos para o GED do ADVWin após o download pelos RPAs.

## 🔧 Configuração

### 1. Credenciais

As credenciais já estão configuradas no arquivo `.env`:

```bash
ADVWIN_HOST=https://lfeigelson.twtinfo.com.br
ADVWIN_USER=leo_api
ADVWIN_PASSWORD=lf@FluxLaw#2025
```

### 2. Módulos Disponíveis

- **`sistemas/advwin/advwin_api.py`**: Cliente principal da API
- **`sistemas/advwin/ged_helper.py`**: Helper simplificado para integração
- **`test_advwin_api.py`**: Script de testes standalone

## 🚀 Como Usar

### Opção 1: Usar o GED Helper (Recomendado)

O `GEDHelper` simplifica a integração e gerencia autenticação automaticamente:

```python
from sistemas.advwin import get_ged_helper

# Obtém instância do helper
ged_helper = get_ged_helper()

# Envia lista de documentos baixados pelo RPA
resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos_baixados,  # Lista retornada pelo RPA
    numero_processo="1234567-89.2024.1.00.0000",
    tabela_or="Pastas",  # Opções: Pastas, Agenda, Debite, Clientes
    codigo_or="123456"   # Opcional - usa numero_processo se não fornecido
)

# Verifica resultado
if resultado['sucesso'] > 0:
    print(f"✓ {resultado['sucesso']} documento(s) enviado(s) com sucesso")
if resultado['falha'] > 0:
    print(f"✗ {resultado['falha']} documento(s) falharam")
```

### Opção 2: Usar a API Diretamente

Para controle mais fino sobre o envio:

```python
from sistemas.advwin import ADVWinAPI

# Inicializa cliente
api = ADVWinAPI()

# Faz login
if api.login():
    # Envia um documento
    resultado = api.upload_ged(
        file_path="/path/to/documento.pdf",
        tabela_or="Pastas",
        codigo_or="123456",
        descricao="Petição Inicial - Processo 1234567",
        observacao="Documento baixado automaticamente"
    )

    if resultado.get("sucesso"):
        print("✓ Documento enviado com sucesso!")
```

## 📦 Integração no Worker

### Modificação no `worker.py`

Adicione o envio de GED após o download dos documentos:

```python
from sistemas.advwin import get_ged_helper

@celery_app.task(name='worker.process_task', bind=True, max_retries=3)
def process_task(self, task_id: str):
    try:
        # ... código existente de download ...

        # 3. Executa a lógica RPA (download dos documentos)
        logger.info(f"Executando download para processo {process_number}")
        documentos = download_document(process_number, client_name)

        if not documentos or len(documentos) == 0:
            raise Exception("Erro no download: nenhum documento foi baixado")

        logger.info(f"Download concluído: {len(documentos)} documento(s) baixado(s)")

        # *** NOVO: Envio para ADVWin GED ***
        try:
            logger.info("Enviando documentos para ADVWin GED...")
            ged_helper = get_ged_helper()

            resultado_ged = ged_helper.enviar_documentos_ged(
                documentos=documentos,
                numero_processo=process_number,
                tabela_or="Pastas",
                codigo_or=None  # Usa numero_processo automaticamente
            )

            logger.info(f"GED enviado: {resultado_ged['sucesso']} sucesso, {resultado_ged['falha']} falhas")

        except Exception as e:
            # Não falha a tarefa se o GED falhar, apenas loga o erro
            logger.error(f"Erro ao enviar para GED (não crítico): {e}")

        # 4. Upload para Azure Blob Storage (código existente)
        # ...

    except Exception as e:
        # ... tratamento de erro existente ...
```

### Pontos Importantes:

1. **Não-Crítico**: O envio para GED está em um try-catch separado para não falhar a tarefa se houver erro
2. **Autenticação Automática**: O helper gerencia autenticação automaticamente
3. **Código Automático**: Se `codigo_or` for None, usa o `numero_processo` limpo como código

## 📊 Formato dos Documentos

Os RPAs retornam documentos no formato:

```python
[
    {
        "numero_linha": 1,
        "nome_arquivo": "documento_original.pdf",
        "tipo_documento": "Petição_Inicial",
        "caminho_arquivo": "/path/temp_downloads/123456_Peticao_Inicial.pdf",
        "nome_arquivo_final": "123456_Peticao_Inicial.pdf"
    },
    # ... mais documentos
]
```

O helper automaticamente:
- Extrai informações relevantes
- Cria descrições apropriadas (máx 250 caracteres)
- Adiciona observações com metadados
- Envia para a API

## 🧪 Testando a Integração

### Teste Standalone

Execute o script de teste:

```bash
python test_advwin_api.py
```

Este script testa:
1. ✅ Autenticação na API
2. ✅ Upload de documento único
3. ✅ Upload de múltiplos documentos

### Teste com RPA

1. Execute um RPA para baixar documentos:
   ```bash
   python test_rpa_standalone_bclegal.py
   ```

2. Os documentos ficarão em `temp_downloads/`

3. Execute o teste da API que irá usar esses documentos

## 📝 Parâmetros da API

### Tabela_OR (Tabela de Origem)

Opções disponíveis:
- **`Pastas`**: Para documentos de processos/pastas
- **`Agenda`**: Para documentos de agenda
- **`Debite`**: Para documentos de débitos
- **`Clientes`**: Para documentos de clientes

### Codigo_OR (Código de Referência)

Depende da tabela:
- **Pastas**: `codigo_comp` (código da pasta)
- **Agenda**: `ident` (identificador da agenda)
- **Debite**: `numero` (número do débito)
- **Clientes**: `codigo` (código do cliente)

### Id_OR (ID de Movimentação)

Opcional. Use quando precisar associar a uma movimentação específica.

## 🔐 Segurança

- As credenciais são carregadas do `.env`
- O token é obtido via login e usado com Bearer Authentication
- O token é automaticamente renovado se expirar (401)
- A sessão HTTP é reutilizada para melhor performance

## 🐛 Troubleshooting

### Erro de Autenticação

```
ValueError: Credenciais ADVWin não configuradas!
```

**Solução**: Verifique se o `.env` contém `ADVWIN_HOST`, `ADVWIN_USER` e `ADVWIN_PASSWORD`

### Erro 401 - Unauthorized

**Solução**: O helper tenta renovar o token automaticamente. Se persistir, verifique as credenciais.

### Timeout

```
Timeout na requisição (mais de 120 segundos)
```

**Solução**: Arquivos muito grandes podem demorar. Considere aumentar o timeout em `advwin_api.py`:

```python
response = self.session.post(url, files=files, data=data, timeout=300)  # 5 minutos
```

### Arquivo não encontrado

```
Arquivo não encontrado: /path/to/file.pdf
```

**Solução**: Certifique-se de que os documentos ainda existem no `temp_downloads/` antes de enviar

## 📚 Referências

- **API ADVWin**: https://lfeigelson.twtinfo.com.br/api/partner/
- **Endpoint GED**: `/api/partner/ged/upload`
- **Endpoint Login**: `/api/partner/auth/login`

## 🎯 Próximos Passos

1. ✅ Teste o script standalone para validar credenciais
2. ✅ Execute os RPAs para ter documentos de teste
3. ✅ Teste o envio de GED com documentos reais
4. ⏳ Integre no worker.py (modifique conforme exemplo acima)
5. ⏳ Teste o fluxo completo end-to-end
6. ⏳ Monitore logs para validar sucesso dos envios
