# 📊 Upload de Planilha Excel - Guia Completo

## ✅ Funcionalidade Implementada

O sistema aceita planilhas Excel (.xlsx) e extrai números CNJ automaticamente.

---

## 📋 Formato da Planilha

### Opção 1: Com Coluna "CNJ" (Recomendado)

```
| CNJ                        | Outros Dados |
|----------------------------|--------------|
| 0001234-56.2024.8.00.0000 | ...          |
| 0005678-90.2023.8.26.0200 | ...          |
| 4000312-69.2025.8.26.0441 | ...          |
```

**O parser irá:**
1. Buscar coluna com nome "CNJ" na primeira linha
2. Ler apenas valores dessa coluna
3. Validar formato CNJ
4. Ignorar linhas vazias

### Opção 2: Sem Cabeçalho (Fallback)

Se não houver coluna "CNJ", o sistema busca em **todas as células** da primeira aba.

---

## ✅ Como Funciona

### 1. Upload no Frontend

```typescript
// Arquivo: src/pages/SolicitarServico.tsx
// Já implementado e funcionando!

<FileUploader onFileSelect={handleFileUpload} />
```

### 2. Backend Processa

```python
# Arquivo: backend/utils/excel_parser.py

# 1. Abre primeira aba
sheet = workbook.worksheets[0]

# 2. Procura coluna "CNJ" na linha 1
for cell in sheet[1]:
    if cell.value.upper() == "CNJ":
        cnj_column = found!

# 3. Lê apenas essa coluna
for row in sheet.rows:
    cnj = row[cnj_column]
    if is_valid_cnj(cnj):
        add to list
```

### 3. Validação Automática

Cada CNJ é validado com regex:
```
NNNNNNN-DD.AAAA.J.TR.OOOO

Exemplo válido:
0001234-56.2024.8.00.0000
```

---

## 🎯 Teste com Sua Planilha

### Arquivo: YDUKS Casos de Habilitação (1).xlsx

**Detectado:** 3 números CNJ ✅

O sistema:
1. ✅ Abriu primeira aba
2. ✅ Encontrou coluna "CNJ"
3. ✅ Extraiu 3 CNJs válidos
4. ✅ Criou solicitação

---

## 📊 Validações Aplicadas

### CNJ Válido
```
✅ 0001234-56.2024.8.00.0000
✅ 0005678-90.2023.8.26.0200
✅ 4000312-69.2025.8.26.0441
```

### CNJ Inválido (Ignorado)
```
❌ 123456 (muito curto)
❌ 00012-34.2024 (formato errado)
❌ ABC123 (não numérico)
```

---

## 🔧 Lógica de Busca

### Prioridade 1: Coluna "CNJ"

```python
# Procura header exato "CNJ" (case insensitive)
if header.upper() == "CNJ":
    use essa coluna
```

**Aceita:**
- "CNJ"
- "cnj"
- "Cnj"

### Prioridade 2: Fallback (Todas Células)

Se não encontrar coluna "CNJ":
- Busca em todas células da primeira aba
- Valida cada valor encontrado
- Ignora headers conhecidos (CNJ, PROCESSO, NÚMERO)

---

## 📝 Mensagens de Erro

### Nenhum CNJ Encontrado

```json
{
  "detail": "Nenhum número CNJ válido encontrado no arquivo Excel. Certifique-se de que a planilha tem uma coluna 'CNJ' com números de processo válidos."
}
```

### CNJs Inválidos

```json
{
  "detail": "Encontrados 5 CNJs inválidos. Exemplos: ['123', 'ABC', '00012']"
}
```

### Arquivo Inválido

```json
{
  "detail": "Formato de arquivo Excel inválido. Por favor, faça upload de um arquivo .xlsx válido"
}
```

---

## 🎯 Exemplo de Uso

### Via Frontend (UI)

1. Acesse: http://localhost:3000/solicitar
2. Escolha cliente
3. Escolha serviço
4. Clique em "Upload de Planilha"
5. Selecione arquivo .xlsx
6. Sistema mostra: "X número(s) CNJ detectados"
7. Clique em "Próximo" e "Enviar"

### Via API (cURL)

```bash
curl -X POST http://localhost:8001/api/solicitacoes/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@planilha.xlsx" \
  -F "cliente_id=690dc2b0b87de491cd982e86" \
  -F "servico=buscar_documentos"
```

---

## ✅ Comportamento Atual

### Com a planilha "YDUKS Casos de Habilitação (1).xlsx"

1. ✅ Sistema abre primeira aba
2. ✅ Encontra coluna "CNJ"
3. ✅ Extrai 3 CNJs válidos
4. ✅ Cria solicitação
5. ✅ Cria 3 tasks para o RPA (1 por CNJ)

**FUNCIONANDO PERFEITAMENTE!** 🎉

---

## 📊 Estatísticas de Parsing

O sistema loga:
```
INFO: Found CNJ column at index 2
INFO: Parsed 3 valid CNJs from Excel file
WARN: Found 1 invalid CNJ entries
```

---

## 🔧 Personalização

### Aceitar Outros Nomes de Coluna

Edite `backend/utils/excel_parser.py` linha 76:

```python
# Aceitar vários nomes
column_names = ["CNJ", "PROCESSO", "NÚMERO", "NUMERO_PROCESSO"]
if cell.value.strip().upper() in column_names:
    cnj_column = found!
```

---

## ✅ SISTEMA COMPLETO

**Upload Excel:** ✅ Funcionando
**Parser Robusto:** ✅ Coluna "CNJ" + Fallback
**Validação:** ✅ Regex completa
**Mensagens de Erro:** ✅ Claras e em português

**3 CNJs detectados da sua planilha!** 🚀
