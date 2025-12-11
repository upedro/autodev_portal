# 🗑️ Arquivos para Deletar - Portal AutoDev

## ⚠️ IMPORTANTE: Leia antes de deletar!

**NÃO DELETE NADA ATÉ:**
1. ✅ A reorganização estiver completa
2. ✅ Todos os testes tiverem passado
3. ✅ A aplicação estiver rodando corretamente
4. ✅ Você ter revisado o conteúdo de cada arquivo marcado

---

## 📁 Categoria 1: Arquivos Duplicados

### Docker Compose Duplicado
```
backend/rpa/_del_docker-compose.yml
```
**Motivo:** Duplicado de `infra/docker-compose.yml`
**Ação:** DELETE após confirmar que infra/docker-compose.yml funciona

---

## 📁 Categoria 2: Documentação Obsoleta/Redundante

### Planejamento/Implementação (Já Concluído)
```
docs/archive/_del_IMPLEMENTACAO_CONCLUIDA.md
docs/archive/_del_PLANO_INTEGRACAO_RPA.md
```
**Motivo:** Documentos de planejamento de features já implementadas
**Ação:** REVISAR conteúdo → Mover informações importantes para docs/changelog → DELETE

### Melhorias/Testes (Informações Incorporadas)
```
docs/archive/_del_MELHORIAS_TESTE.md
docs/archive/_del_START_TESTE.md
docs/archive/_del_TESTE_STANDALONE.md
```
**Motivo:** Informações já incorporadas em `docs/rpa/TESTING_GUIDE.md`
**Ação:** REVISAR → Confirmar que info está em TESTING_GUIDE.md → DELETE

### Testes GED (Redundantes)
```
docs/archive/_del_COMO_TESTAR_SUPERSIM_GED.md
docs/archive/_del_README_TESTES_GED.md
docs/archive/_del_README_API_INTEGRATION.md
```
**Motivo:** Informações duplicadas ou já incorporadas em outros docs
**Ação:** REVISAR → Extrair comandos úteis para TESTING_GUIDE.md → DELETE

### CLAUDE.md Duplicado
```
docs/archive/_del_CLAUDE_RPA.md
```
**Motivo:** Havia um CLAUDE.md específico do RPA, mas agora temos um unificado na raiz
**Ação:** REVISAR → Confirmar que info importante está no CLAUDE.md raiz → DELETE

---

## 📁 Categoria 3: Diretórios Vazios (Após Reorganização)

```
backend/api/          # Vazio após mover para src/api
backend/rpa/          # Vazio após mover para src/rpa
backend/              # Vazio após remover api/ e rpa/
frontend/             # Vazio após mover para src/frontend
docker/               # Vazio ou apenas com mongo-init.js (verificar)
```

**Ação:** DELETE apenas após confirmar que estão realmente vazios

---

## 🔍 Categoria 4: Arquivos a Revisar (NÃO marcar _del ainda)

Estes arquivos NÃO foram marcados com `_del_` porque podem conter informações valiosas:

### Changelog Valioso
```
docs/changelog/CORRECAO_*.md
docs/changelog/SOLUCAO_FINAL_ADVWIN.md
```
**Motivo:** Histórico de correções importantes
**Ação:** MANTER - São úteis para troubleshooting futuro

### Guias e Documentação Ativa
```
docs/rpa/RPA_GUIDE.md
docs/rpa/TESTING_GUIDE.md
docs/rpa/DOCKER_RPA.md
docs/rpa/INTEGRACAO_GED.md
docs/rpa/CLASSIFICACAO_DOCUMENTOS.md
docs/api/API_DOCS.md
docs/api/EXAMPLES_API.md
docs/setup/SETUP_REDIS_WINDOWS.md
```
**Motivo:** Documentação ativa e necessária
**Ação:** MANTER e atualizar conforme necessário

---

## 🚨 Categoria 5: NUNCA DELETE

```
.env
.env.example
.gitignore
CLAUDE.md
README.md
src/**/*                    # Todo o código-fonte
infra/docker-compose.yml
infra/docker-compose.prod.yml
infra/docker/Dockerfile.*
scripts/deploy.ps1
package.json
requirements.txt
```

---

## 📋 Processo de Deleção Recomendado

### Passo 1: Revisão Individual (Faça ANTES de deletar)
```powershell
# Para cada arquivo _del_, revise o conteúdo:
code docs/archive/_del_IMPLEMENTACAO_CONCLUIDA.md

# Pergunte a si mesmo:
# - Há informações que não estão em outro lugar?
# - Há comandos ou exemplos úteis?
# - Há decisões arquiteturais documentadas?
```

### Passo 2: Extração de Informações Valiosas
```powershell
# Se encontrar info valiosa, copie para o documento apropriado:
# - Comandos úteis → docs/rpa/TESTING_GUIDE.md
# - Decisões de design → docs/architecture/ARCHITECTURE.md
# - Correções importantes → docs/changelog/[manter original]
```

### Passo 3: Deleção Segura
```powershell
# Apenas DEPOIS de revisar tudo:

# 1. Deletar arquivos marcados com _del_
Get-ChildItem -Path docs/archive -Filter "_del_*" | Remove-Item -Force

# 2. Deletar docker-compose duplicado
Remove-Item backend/rpa/_del_docker-compose.yml -Force

# 3. Deletar diretórios vazios
Remove-Item backend/api -Force -ErrorAction SilentlyContinue
Remove-Item backend/rpa -Force -ErrorAction SilentlyContinue
Remove-Item backend -Force -ErrorAction SilentlyContinue
Remove-Item frontend -Force -ErrorAction SilentlyContinue

# 4. Verificar que não deletou nada importante
git status
```

### Passo 4: Commit de Limpeza
```powershell
git add .
git commit -m "chore: remove obsolete and duplicate files after reorganization"
```

---

## 📊 Resumo Quantitativo

| Categoria | Quantidade | Tamanho Estimado | Ação |
|-----------|------------|------------------|------|
| Duplicados | 1 arquivo | ~2 KB | DELETE após testes |
| Docs Obsoletos | 8 arquivos | ~50 KB | REVISAR → DELETE |
| Diretórios Vazios | 4 dirs | 0 KB | DELETE se vazios |
| **TOTAL A DELETAR** | **~13 itens** | **~52 KB** | - |

---

## ✅ Checklist de Segurança

Antes de deletar QUALQUER arquivo, confirme:

- [ ] Fiz backup completo (via script de reorganização)
- [ ] Todos os testes passaram após reorganização
- [ ] Revisei CADA arquivo _del_ individualmente
- [ ] Extraí informações valiosas para outros docs
- [ ] Confirmei que diretórios estão realmente vazios
- [ ] Tenho um commit recente que posso reverter
- [ ] Avisei o time sobre a reorganização

---

## 🔄 Script de Deleção Automática (Use com Cuidado!)

```powershell
# =============================================================================
# APENAS EXECUTE APÓS REVISAR TODOS OS ARQUIVOS!
# =============================================================================

param([switch]$Confirm = $true)

if ($Confirm) {
    Write-Host "⚠️ Este script vai DELETAR arquivos permanentemente!" -ForegroundColor Red
    $response = Read-Host "Você revisou todos os arquivos _del_? (yes/no)"
    if ($response -ne "yes") {
        Write-Host "Operação cancelada." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "Deletando arquivos marcados com _del_..." -ForegroundColor Cyan

# Deletar documentos obsoletos
Remove-Item docs/archive/_del_* -Force -Verbose

# Deletar docker-compose duplicado
Remove-Item backend/rpa/_del_docker-compose.yml -Force -Verbose -ErrorAction SilentlyContinue

# Deletar diretórios vazios (apenas se estiverem vazios)
$dirsToCheck = @("backend/api", "backend/rpa", "backend", "frontend")
foreach ($dir in $dirsToCheck) {
    if (Test-Path $dir) {
        $items = Get-ChildItem $dir -Recurse
        if ($items.Count -eq 0) {
            Remove-Item $dir -Recurse -Force -Verbose
            Write-Host "✓ Removido: $dir (vazio)" -ForegroundColor Green
        } else {
            Write-Host "⚠ Mantido: $dir (contém $($items.Count) arquivos)" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n✅ Limpeza concluída!" -ForegroundColor Green
Write-Host "Execute 'git status' para revisar as mudanças." -ForegroundColor Cyan
```

**Salve como:** `scripts/cleanup.ps1`

---

## 📞 Dúvidas?

Se não tiver certeza se deve deletar algo:
1. ✅ **MANTENHA** - É melhor manter um arquivo a mais do que perder informação valiosa
2. 📦 Mova para `docs/archive/` em vez de deletar
3. 🤝 Consulte o time antes de deletar

---

**Última Atualização:** 2025-12-10
**Status:** Aguardando execução da reorganização
