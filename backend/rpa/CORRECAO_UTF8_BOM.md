# 🔧 Correção: UTF-8 BOM na Resposta da API ADVWin

## ❌ Problema Encontrado

```
ERROR - Erro inesperado durante autenticação:
Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)

json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig):
line 1 column 1 (char 0)
```

### O que é UTF-8 BOM?

**BOM (Byte Order Mark)** é uma sequência de bytes (`EF BB BF`) que alguns sistemas adicionam no início de arquivos UTF-8. O Python JSON decoder não consegue fazer parse de JSON com BOM sem tratamento especial.

### Causa

O servidor ADVWin está retornando a resposta JSON com UTF-8 BOM no início:

```
EF BB BF {"status": 200, "data": {"token": "..."}}
^^^^^^^
  BOM
```

Isso causa erro ao tentar fazer `response.json()`.

---

## ✅ Solução Aplicada

**Arquivo:** [sistemas/advwin/advwin_api.py](sistemas/advwin/advwin_api.py#L109-L122)

### Correção Implementada:

```python
if response.status_code == 200:
    # Remove UTF-8 BOM se presente
    response.encoding = 'utf-8-sig'

    try:
        data = response.json()
    except Exception as json_error:
        # Tenta decodificar manualmente removendo BOM
        logger.warning(f"Erro ao fazer parse do JSON: {json_error}")
        logger.info("Tentando remover BOM manualmente...")

        import json
        text = response.content.decode('utf-8-sig')
        data = json.loads(text)
```

### Como Funciona:

1. **Primeira tentativa:** Define `response.encoding = 'utf-8-sig'`
   - `utf-8-sig` é um codec que automaticamente remove o BOM

2. **Fallback:** Se ainda falhar, decodifica manualmente:
   - `response.content.decode('utf-8-sig')` remove o BOM
   - `json.loads(text)` faz o parse do JSON limpo

### Benefícios:

✅ Funciona com respostas COM BOM
✅ Funciona com respostas SEM BOM
✅ Logging claro quando usa fallback
✅ Não quebra se o servidor corrigir o BOM no futuro

---

## 🚀 Executar Novamente

Com a correção aplicada, execute:

```bash
# Teste rápido
python test_quick_supersim_ged.py

# OU teste completo
python test_supersim_to_ged.py
```

---

## 📊 Saída Esperada

### Autenticação Bem-Sucedida (sem BOM):

```
INFO - POST https://lfeigelson.twtinfo.com.br/api/partner/login
INFO - Status Code: 200
INFO - ✓ Autenticação realizada com sucesso!
```

### Autenticação Bem-Sucedida (com BOM + fallback):

```
INFO - POST https://lfeigelson.twtinfo.com.br/api/partner/login
INFO - Status Code: 200
WARNING - Erro ao fazer parse do JSON: Unexpected UTF-8 BOM...
INFO - Tentando remover BOM manualmente...
INFO - ✓ Autenticação realizada com sucesso!
```

### Token Extraído:

```
INFO - ✓ Autenticação realizada com sucesso!
DEBUG - Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## 📋 Resumo de Todas as Correções

| # | Problema | Solução | Status |
|---|----------|---------|--------|
| 1 | `download_path` incorreto | `downloads_dir` | ✅ |
| 2 | Métodos inexistentes | `ENTRAR_NO_SISTEMA()` + `LOGIN()` | ✅ |
| 3 | Processo não encontrado | Normalizar números | ✅ |
| 4 | SSL Certificate Error | `session.verify = False` | ✅ |
| 5 | KeyError 'falha' | `.get()` com defaults | ✅ |
| 6 | Endpoint 404 | `/api/partner/login` | ✅ |
| 7 | Campo payload errado | `"password"` não `"pass"` | ✅ |
| 8 | **UTF-8 BOM** | **`utf-8-sig` codec** | ✅ |

---

## 🔍 Debugging

Se ainda houver problemas, verifique a resposta raw:

```python
# Adicione ao código de debug:
logger.info(f"Response bytes (hex): {response.content[:20].hex()}")
logger.info(f"Response text (raw): {response.text[:100]}")
```

Se ver `efbbbf` no início do hex, é BOM UTF-8.

---

## 📚 Referências

- [UTF-8 BOM](https://en.wikipedia.org/wiki/Byte_order_mark)
- [Python utf-8-sig codec](https://docs.python.org/3/library/codecs.html#encodings-and-unicode)
- [Requests encoding](https://requests.readthedocs.io/en/latest/user/quickstart/#response-content)

---

**Data**: 2025-11-19
**Status**: ✅ Correção aplicada
**Próximo**: Validar token e testar upload GED completo
