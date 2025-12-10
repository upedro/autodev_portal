# 🔧 Correção: Endpoint e Payload da API ADVWin

## ❌ Problema Encontrado

```
2025-11-19 13:12:32,794 - ERROR - Erro na autenticação - Status: 404
Response: {"status":404,"message":"Not Found."}
```

### Causa

O endpoint e o payload estavam **incorretos**:

❌ **Endpoint errado:** `/api/partner/auth/login`
❌ **Campo errado:** `"pass": "senha"`

## ✅ Solução Aplicada

### Documentação Oficial Encontrada:

```
Endpoint: https://URL_BASE/api/partner/login
Method: POST
Body (JSON):
{
  "user": "meu usuário",
  "password": "minha senha de acesso"
}

Response 200:
{
  "status": 200,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI18..."
  }
}
```

### Correção Aplicada

**Arquivo:** [sistemas/advwin/advwin_api.py](sistemas/advwin/advwin_api.py#L94-L102)

**Antes (❌ incorreto):**

```python
url = f"{self.host}/api/partner/auth/login"

payload = {
    "user": self.user,
    "pass": self.password  # ❌ Campo errado
}
```

**Depois (✅ correto):**

```python
url = f"{self.host}/api/partner/login"  # ✅ Endpoint correto

payload = {
    "user": self.user,
    "password": self.password  # ✅ Campo correto
}
```

### Estrutura de Resposta

O token é extraído de `data.token`:

```python
if response.status_code == 200:
    data = response.json()

    # Tenta obter o token (já estava correto)
    self.token = (
        data.get('token') or
        data.get('access_token') or
        data.get('data', {}).get('token')  # ✅ Pega de data.token
    )
```

## 🚀 Executar Novamente

Com a correção aplicada, execute:

```bash
# Teste rápido
python test_quick_supersim_ged.py

# OU teste completo
python test_supersim_to_ged.py
```

## 📊 Saída Esperada

### Autenticação Bem-Sucedida:

```
INFO - Iniciando autenticação na API ADVWin...
INFO - POST https://lfeigelson.twtinfo.com.br/api/partner/login
INFO - Payload: {'user': 'leo_api', 'password': '***'}
INFO - Status Code: 200
INFO - ✓ Autenticação realizada com sucesso!
```

### Response esperado:

```json
{
  "status": 200,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

## 📋 Resumo de Todas as Correções

| # | Problema | Solução | Status |
|---|----------|---------|--------|
| 1 | `download_path` incorreto | Usar `downloads_dir` | ✅ |
| 2 | Métodos inexistentes | `ENTRAR_NO_SISTEMA()` + `LOGIN()` | ✅ |
| 3 | Processo não encontrado | Normalizar números | ✅ |
| 4 | SSL Certificate Error | Desabilitar verificação SSL | ✅ |
| 5 | KeyError 'falha' | Usar `.get()` com defaults | ✅ |
| 6 | Endpoint 404 | `/api/partner/login` | ✅ |
| 7 | Campo payload errado | `"password"` não `"pass"` | ✅ |

## 🎯 Endpoints Corretos da API

### Login:
```
POST https://lfeigelson.twtinfo.com.br/api/partner/login
Body: {"user": "leo_api", "password": "lf@FluxLaw#2025"}
```

### Upload GED:
```
POST https://lfeigelson.twtinfo.com.br/api/partner/ged/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}
```

---

**Data**: 2025-11-19
**Status**: ✅ Correção aplicada
**Próximo**: Testar autenticação e upload completo
