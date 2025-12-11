# =============================================================================
# Portal AutoDev - Script de Reorganizac~ao
# Autor: Claude Code + Tech Lead
# Data: 2025-12-10
# =============================================================================

param(
    [switch]$DryRun = $false,  # Simula sem executar
    [switch]$Backup = $true    # Cria backup antes
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

# -----------------------------------------------------------------------------
# 0. Verificac~oes Iniciais
# -----------------------------------------------------------------------------
Write-Host "`n=============================================" -ForegroundColor Magenta
Write-Host "  Portal AutoDev - Reorganizac~ao" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

if ($DryRun) {
    Write-Warning "Modo DRY RUN - Nenhuma alterac~ao ser'a feita"
}

$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = Get-Location
}

Write-Step "Verificando estrutura atual..."
if (-not (Test-Path "$rootDir/backend/rpa")) {
    Write-Error "Diret'orio backend/rpa n~ao encontrado. Execute na raiz do projeto!"
    exit 1
}
Write-Success "Estrutura atual validada"

# -----------------------------------------------------------------------------
# 1. Backup (se habilitado)
# -----------------------------------------------------------------------------
if ($Backup -and -not $DryRun) {
    Write-Step "Criando backup..."
    $backupDir = "$rootDir/backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    # Backup de arquivos cr'iticos
    Copy-Item "$rootDir/docker-compose.yml" "$backupDir/" -ErrorAction SilentlyContinue
    Copy-Item "$rootDir/backend/rpa/docker-compose*.yml" "$backupDir/" -ErrorAction SilentlyContinue
    Copy-Item "$rootDir/backend/*/Dockerfile" "$backupDir/" -Recurse -ErrorAction SilentlyContinue
    Copy-Item "$rootDir/frontend/Dockerfile" "$backupDir/" -ErrorAction SilentlyContinue

    Write-Success "Backup criado em: $backupDir"
}

# -----------------------------------------------------------------------------
# 2. Criar Nova Estrutura de Diret'orios
# -----------------------------------------------------------------------------
Write-Step "Criando nova estrutura de diret'orios..."

$newDirs = @(
    "src/frontend",
    "src/api",
    "src/rpa",
    "infra/docker",
    "docs/architecture",
    "docs/api",
    "docs/rpa",
    "docs/changelog",
    "docs/setup",
    "docs/archive",
    "scripts/setup"
)

foreach ($dir in $newDirs) {
    $fullPath = Join-Path $rootDir $dir
    if ($DryRun) {
        Write-Host "  [DRY] Criaria: $dir"
    } else {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Success "Criado: $dir"
    }
}

# -----------------------------------------------------------------------------
# 3. Mover C'odigo-Fonte para /src
# -----------------------------------------------------------------------------
Write-Step "Movendo c'odigo-fonte para /src..."

$codeMoves = @(
    @{From="frontend/*"; To="src/frontend/"; Exclude=@("Dockerfile")},
    @{From="backend/api/*"; To="src/api/"; Exclude=@("Dockerfile", "README.md")},
    @{From="backend/rpa/*"; To="src/rpa/"; Exclude=@("Dockerfile", "*.md", "docker-compose*.yml")}
)

foreach ($move in $codeMoves) {
    $sourcePattern = Join-Path $rootDir $move.From
    $destDir = Join-Path $rootDir $move.To

    Get-ChildItem -Path (Split-Path $sourcePattern) -Recurse -File | ForEach-Object {
        $relativePath = $_.FullName.Replace((Split-Path $sourcePattern), "")
        $shouldExclude = $false

        foreach ($pattern in $move.Exclude) {
            if ($_.Name -like $pattern) {
                $shouldExclude = $true
                break
            }
        }

        if (-not $shouldExclude) {
            $destPath = Join-Path $destDir $relativePath
            $destFolder = Split-Path $destPath

            if ($DryRun) {
                Write-Host "  [DRY] Moveria: $($_.FullName) -> $destPath"
            } else {
                New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
                Move-Item -Path $_.FullName -Destination $destPath -Force
                Write-Success "Movido: $($_.Name)"
            }
        }
    }
}

# -----------------------------------------------------------------------------
# 4. Mover Dockerfiles para /infra/docker
# -----------------------------------------------------------------------------
Write-Step "Movendo Dockerfiles para /infra/docker..."

$dockerMoves = @(
    @{From="backend/api/Dockerfile"; To="infra/docker/Dockerfile.api"},
    @{From="backend/rpa/Dockerfile"; To="infra/docker/Dockerfile.rpa"},
    @{From="frontend/Dockerfile"; To="infra/docker/Dockerfile.frontend"}
)

foreach ($move in $dockerMoves) {
    $source = Join-Path $rootDir $move.From
    $dest = Join-Path $rootDir $move.To

    if (Test-Path $source) {
        if ($DryRun) {
            Write-Host "  [DRY] Moveria: $($move.From) -> $($move.To)"
        } else {
            Move-Item -Path $source -Destination $dest -Force
            Write-Success "Movido: $(Split-Path $move.From -Leaf) -> $(Split-Path $move.To -Leaf)"
        }
    }
}

# -----------------------------------------------------------------------------
# 5. Mover docker-compose.yml para /infra
# -----------------------------------------------------------------------------
Write-Step "Movendo docker-compose para /infra..."

$composeMoves = @(
    @{From="docker-compose.yml"; To="infra/docker-compose.yml"},
    @{From="backend/rpa/docker-compose.prod.yml"; To="infra/docker-compose.prod.yml"}
)

foreach ($move in $composeMoves) {
    $source = Join-Path $rootDir $move.From
    $dest = Join-Path $rootDir $move.To

    if (Test-Path $source) {
        if ($DryRun) {
            Write-Host "  [DRY] Moveria: $($move.From) -> $($move.To)"
        } else {
            Move-Item -Path $source -Destination $dest -Force
            Write-Success "Movido: $(Split-Path $move.From -Leaf)"
        }
    }
}

# Marcar docker-compose duplicado para deletar
$dupCompose = Join-Path $rootDir "backend/rpa/docker-compose.yml"
if (Test-Path $dupCompose) {
    if ($DryRun) {
        Write-Host "  [DRY] Renomearia: backend/rpa/docker-compose.yml -> _del_docker-compose.yml"
    } else {
        $delPath = Join-Path $rootDir "backend/rpa/_del_docker-compose.yml"
        Move-Item -Path $dupCompose -Destination $delPath -Force
        Write-Warning "Marcado para deletar: _del_docker-compose.yml"
    }
}

# -----------------------------------------------------------------------------
# 6. Organizar Documentac~ao em /docs
# -----------------------------------------------------------------------------
Write-Step "Organizando documentac~ao em /docs..."

# Mover READMEs principais
$docMoves = @{
    # API
    "backend/api/README.md" = "docs/api/API_DOCS.md"

    # RPA - Guias principais
    "backend/rpa/README.md" = "docs/rpa/RPA_GUIDE.md"
    "backend/rpa/GUIA_TESTES.md" = "docs/rpa/TESTING_GUIDE.md"
    "backend/rpa/DOCKER.md" = "docs/rpa/DOCKER_RPA.md"
    "backend/rpa/INTEGRACAO_GED.md" = "docs/rpa/INTEGRACAO_GED.md"
    "backend/rpa/CLASSIFICACAO_DOCUMENTOS.md" = "docs/rpa/CLASSIFICACAO_DOCUMENTOS.md"
    "backend/rpa/EXAMPLES_API.md" = "docs/api/EXAMPLES_API.md"

    # Changelog
    "backend/rpa/CORRECAO_BUSCA_PROCESSO.md" = "docs/changelog/CORRECAO_BUSCA_PROCESSO.md"
    "backend/rpa/CORRECAO_ENDPOINT_ADVWIN.md" = "docs/changelog/CORRECAO_ENDPOINT_ADVWIN.md"
    "backend/rpa/CORRECAO_ID_OR_NULL.md" = "docs/changelog/CORRECAO_ID_OR_NULL.md"
    "backend/rpa/CORRECAO_SSL_ADVWIN.md" = "docs/changelog/CORRECAO_SSL_ADVWIN.md"
    "backend/rpa/CORRECAO_SUPERSIM_GED.md" = "docs/changelog/CORRECAO_SUPERSIM_GED.md"
    "backend/rpa/CORRECAO_UTF8_BOM.md" = "docs/changelog/CORRECAO_UTF8_BOM.md"
    "backend/rpa/SOLUCAO_FINAL_ADVWIN.md" = "docs/changelog/SOLUCAO_FINAL_ADVWIN.md"

    # Setup
    "backend/rpa/SETUP_REDIS_WINDOWS.md" = "docs/setup/SETUP_REDIS_WINDOWS.md"

    # Archive (documentos que podem ser revisados/deletados)
    "backend/rpa/IMPLEMENTACAO_CONCLUIDA.md" = "docs/archive/_del_IMPLEMENTACAO_CONCLUIDA.md"
    "backend/rpa/PLANO_INTEGRACAO_RPA.md" = "docs/archive/_del_PLANO_INTEGRACAO_RPA.md"
    "backend/rpa/MELHORIAS_TESTE.md" = "docs/archive/_del_MELHORIAS_TESTE.md"
    "backend/rpa/START_TESTE.md" = "docs/archive/_del_START_TESTE.md"
    "backend/rpa/TESTE_STANDALONE.md" = "docs/archive/_del_TESTE_STANDALONE.md"
    "backend/rpa/COMO_TESTAR_SUPERSIM_GED.md" = "docs/archive/_del_COMO_TESTAR_SUPERSIM_GED.md"
    "backend/rpa/README_API_INTEGRATION.md" = "docs/archive/_del_README_API_INTEGRATION.md"
    "backend/rpa/README_TESTES_GED.md" = "docs/archive/_del_README_TESTES_GED.md"
    "backend/rpa/CLAUDE.md" = "docs/archive/_del_CLAUDE_RPA.md"
}

foreach ($move in $docMoves.GetEnumerator()) {
    $source = Join-Path $rootDir $move.Key
    $dest = Join-Path $rootDir $move.Value

    if (Test-Path $source) {
        if ($DryRun) {
            Write-Host "  [DRY] Moveria: $($move.Key) -> $($move.Value)"
        } else {
            $destFolder = Split-Path $dest
            New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
            Move-Item -Path $source -Destination $dest -Force
            Write-Success "Movido: $(Split-Path $move.Key -Leaf)"
        }
    }
}

# -----------------------------------------------------------------------------
# 7. Frontend - Mover Attributions.md
# -----------------------------------------------------------------------------
$attrSource = Join-Path $rootDir "frontend/src/Attributions.md"
$attrDest = Join-Path $rootDir "src/frontend/src/Attributions.md"

if (Test-Path $attrSource) {
    if ($DryRun) {
        Write-Host "  [DRY] Moveria: frontend/src/Attributions.md"
    } else {
        New-Item -ItemType Directory -Path (Split-Path $attrDest) -Force | Out-Null
        Move-Item -Path $attrSource -Destination $attrDest -Force
        Write-Success "Movido: Attributions.md"
    }
}

# -----------------------------------------------------------------------------
# 8. Limpar Diret'orios Vazios
# -----------------------------------------------------------------------------
Write-Step "Limpando diret'orios vazios..."

$oldDirs = @("backend/api", "backend/rpa", "backend", "frontend")

foreach ($dir in $oldDirs) {
    $fullPath = Join-Path $rootDir $dir
    if (Test-Path $fullPath) {
        $items = Get-ChildItem -Path $fullPath -Recurse -Force
        if ($items.Count -eq 0) {
            if ($DryRun) {
                Write-Host "  [DRY] Removeria diret'orio vazio: $dir"
            } else {
                Remove-Item -Path $fullPath -Recurse -Force
                Write-Success "Removido diret'orio vazio: $dir"
            }
        } else {
            Write-Warning "Diret'orio $dir ainda cont'em arquivos (verifique manualmente)"
        }
    }
}

# -----------------------------------------------------------------------------
# RESUMO FINAL
# -----------------------------------------------------------------------------
Write-Host "`n=============================================" -ForegroundColor Magenta
Write-Host "  Reorganizac~ao Conclu'ida!" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

Write-Host "`nPR'OXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Atualize os build contexts no docker-compose.yml"
Write-Host "2. Atualize os paths nos Dockerfiles (COPY commands)"
Write-Host "3. Teste o build: docker-compose -f infra/docker-compose.yml build"
Write-Host "4. Revise arquivos marcados com _del_ em docs/archive/"
Write-Host "5. Delete os arquivos _del_ ap'os confirmar que n~ao s~ao necess'arios"
Write-Host "6. Atualize o README.md com a nova estrutura"
Write-Host "7. Atualize o CLAUDE.md com os novos paths"

if ($Backup -and -not $DryRun) {
    Write-Host "`n[BACKUP] Backup criado em: $backupDir" -ForegroundColor Cyan
}

Write-Host ""
