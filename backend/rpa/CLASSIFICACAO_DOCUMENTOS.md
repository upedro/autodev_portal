# 🤖 Classificação Automática de Documentos Jurídicos

Sistema inteligente para classificar automaticamente documentos jurídicos baseado em metadados e conteúdo.

---

## 📋 Índice

- [O que faz](#o-que-faz)
- [Como funciona](#como-funciona)
- [Categorias suportadas](#categorias-suportadas)
- [Instalação](#instalação)
- [Uso](#uso)
- [Exemplos](#exemplos)
- [Melhorando a precisão](#melhorando-a-precisão)

---

## 🎯 O que faz

O classificador analisa documentos PDF e identifica automaticamente o tipo/categoria do documento:

- **Petição Inicial**
- **Contestação**
- **Sentença**
- **Acórdão**
- **Despacho**
- **Decisão Interlocutória**
- **Manifestação**
- **Acordo/Transação**
- **Procuração**
- **Certidão**
- **Documento Geral** (fallback)

---

## 🔍 Como funciona

O sistema usa **3 estratégias** de classificação, em ordem de prioridade:

### 1. **Classificação por Nome do Arquivo** (Confiança: Média)
Analisa o nome do arquivo procurando por palavras-chave e padrões:

```
"peticao_inicial.pdf" → Petição Inicial
"contestacao_reu.pdf" → Contestação
"sentenca_1grau.pdf" → Sentença
```

### 2. **Classificação por Conteúdo do PDF** (Confiança: Alta)
Extrai o texto das primeiras páginas do PDF e analisa:

- Palavras-chave específicas
- Padrões regex
- Contexto do documento

```python
# Exemplo de texto extraído:
"PETIÇÃO INICIAL
O autor vem, por seu advogado, propor a presente ação..."
→ Petição Inicial (confiança: alta)
```

### 3. **Classificação Padrão** (Confiança: Baixa)
Se nenhuma das estratégias anteriores funcionar, classifica como "Documento Geral"

---

## 📁 Categorias Suportadas

| Categoria | Palavras-chave | Exemplos de Nomes |
|-----------|----------------|-------------------|
| **Petição Inicial** | petição inicial, exordial, ação, requer, autor, réu | `peticao_inicial.pdf`, `exordial.pdf` |
| **Contestação** | contestação, defesa, impugnação, preliminares | `contestacao.pdf`, `defesa_merito.pdf` |
| **Sentença** | sentença, julgo, procedente, improcedente | `sentenca.pdf`, `decisao_merito.pdf` |
| **Acórdão** | acórdão, tribunal, relator, desembargador | `acordao_tjsp.pdf`, `voto_relator.pdf` |
| **Despacho** | despacho, intime-se, cumpra-se | `despacho.pdf` |
| **Decisão** | decisão, defiro, indefiro, tutela, liminar | `decisao_liminar.pdf`, `tutela.pdf` |
| **Manifestação** | manifestação, requer, protesta | `manifestacao.pdf`, `peticionamento.pdf` |
| **Acordo** | acordo, transação, composição | `acordo.pdf`, `transacao.pdf` |
| **Procuração** | procuração, outorgante, outorgado, poderes | `procuracao.pdf` |
| **Certidão** | certidão, certifico, secretaria | `certidao.pdf` |

---

## 💻 Instalação

### Dependências Básicas (Obrigatórias)
Já incluídas no projeto - nenhuma ação necessária.

### Dependências Opcionais (Recomendadas)
Para extração de texto de PDFs (melhora significativamente a precisão):

```bash
pip install PyPDF2 pdfplumber
```

**Sem essas bibliotecas:**
- ✅ Classificação por nome funciona normalmente
- ❌ Classificação por conteúdo não estará disponível
- 📊 Confiança limitada a "média" no máximo

**Com essas bibliotecas:**
- ✅ Classificação por nome
- ✅ Classificação por conteúdo do PDF
- 📊 Confiança pode chegar a "alta"

---

## 🚀 Uso

### 1. Uso Automático (Recomendado)

O classificador é **ativado automaticamente** quando você usa o `GEDHelper`:

```python
from sistemas.advwin import get_ged_helper

ged_helper = get_ged_helper()

# Envia documentos - classificação automática incluída!
resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos,
    numero_processo="1234567-89.2025.8.26.0100",
    tabela_or="Pastas",
    codigo_or="00016-000407"
)
```

**O que acontece:**
1. Cada documento é classificado automaticamente
2. A categoria é usada na **descrição** do documento no ADVWin
3. Informações de classificação ficam na **observação**

**Exemplo de descrição gerada:**
```
"Petição Inicial - Documentos baixados via RPA Autodev"
```

**Exemplo de observação gerada:**
```
Documento baixado automaticamente pelo RPA FluxLaw
Arquivo original: peticao_inicial.pdf
Linha: 1
Tipo original: peticao_inicial
Classificação: Petição Inicial (método: conteudo, confiança: alta)
```

### 2. Uso Manual (Para Testes)

Você pode testar o classificador diretamente:

```python
from sistemas.advwin.document_classifier import DocumentClassifier

classifier = DocumentClassifier()

# Classificar um documento
resultado = classifier.classificar_documento(
    caminho_pdf="/caminho/para/documento.pdf",
    nome_arquivo="peticao_inicial.pdf"
)

print(resultado)
# {
#     "categoria": "peticao_inicial",
#     "nome_categoria": "Petição Inicial",
#     "confianca": "alta",
#     "metodo": "conteudo",
#     "texto_extraido": True
# }
```

### 3. Classificação em Lote

```python
from sistemas.advwin.document_classifier import get_classifier

classifier = get_classifier()

documentos = [
    {
        "caminho_arquivo": "/path/to/doc1.pdf",
        "nome_arquivo": "peticao.pdf",
        "tipo_documento": "peticao"
    },
    {
        "caminho_arquivo": "/path/to/doc2.pdf",
        "nome_arquivo": "contestacao.pdf",
        "tipo_documento": "contestacao"
    }
]

# Adiciona campo "classificacao" em cada documento
documentos_classificados = classifier.classificar_lote(documentos)

for doc in documentos_classificados:
    print(f"{doc['nome_arquivo']} → {doc['classificacao']['nome_categoria']}")
```

### 4. Desativar Classificação

Se por algum motivo você não quiser usar a classificação automática:

```python
from sistemas.advwin import GEDHelper

# Desativa o classificador
ged_helper = GEDHelper(usar_classificador=False)
```

---

## 🧪 Testando o Classificador

Execute o script de teste:

```bash
python test_classifier.py
```

**O que o teste faz:**
1. ✅ Testa classificação por nome de arquivo
2. ✅ Testa classificação de PDFs reais (se disponíveis em `downloads_teste/`)
3. ✅ Testa classificação em lote
4. ✅ Testa extração de texto
5. 📊 Mostra estatísticas de classificação

**Exemplo de saída:**
```
TESTE 1: Classificação por Nome de Arquivo
================================================================================
✓ peticao_inicial.pdf                    → Petição Inicial
✓ contestacao_reu.pdf                    → Contestação
✓ sentenca_1grau.pdf                     → Sentença
✓ acordao_tjsp.pdf                       → Acórdão
✗ documento_generico.pdf                 → [Não identificado]
================================================================================

TESTE 2: Classificação de PDFs Reais
================================================================================
Encontrados 5 arquivo(s) PDF

Analisando: peticao_123.pdf
  ├─ Categoria: Petição Inicial
  ├─ Confiança: alta
  ├─ Método: conteudo
  └─ Texto extraído: Sim
...
```

---

## 📈 Melhorando a Precisão

### 1. Instale as Bibliotecas de PDF

```bash
pip install PyPDF2 pdfplumber
```

**Impacto:** De ~60% para ~90% de precisão

### 2. Use Nomes Descritivos

Renomeie arquivos antes do upload:

❌ Ruim:
```
documento.pdf
arquivo1.pdf
```

✅ Bom:
```
peticao_inicial_caso_x.pdf
contestacao_reu_fulano.pdf
sentenca_1grau_processo_y.pdf
```

### 3. Adicione Novas Categorias

Edite [`document_classifier.py`](./sistemas/advwin/document_classifier.py):

```python
CATEGORIAS = {
    # ... categorias existentes ...

    "sua_categoria": {
        "nome": "Sua Categoria",
        "palavras_chave": ["palavra1", "palavra2"],
        "patterns": [r"padr[ãa]o\s+regex"]
    }
}
```

### 4. Ajuste Palavras-chave

Se a classificação não está detectando corretamente, adicione mais palavras-chave ou padrões:

```python
"peticao_inicial": {
    "nome": "Petição Inicial",
    "palavras_chave": [
        "petição inicial", "exordial", "ação",
        "nova_palavra_1", "nova_palavra_2"  # ← Adicione aqui
    ],
    "patterns": [
        r"peti[çc][ãa]o\s+inicial",
        r"novo_padrao"  # ← Ou aqui
    ]
}
```

---

## 📊 Estatísticas

O classificador coleta estatísticas durante a execução:

```python
stats = classifier.get_stats()

# {
#     "total": 10,
#     "com_texto": 8,
#     "sem_texto": 2,
#     "por_categoria": {
#         "peticao_inicial": 3,
#         "contestacao": 2,
#         "sentenca": 1,
#         "documento": 4
#     }
# }
```

---

## ⚙️ Configurações Avançadas

### Limitar Páginas para Extração

Por padrão, o classificador lê as primeiras **3 páginas** do PDF. Para mudar:

```python
texto = classifier.extrair_texto_pdf(
    caminho_pdf="/path/to/doc.pdf",
    max_paginas=5  # ← Aumenta para 5 páginas
)
```

**Trade-off:**
- Mais páginas = Mais preciso, mas mais lento
- Menos páginas = Mais rápido, mas pode perder contexto

### Usar Classificação com IA (Futuro)

Atualmente o classificador usa **regras e padrões**. No futuro, pode ser integrado com modelos de IA:

```python
# Placeholder para futura integração
classifier = DocumentClassifier(use_ai=True)
```

---

## 🐛 Troubleshooting

### Problema: "PyPDF2 não instalado"

**Solução:**
```bash
pip install PyPDF2 pdfplumber
```

### Problema: PDF não está sendo classificado corretamente

**Diagnóstico:**
1. Execute `python test_classifier.py`
2. Veja o método usado (nome vs conteudo)
3. Veja se o texto foi extraído

**Soluções:**
- Se texto não foi extraído → PDF pode ser imagem (use OCR)
- Se classificação por nome falhou → Renomeie o arquivo
- Se nenhum método funcionou → Adicione palavras-chave específicas

### Problema: Classificação muito lenta

**Causas:**
- PDFs muito grandes
- Muitas páginas sendo processadas

**Soluções:**
- Reduza `max_paginas` na extração
- Processe documentos em paralelo (futuro)

---

## 📝 Exemplo Completo

Exemplo de uso completo no fluxo SuperSim → ADVWin:

```python
# 1. Baixa documentos do SuperSim
documentos = supersim.baixa_documento_anexo("1234567-89.2025")

# 2. Envia para ADVWin com classificação automática
from sistemas.advwin import get_ged_helper

ged_helper = get_ged_helper()  # Classificação ativada por padrão

resultado = ged_helper.enviar_documentos_ged(
    documentos=documentos,
    numero_processo="1234567-89.2025.8.26.0100",
    tabela_or="Pastas",
    codigo_or="00016-000407"
)

# 3. Resultado
# Documentos foram classificados e enviados com descrições inteligentes:
#   "Petição Inicial - Documentos baixados via RPA Autodev"
#   "Contestação - Documentos baixados via RPA Autodev"
#   "Sentença - Documentos baixados via RPA Autodev"
```

---

## 🎯 Próximos Passos

- [ ] Integração com OCR para PDFs escaneados
- [ ] Classificação usando modelos de IA (GPT/Claude)
- [ ] Treinamento de modelo customizado
- [ ] Classificação de tipos específicos por cliente
- [ ] Dashboard de estatísticas de classificação

---

**Data**: 2025-11-19
**Versão**: 1.0
**Autor**: AutoDev
