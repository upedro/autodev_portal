# Teste Standalone - RPA eLaw COGNA

## Descrição

Este é um teste que **roda fora do worker**, permitindo testar o RPA de forma independente sem precisar do Celery, Redis ou qualquer outra infraestrutura.

## Arquivo de Teste

- **Arquivo:** `test_rpa_standalone.py`
- **Localização:** Raiz do projeto

## Pré-requisitos

1. Python 3.x instalado
2. Google Chrome instalado
3. Dependências instaladas:

```bash
pip install selenium webdriver-manager
```

**Nota:** Você NÃO precisa ter Redis, Celery ou qualquer outra dependência do worker instalada para executar este teste.

## Como Executar

### Passo 1: Navegue até a pasta do projeto

```bash
cd d:\Files\Auryn\autodev\rpa-fluxlaw
```

### Passo 2: Execute o script

```bash
python test_rpa_standalone.py
```

### Passo 3: Escolha o teste desejado

O script apresentará um menu interativo:

```
Escolha o teste a executar:
1 - Teste de Login Simples
2 - Teste de Login + Pesquisa de Processo
3 - Teste Completo: Baixa de Documentos
4 - Teste Completo: Inserir Andamento
5 - Executar TODOS os testes

Digite sua opcao (1-5):
```

## Testes Disponíveis

### Teste 1: Login Simples
- Testa apenas o login no sistema eLaw COGNA
- Tempo estimado: ~15 segundos
- Útil para: Verificar credenciais e conectividade

### Teste 2: Login + Pesquisa de Processo
- Faz login e pesquisa um processo específico
- Tempo estimado: ~30 segundos
- Útil para: Verificar funcionalidade de pesquisa

### Teste 3: Baixa de Documentos (COMPLETO)
- Executa o fluxo completo:
  1. Login
  2. Acessa lista de processos
  3. Pesquisa processo
  4. Acessa o processo
  5. Acessa aba de anexos
  6. Baixa documento
  7. Renomeia e move para `downloads_standalone/`
- Tempo estimado: ~60 segundos
- Útil para: Testar fluxo completo de download

### Teste 4: Inserir Andamento (COMPLETO)
- Executa o fluxo completo:
  1. Login
  2. Acessa lista de processos
  3. Pesquisa processo
  4. Acessa o processo
  5. Acessa inclusão de andamentos
  6. Preenche dados do andamento
  7. Salva andamento
- Tempo estimado: ~60 segundos
- Útil para: Testar inserção de andamentos

### Teste 5: Executar TODOS
- Executa os 4 testes em sequência
- Tempo estimado: ~3-4 minutos
- Útil para: Validação completa do sistema

## Configuração

### Processo de Teste

O número do processo de teste está definido no script:

```python
NUMERO_PROCESSO_TESTE = "0569584-89.2017.8.05.0001"
```

Para testar com outro processo, edite esta variável no arquivo `test_rpa_standalone.py`.

### Credenciais

As credenciais estão definidas no script:

```python
USUARIO = "lima.feigelson06"
SENHA = "@Ingrid74"
```

**ATENÇÃO:** Em produção, use variáveis de ambiente ou arquivo `.env` para armazenar credenciais.

### Pasta de Downloads

Os documentos baixados serão salvos em:
```
d:\Files\Auryn\autodev\rpa-fluxlaw\downloads_standalone\
```

### Logs

Os logs serão salvos em:
```
d:\Files\Auryn\autodev\rpa-fluxlaw\logs_standalone\
```

Cada execução gera um arquivo de log com timestamp:
```
test_standalone_2025-11-06_14-30-15.log
```

## Saída do Teste

### Durante a Execução

O teste exibe logs em tempo real no console:

```
2025-11-06 14:30:15 - INFO - ======================================================================
2025-11-06 14:30:15 - INFO - TESTE 3: FLUXO COMPLETO - BAIXA DE DOCUMENTOS
2025-11-06 14:30:15 - INFO - ======================================================================
2025-11-06 14:30:16 - INFO - Criando driver Chrome local...
2025-11-06 14:30:18 - INFO - Driver Chrome local criado com sucesso (modo stealth)
2025-11-06 14:30:18 - INFO - Realizando login...
...
```

### Ao Final

Um resumo dos resultados:

```
######################################################################
# RESUMO DOS TESTES
######################################################################
3. Baixa de Documentos: PASSOU
######################################################################
# RESULTADO FINAL: TODOS OS TESTES PASSARAM!
######################################################################

Log completo salvo em: d:\Files\Auryn\autodev\rpa-fluxlaw\logs_standalone\test_standalone_2025-11-06_14-30-15.log
```

## Diferenças entre Teste Standalone e Worker

| Característica | Teste Standalone | Worker (Produção) |
|---------------|------------------|-------------------|
| Dependências | Apenas Selenium | Celery, Redis, SQLAlchemy, etc. |
| Execução | Direta via Python | Via fila de tarefas (Celery) |
| Logs | Console + arquivo local | Sistema de logs do worker |
| Downloads | `downloads_standalone/` | Configurado no worker |
| Uso | Desenvolvimento e testes | Produção |
| Paralelismo | Um teste por vez | Múltiplas tarefas simultâneas |

## Vantagens do Teste Standalone

✅ **Independente:** Não precisa de infraestrutura (Redis, Celery, etc.)
✅ **Rápido:** Execução direta sem overhead de fila
✅ **Simples:** Um único arquivo Python
✅ **Debug fácil:** Logs claros e diretos no console
✅ **Portátil:** Pode rodar em qualquer máquina com Python e Chrome

## Troubleshooting

### Erro: "ChromeDriver not found"

**Solução:** O script usa `webdriver_manager` que baixa automaticamente o driver. Certifique-se de ter conexão com a internet na primeira execução.

### Erro: "Login failed"

**Solução:** Verifique as credenciais no script ou se o site está acessível.

### Erro: "Processo não encontrado"

**Solução:** Verifique se o número do processo está correto e existe no sistema.

### Navegador não fecha após o teste

**Solução:** O script aguarda alguns segundos para você visualizar o resultado. Se travar, feche o navegador manualmente.

## Integração com CI/CD

Este teste pode ser facilmente integrado em pipelines de CI/CD:

```yaml
# Exemplo para GitHub Actions
- name: Executar Teste Standalone
  run: python test_rpa_standalone.py
```

## Próximos Passos

Após validar o RPA com este teste standalone, você pode:

1. Integrar com o worker usando o arquivo `worker.py`
2. Configurar o Celery para execução em produção
3. Adicionar mais casos de teste
4. Implementar testes unitários adicionais

## Suporte

Para dúvidas ou problemas, consulte:
- `README.md` - Documentação geral do projeto
- `GUIA_TESTES.md` - Guia completo de testes
- Logs em `logs_standalone/` - Detalhes da execução
