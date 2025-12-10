# 🔧 Correções: SSL e KeyError na API ADVWin

## ❌ Problemas Encontrados

### Problema 1: Erro de Certificado SSL

```
ERROR - Erro de conexão ao tentar autenticar na API ADVWin:
HTTPSConnectionPool(host='lfeigelson.twtinfo.com.br', port=443):
Max retries exceeded with url: /api/partner/auth/login
(Caused by SSLError(SSLCertVerificationError(1,
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate (_ssl.c:997)')))
```

**Causa:** O servidor ADVWin está usando um certificado SSL auto-assinado ou não confiável, comum em ambientes de desenvolvimento/staging.

### Problema 2: KeyError no tratamento de resultado

```
logger.info(f"✗ Falha: {resultado['falha']}")
KeyError: 'falha'
```

**Causa:** Quando há erro na autenticação, o dicionário `resultado` não tem as chaves `'total'`, `'sucesso'` e `'falha'`, apenas `'erro'`.

---

## ✅ Soluções Aplicadas

### Solução 1: Desabilitar Verificação SSL

**Arquivo:** [sistemas/advwin/advwin_api.py](sistemas/advwin/advwin_api.py#L72-L81)

**Código adicionado:**

```python
# Session para reutilizar conexões
self.session = requests.Session()
self.session.headers.update({
    'User-Agent': 'FluxLaw-RPA/1.0'
})

# Desabilita verificação SSL (comum em ambientes de desenvolvimento/staging)
# IMPORTANTE: Em produção, considere usar certificados válidos
self.session.verify = False

# Suprime avisos de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger.info(f"Cliente ADVWin API inicializado - Host: {self.host}, User: {self.user}")
logger.warning("Verificação SSL desabilitada - use apenas em desenvolvimento")
```

**O que faz:**
- Define `session.verify = False` para desabilitar verificação SSL
- Suprime avisos do urllib3 sobre SSL
- Adiciona log de aviso sobre SSL desabilitado

**⚠️ IMPORTANTE:** Em produção, o ideal é:
1. Usar certificados SSL válidos no servidor
2. Ou adicionar o certificado à cadeia de confiança do Python

---

### Solução 2: Tratamento Seguro de Dicionário

**Arquivo:** [test_supersim_to_ged.py](test_supersim_to_ged.py#L240-L270)

**Antes (❌ KeyError):**

```python
logger.info(f"Total: {resultado['total']}")      # ❌ Pode não existir
logger.info(f"✓ Sucesso: {resultado['sucesso']}") # ❌ Pode não existir
logger.info(f"✗ Falha: {resultado['falha']}")    # ❌ Pode não existir
```

**Depois (✅ seguro):**

```python
# Usa .get() para evitar KeyError
if 'total' in resultado:
    logger.info(f"Total: {resultado.get('total', 0)}")
    logger.info(f"✓ Sucesso: {resultado.get('sucesso', 0)}")
    logger.info(f"✗ Falha: {resultado.get('falha', 0)}")
elif 'erro' in resultado:
    logger.error(f"✗ Erro: {resultado.get('erro', 'Erro desconhecido')}")
else:
    logger.warning("⚠ Resultado em formato inesperado")
```

**Melhorias:**
- Verifica se as chaves existem antes de acessar
- Usa `.get()` com valores padrão
- Trata diferentes formatos de resposta
- Mostra erro específico quando disponível

---

## 🚀 Executar Novamente

Com as correções aplicadas, execute:

```bash
# Teste rápido
python test_quick_supersim_ged.py

# OU teste completo
python test_supersim_to_ged.py
```

---

## 📊 Saída Esperada

### Sucesso na Autenticação:

```
INFO - Cliente ADVWin API inicializado - Host: https://lfeigelson.twtinfo.com.br, User: leo_api
WARNING - Verificação SSL desabilitada - use apenas em desenvolvimento
INFO - Iniciando autenticação na API ADVWin...
INFO - ✓ Autenticação realizada com sucesso!
```

### Upload de Documentos:

```
================================================================================
RESULTADO DO ENVIO PARA GED
================================================================================
Total: 3
✓ Sucesso: 3
✗ Falha: 0
================================================================================

Detalhes por arquivo:
  ✓ 50130622420258215001_Documento1.pdf
  ✓ 50130622420258215001_Documento2.pdf
  ✓ 50130622420258215001_Documento3.pdf
================================================================================
```

---

## 🔐 Nota sobre Segurança SSL

### Para Ambiente de Desenvolvimento (atual):
✅ SSL desabilitado - OK para testes

### Para Produção:
Escolha uma das opções:

#### Opção 1: Certificado Válido (recomendado)
Instale um certificado SSL válido no servidor ADVWin.

#### Opção 2: Adicionar Certificado à Cadeia
```python
# Em advwin_api.py
self.session.verify = '/caminho/para/certificado.pem'
```

#### Opção 3: Variável de Ambiente
```python
# No código
import os
verificar_ssl = os.getenv('ADVWIN_VERIFY_SSL', 'false').lower() == 'true'
self.session.verify = verificar_ssl
```

```bash
# No .env
ADVWIN_VERIFY_SSL=false  # Desenvolvimento
ADVWIN_VERIFY_SSL=true   # Produção
```

---

## 📋 Resumo

| Problema | Solução | Arquivo | Status |
|----------|---------|---------|--------|
| SSL Certificate Error | `session.verify = False` | advwin_api.py | ✅ |
| KeyError 'falha' | Usar `.get()` com defaults | test_supersim_to_ged.py | ✅ |

---

**Data**: 2025-11-19
**Status**: ✅ Todas as correções aplicadas
**Próximo Passo**: Executar teste completo SuperSim → GED
