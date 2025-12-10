# 🧪 Guia de Testes - Sistema → ADVWin GED

Scripts de teste end-to-end para validar o fluxo completo: **Download → Classificação → Upload GED**

---

## 📋 Testes Disponíveis

| Script | Sistema Origem | Status |
|--------|---------------|--------|
| [`test_supersim_to_ged.py`](./test_supersim_to_ged.py) | Lexxy SuperSim | ✅ Pronto |
| [`test_cogna_to_ged.py`](./test_cogna_to_ged.py) | eLaw Cogna | ✅ Pronto |
| [`test_loft_to_ged.py`](./test_loft_to_ged.py) | BCLegal Loft | ✅ Pronto |

**Todos incluem:**
- ✅ Download automático de documentos
- ✅ Classificação automática (Petição, Sentença, etc.)
- ✅ Renomeação com categoria (ex: `123456_PeticaoInicial.pdf`)
- ✅ Upload para ADVWin GED
- ✅ Logs detalhados

---

## 🚀 Como Usar

### **Teste SuperSim → ADVWin**

```bash
python test_supersim_to_ged.py
```

**Configuração:**
1. Edite linha ~53: Ajuste o número do processo
   ```python
   NUMERO_PROCESSO_TESTE = "5013062-24.2025.8.21.5001"
   ```

2. Edite linha ~206: Ajuste o código da pasta no ADVWin
   ```python
   codigo_or = "00016-000407"
   ```

### **Teste Cogna → ADVWin**

```bash
python test_cogna_to_ged.py
```

**Configuração:**
1. Edite linha ~53: Ajuste o número do processo
2. Edite linha ~240: Ajuste o código da pasta

### **Teste Loft → ADVWin**

```bash
python test_loft_to_ged.py
```

**Configuração:**
1. Edite linha ~53: Ajuste o número do contrato
2. Edite linha ~240: Ajuste o código da pasta

---

## 🎯 O Que os Testes Fazem

```
1. Download  → 2. Classificação → 3. Renomeação → 4. Upload GED
   📥             🤖                ✏️              ☁️
```

### Exemplo Prático:

**Arquivo baixado:**
```
50130622420258215001_arquivo-original-9e7e30b3.pdf
```

**Após classificação automática:**
- Categoria: "Petição Inicial"
- Confiança: alta
- Método: conteúdo

**Arquivo renomeado:**
```
50130622420258215001_PeticaoInicial.pdf
```

**No ADVWin aparece:**
- Nome: `50130622420258215001_PeticaoInicial.pdf`
- Descrição: `Petição Inicial - Documentos baixados via RPA Autodev`

---

## ⚙️ Configurações Necessárias

### 1. Credenciais do ADVWin (`.env`)

```env
ADVWIN_HOST=https://lfeigelson.twtinfo.com.br
ADVWIN_USER=leo_api
ADVWIN_PASSWORD=sua_senha
```

### 2. Código da Pasta no ADVWin

**⚠️ IMPORTANTE:** Use o código da **pasta**, não do processo!

```python
# ❌ ERRADO
codigo_or = "50130622420258215001"  # Número do processo

# ✅ CORRETO
codigo_or = "00016-000407"  # Código da pasta no ADVWin
```

---

## 📁 Arquivos Gerados

```
rpa-fluxlaw/
├── downloads_teste/              # SuperSim
├── downloads_teste_cogna/        # Cogna
├── downloads_teste_loft/         # Loft
└── logs/
    ├── test_supersim_to_ged_*.log
    ├── test_cogna_to_ged_*.log
    └── test_loft_to_ged_*.log
```

---

## ✅ Checklist Antes de Executar

- [ ] Credenciais configuradas no `.env`
- [ ] Número do processo/contrato ajustado
- [ ] Código da pasta (`codigo_or`) correto
- [ ] Chrome instalado
- [ ] Internet estável

---

## 🐛 Problemas Comuns

### "API retorna 400"
**Causa:** `codigo_or` incorreto
**Solução:** Verifique o código da pasta no ADVWin

### "Nenhum documento baixado"
**Causa:** Processo não existe ou sem documentos
**Solução:** Verifique o número do processo

### "Timeout no login"
**Causa:** Credenciais incorretas ou sistema fora do ar
**Solução:** Teste manualmente no navegador

---

**Criado**: 2025-11-19
**Versão**: 1.0
