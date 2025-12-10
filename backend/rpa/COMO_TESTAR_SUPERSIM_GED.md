# 🧪 Como Testar: SuperSim → ADVWin GED

Guia para testar o fluxo completo de download do Lexxy SuperSim e envio para ADVWin GED.

## 📋 Pré-requisitos

1. ✅ Credenciais configuradas no `.env`:
   - `LEXXY_USER` e `LEXXY_PASSWORD` (SuperSim)
   - `ADVWIN_HOST`, `ADVWIN_USER` e `ADVWIN_PASSWORD` (ADVWin)

2. ✅ Chrome instalado (para o RPA)

3. ✅ Dependências Python instaladas

## 🚀 Opção 1: Teste Rápido (Recomendado)

Para um teste rápido e direto:

```bash
cd D:\Files\Auryn\autodev\projeto-fluxlaw\rpa-fluxlaw
python test_quick_supersim_ged.py
```

### O que este teste faz:

1. ✅ Abre o Chrome
2. ✅ Faz login no Lexxy SuperSim
3. ✅ Busca o processo: **5013062-24.2025.8.21.5001**
4. ✅ Baixa todos os documentos
5. ✅ Renomeia com o padrão: `{numero_processo}_{nome_documento}.pdf`
6. ✅ Pede confirmação para enviar
7. ✅ Envia para ADVWin GED
8. ✅ Mostra relatório de sucesso/falhas

### Saída esperada:

```
================================================================================
  TESTE RÁPIDO: SuperSim → GED
================================================================================
  Processo: 5013062-24.2025.8.21.5001
  Tabela GED: Pastas
================================================================================

► ETAPA 1: Baixando documentos do SuperSim...
  ✓ Login realizado
  ✓ 3 documento(s) baixado(s)
    [1] 5013062242025821500_Documento1.pdf
    [2] 5013062242025821500_Documento2.pdf
    [3] 5013062242025821500_Documento3.pdf

► ETAPA 2: Enviando para ADVWin GED...

  Confirma envio para GED? (s/N): s

  ✓ Envio concluído:
    • Total: 3
    • Sucesso: 3
    • Falhas: 0

================================================================================
  ✓ TESTE CONCLUÍDO COM SUCESSO!
================================================================================
```

## 📊 Opção 2: Teste Completo (com logs detalhados)

Para um teste mais completo com logging:

```bash
cd D:\Files\Auryn\autodev\projeto-fluxlaw\rpa-fluxlaw
python test_supersim_to_ged.py
```

### Recursos adicionais:

- ✅ Logs detalhados salvos em arquivo
- ✅ Informações de debug completas
- ✅ Relatório detalhado por arquivo
- ✅ Opção de limpeza de arquivos temporários
- ✅ Interface mais verbosa

### Saída esperada:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              TESTE END-TO-END: LEXXY SUPERSIM → ADVWIN GED                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Processo de teste: 5013062-24.2025.8.21.5001
Data/Hora: 19/11/2025 14:30:00
Log: logs/test_supersim_to_ged_2025-11-19_14-30-00.log

################################################################################
# ETAPA 1: DOWNLOAD DE DOCUMENTOS - LEXXY SUPERSIM
################################################################################
# Processo: 5013062-24.2025.8.21.5001
################################################################################

Inicializando Lexxy SuperSim...
✓ Driver inicializado com sucesso
Realizando login no Lexxy SuperSim...
✓ Login realizado com sucesso
Baixando documentos do processo 5013062-24.2025.8.21.5001...

================================================================================
✓ DOWNLOAD CONCLUÍDO COM SUCESSO!
================================================================================
Total de documentos baixados: 3

Documentos:
  [1] 5013062242025821500_Documento1.pdf - Documento1
  [2] 5013062242025821500_Documento2.pdf - Documento2
  [3] 5013062242025821500_Documento3.pdf - Documento3
================================================================================

################################################################################
# ETAPA 2: ENVIO PARA ADVWIN GED
################################################################################
# Processo: 5013062-24.2025.8.21.5001
# Documentos: 3
################################################################################

Inicializando ADVWin API...
Configurações:
  - Tabela: Pastas
  - Código: automático
  - ID: nenhum

================================================================================
ATENÇÃO: Os documentos serão enviados para o ADVWin GED!
Processo: 5013062-24.2025.8.21.5001
Quantidade: 3 documento(s)
================================================================================
Deseja prosseguir com o envio? (s/N): s

Iniciando envio para GED...

================================================================================
✓ ENVIO PARA GED CONCLUÍDO!
================================================================================
Total: 3
✓ Sucesso: 3
✗ Falha: 0
================================================================================

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ✓ TESTE END-TO-END CONCLUÍDO COM SUCESSO!                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

RESUMO:
  • Processo: 5013062-24.2025.8.21.5001
  • Documentos baixados: 3
  • Enviados para GED: 3
  • Falhas no GED: 0

Log completo salvo em: logs/test_supersim_to_ged_2025-11-19_14-30-00.log
```

## ⚙️ Configurações

### Alterar o número do processo

#### No teste rápido:

Edite [test_quick_supersim_ged.py](test_quick_supersim_ged.py#L19):

```python
NUMERO_PROCESSO = "5013062-24.2025.8.21.5001"  # ← ALTERE AQUI
```

#### No teste completo:

Edite [test_supersim_to_ged.py](test_supersim_to_ged.py#L52):

```python
NUMERO_PROCESSO_TESTE = "5013062-24.2025.8.21.5001"  # ← ALTERE AQUI
```

### Alterar a tabela do GED

Opções disponíveis: `Pastas`, `Agenda`, `Debite`, `Clientes`

#### No teste rápido:

```python
TABELA_GED = "Pastas"  # ← ALTERE AQUI
```

#### No teste completo:

Em [test_supersim_to_ged.py](test_supersim_to_ged.py#L139), na função `test_ged_upload()`:

```python
tabela_or = "Pastas"  # ← ALTERE AQUI
```

## 📁 Onde ficam os arquivos

### Documentos baixados:
```
D:\Files\Auryn\autodev\projeto-fluxlaw\rpa-fluxlaw\
├── downloads_teste/
│   └── (arquivos baixados ficam aqui temporariamente)
└── temp_downloads/
    └── (arquivos renomeados ficam aqui)
```

### Logs:
```
D:\Files\Auryn\autodev\projeto-fluxlaw\rpa-fluxlaw\
└── logs/
    ├── test_supersim_to_ged_2025-11-19_14-30-00.log
    └── (outros logs...)
```

## 🐛 Troubleshooting

### Erro: "Credenciais não encontradas"

```
ValueError: Credenciais nao encontradas! Configure LEXXY_USER e LEXXY_PASSWORD
```

**Solução**: Verifique o arquivo `.env`:

```bash
LEXXY_USER=mariana.barcelos@limafeigelson.com.br
LEXXY_PASSWORD=Mpb@188336

ADVWIN_HOST=https://lfeigelson.twtinfo.com.br
ADVWIN_USER=leo_api
ADVWIN_PASSWORD=lf@FluxLaw#2025
```

### Erro: "Nenhum documento baixado"

Possíveis causas:
1. Processo não existe no SuperSim
2. Processo não tem documentos
3. Erro de navegação/timeout

**Solução**: Verifique os logs detalhados ou tente acessar manualmente o processo no SuperSim.

### Erro: "Falha na autenticação ADVWin"

```
Falha na autenticação com ADVWin API
```

**Solução**:
1. Verifique as credenciais `ADVWIN_*` no `.env`
2. Teste isoladamente: `python test_advwin_api.py`

### Chrome não abre

```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solução**: Instale o ChromeDriver ou use o Selenium Manager (já incluso no Selenium 4+).

## 🎯 Próximos Passos

Após o teste bem-sucedido:

1. ✅ Valide os documentos no ADVWin GED
2. ✅ Verifique se foram associados ao processo correto
3. ✅ Teste com outros processos
4. ✅ Integre no worker para automação completa (veja [worker_with_ged_example.py](worker_with_ged_example.py))

## 📞 Suporte

Em caso de dúvidas ou erros:

1. Verifique os logs em `logs/`
2. Consulte [INTEGRACAO_GED.md](INTEGRACAO_GED.md) para detalhes da API
3. Execute os testes isolados:
   - `python test_rpa_standalone_lexxy.py` (só SuperSim)
   - `python test_advwin_api.py` (só ADVWin)

## ✅ Checklist de Teste

Antes de executar:

- [ ] Arquivo `.env` configurado com todas as credenciais
- [ ] Chrome instalado
- [ ] Processo existe no SuperSim
- [ ] Internet estável
- [ ] Sem bloqueios de firewall

Durante o teste:

- [ ] Login no SuperSim funcionou
- [ ] Documentos foram baixados
- [ ] Arquivos aparecem em `temp_downloads/`
- [ ] Confirmou envio para GED
- [ ] Autenticação ADVWin funcionou
- [ ] Upload concluiu sem erros

Após o teste:

- [ ] Documentos visíveis no ADVWin GED
- [ ] Associados ao processo correto
- [ ] Nomes dos arquivos corretos
- [ ] Sem arquivos temporários deixados para trás
