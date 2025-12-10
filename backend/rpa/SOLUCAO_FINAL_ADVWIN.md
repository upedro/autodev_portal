# ✅ SOLUÇÃO ENCONTRADA: Mapeamento Correto dos Parâmetros

## 🎯 Problema Identificado

A API retorna status 200, mas os documentos **não aparecem** no ADVWin porque estávamos usando os parâmetros **invertidos**!

---

## 🔑 Mapeamento Correto

Conforme você descobriu:

| Parâmetro | Valor Correto | Exemplo |
|-----------|---------------|---------|
| **Codigo_OR** | Código da pasta no ADVWin | `00016-000407` |
| **Id_OR** | Número do processo | `5013062-24.2025.8.21.5001` |

### ❌ O que estávamos fazendo (ERRADO):
```python
codigo_or = "50130622420258215001"  # ❌ Número do processo limpo
id_or = "null"                       # ❌ Null
```

### ✅ O que devemos fazer (CORRETO):
```python
codigo_or = "00016-000407"                    # ✅ Código da pasta
id_or = "5013062-24.2025.8.21.5001"          # ✅ Número do processo
```

---

## 🛠️ Como Aplicar a Correção

### Opção 1: Teste Rápido com Valores Fixos

Edite `test_quick_supersim_ged.py`:

```python
# Linha ~225, na função test_ged_upload
resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos,
    numero_processo=NUMERO_PROCESSO,
    tabela_or="Pastas",
    codigo_or="00016-000407",                    # ← CÓDIGO DA PASTA
    id_or="5013062-24.2025.8.21.5001"           # ← NÚMERO DO PROCESSO
)
```

### Opção 2: Teste Completo com Valores Fixos

Edite `test_supersim_to_ged.py`:

```python
# Linha ~205, na função test_ged_upload
codigo_or = "00016-000407"                       # ← CÓDIGO DA PASTA
id_or = NUMERO_PROCESSO_TESTE                   # ← NÚMERO DO PROCESSO

resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos,
    numero_processo=NUMERO_PROCESSO_TESTE,
    tabela_or=tabela_or,
    codigo_or=codigo_or,
    id_or=id_or
)
```

---

## 🔄 Solução Dinâmica (Futuro)

Para automação completa, seria necessário:

### 1. Buscar o código da pasta dinamicamente

Criar um método no `ADVWinAPI`:

```python
def buscar_pasta_por_processo(self, numero_processo: str) -> Optional[str]:
    """
    Busca uma pasta no ADVWin pelo número do processo
    Retorna o codigo_comp da pasta
    """
    url = f"{self.host}/api/partner/pastas/buscar"

    params = {"numero_processo": numero_processo}

    response = self.session.get(url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        # Assumindo que retorna {"data": {"codigo_comp": "00016-000407"}}
        return data.get('data', {}).get('codigo_comp')

    return None
```

### 2. Usar no helper automaticamente

```python
# Em ged_helper.py
def enviar_documentos_ged(...):
    # Se codigo_or não for fornecido, busca dinamicamente
    if not codigo_or:
        logger.info("Buscando código da pasta no ADVWin...")
        codigo_or = self.api.buscar_pasta_por_processo(numero_processo)

        if not codigo_or:
            logger.error("Pasta não encontrada no ADVWin!")
            return {"sucesso": False, "erro": "Pasta não encontrada"}

        logger.info(f"Código da pasta encontrado: {codigo_or}")

    # Usa o número do processo como Id_OR
    if not id_or:
        id_or = numero_processo
```

---

## 🧪 Teste Imediato

Execute com os valores corretos:

```bash
python test_quick_supersim_ged.py
```

Mas **ANTES**, edite o arquivo e adicione:

```python
# Em test_quick_supersim_ged.py, linha ~90
resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos,
    numero_processo=NUMERO_PROCESSO,
    tabela_or="Pastas",
    codigo_or="00016-000407",                    # ← AJUSTE AQUI
    id_or="5013062-24.2025.8.21.5001"           # ← AJUSTE AQUI
)
```

---

## 📋 Checklist

- [ ] Confirmar que `00016-000407` é o código correto da pasta no ADVWin
- [ ] Editar o teste para usar esses valores
- [ ] Executar o teste
- [ ] Verificar no ADVWin se os documentos apareceram
- [ ] ✅ SUCESSO!

---

## 🎯 Resultado Esperado

Após executar com os valores corretos:

```
INFO - Código: 00016-000407
INFO - ID: 5013062-24.2025.8.21.5001

[1/3] Status: 200 ✓ Documento enviado!
[2/3] Status: 200 ✓ Documento enviado!
[3/3] Status: 200 ✓ Documento enviado!

✓ Sucesso: 3
✗ Falha: 0
```

E os documentos **DEVEM aparecer** no ADVWin na pasta `00016-000407`! ✅

---

## 📞 Próximos Passos

1. **Imediato**: Testar com valores corretos fixos
2. **Curto prazo**: Implementar busca dinâmica de pasta
3. **Longo prazo**: Integrar no worker com lookup automático

---

**Data**: 2025-11-19
**Status**: ✅ Solução identificada
**Ação**: Ajustar teste com valores corretos e executar
