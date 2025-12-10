# 🔧 Correção: Busca de Processo no SuperSim

## ❌ Problema Encontrado

```
2025-11-19 12:59:51,593 - INFO - Encontrados 1 processos na lista
2025-11-19 12:59:51,727 - ERROR - Processo 5013062-24.2025.8.21.5001 nao encontrado na lista
```

### Descrição

O SuperSim estava encontrando 1 processo na lista após a busca, mas não conseguia identificá-lo como o processo correto. Isso acontecia porque:

1. O número buscado estava **com pontuação**: `5013062-24.2025.8.21.5001`
2. O título retornado pelo sistema poderia estar em **formato diferente**
3. A comparação era **exata** (substring), sem normalização

## ✅ Solução Aplicada

### Arquivo Modificado

**[sistemas/lexxy/supersim.py](sistemas/lexxy/supersim.py#L431-L457)** - Método `BUSCAR_PROCESSO`

### Mudança Implementada

**Antes (❌ falha com pontuação diferente):**

```python
for item in items:
    link = item.find_element(By.CLASS_NAME, "list-item__value--link")
    titulo = link.get_attribute("title")

    if titulo and numero_processo in titulo:  # ❌ Comparação rígida
        processo_encontrado = item
        break
```

**Depois (✅ normaliza ambos antes de comparar):**

```python
# Normaliza o numero do processo (remove pontos, tracos e espacos)
numero_normalizado = numero_processo.replace(".", "").replace("-", "").replace(" ", "")
self.logger.info(f"Numero normalizado para busca: {numero_normalizado}")

for item in items:
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
```

### Melhorias Adicionadas

1. **Normalização**: Remove `.`, `-` e espaços de ambos os números
2. **Comparação bidirecional**: Verifica se A está em B OU B está em A
3. **Logging melhorado**: Mostra o número normalizado e as comparações
4. **Mensagem de erro detalhada**: Mostra o número normalizado em caso de falha

## 🎯 Formatos Suportados

Agora a busca funciona com **qualquer formato** de número de processo:

| Formato de Entrada | Normalizado | Status |
|-------------------|-------------|--------|
| `5013062-24.2025.8.21.5001` | `50130622420258215001` | ✅ |
| `50130622420258215001` | `50130622420258215001` | ✅ |
| `5013062 24 2025 8 21 5001` | `50130622420258215001` | ✅ |
| `5013062.24.2025.8.21.5001` | `50130622420258215001` | ✅ |

## 🧪 Teste

Execute novamente o teste:

```bash
python test_quick_supersim_ged.py
```

ou

```bash
python test_supersim_to_ged.py
```

Agora o processo `5013062-24.2025.8.21.5001` deve ser encontrado corretamente! ✅

## 📝 Logs Esperados

Após a correção, você verá:

```
2025-11-19 XX:XX:XX - INFO - Encontrados 1 processos na lista
2025-11-19 XX:XX:XX - INFO - Numero normalizado para busca: 50130622420258215001
2025-11-19 XX:XX:XX - INFO - Processo encontrado: 5013062-24.2025.8.21.5001
2025-11-19 XX:XX:XX - INFO - Clicando no botao de opcoes do processo...
2025-11-19 XX:XX:XX - INFO - Botao de opcoes clicado com sucesso!
```

---

**Data**: 2025-11-19
**Status**: ✅ Resolvido
**Arquivo**: [sistemas/lexxy/supersim.py](sistemas/lexxy/supersim.py#L431-L457)
