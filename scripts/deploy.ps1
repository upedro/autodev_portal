# =============================================================================
# Portal AutoDev - Deploy Script (PowerShell)
# =============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "dev-mongo", "dev-full", "prod", "stop", "restart", "logs", "logs-api", "logs-rpa", "logs-frontend", "clean", "build", "health")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Show-Help {
    Write-Header "Portal AutoDev - Comandos"
    Write-Host "  DESENVOLVIMENTO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 dev          - Frontend + API + RPA + Redis"
    Write-Host "    .\deploy.ps1 dev-mongo    - Inclui MongoDB local"
    Write-Host "    .\deploy.ps1 dev-full     - Tudo + Flower (monitoramento)"
    Write-Host ""
    Write-Host "  PRODUCAO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 prod         - Build otimizado"
    Write-Host ""
    Write-Host "  GERENCIAMENTO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 build        - Constroi imagens"
    Write-Host "    .\deploy.ps1 stop         - Para containers"
    Write-Host "    .\deploy.ps1 restart      - Reinicia"
    Write-Host "    .\deploy.ps1 clean        - Remove tudo"
    Write-Host ""
    Write-Host "  LOGS:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 logs         - Todos os logs"
    Write-Host "    .\deploy.ps1 logs-api     - Logs da API"
    Write-Host "    .\deploy.ps1 logs-rpa     - Logs do RPA"
    Write-Host "    .\deploy.ps1 logs-frontend - Logs do Frontend"
    Write-Host ""
    Write-Host "  SAUDE:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 health       - Verifica servicos"
    Write-Host ""
}

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $true
    } catch {
        Write-Host "[ERRO] Docker nao esta rodando. Inicie o Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

function Start-Dev {
    Write-Header "Iniciando Desenvolvimento"
    Test-DockerRunning
    docker compose up -d frontend api rpa-worker rpa-beat redis
    Write-Success "Ambiente iniciado!"
    Write-Host ""
    Write-Info "Frontend: http://localhost:5173"
    Write-Info "API:      http://localhost:8001"
    Write-Info "API Docs: http://localhost:8001/docs"
}

function Start-DevMongo {
    Write-Header "Iniciando com MongoDB Local"
    Test-DockerRunning
    docker compose --profile with-mongodb up -d
    Write-Success "Ambiente com MongoDB iniciado!"
    Write-Host ""
    Write-Info "Frontend: http://localhost:5173"
    Write-Info "API:      http://localhost:8001"
    Write-Info "MongoDB:  localhost:27017"
}

function Start-DevFull {
    Write-Header "Iniciando Ambiente Completo"
    Test-DockerRunning
    docker compose --profile with-mongodb --profile monitoring up -d
    Write-Success "Ambiente completo iniciado!"
    Write-Host ""
    Write-Info "Frontend: http://localhost:5173"
    Write-Info "API:      http://localhost:8001"
    Write-Info "MongoDB:  localhost:27017"
    Write-Info "Flower:   http://localhost:5555"
}

function Start-Prod {
    Write-Header "Iniciando Producao"
    Test-DockerRunning
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    Write-Success "Producao iniciada!"
}

function Stop-All {
    Write-Header "Parando Containers"
    docker compose --profile with-mongodb --profile monitoring down
    Write-Success "Containers parados!"
}

function Restart-All {
    Write-Header "Reiniciando"
    docker compose restart
    Write-Success "Reiniciado!"
}

function Show-Logs {
    docker compose logs -f
}

function Show-LogsApi {
    docker compose logs -f api
}

function Show-LogsRpa {
    docker compose logs -f rpa-worker rpa-beat
}

function Show-LogsFrontend {
    docker compose logs -f frontend
}

function Clean-All {
    Write-Header "Limpando Tudo"
    docker compose --profile with-mongodb --profile monitoring down -v --remove-orphans
    Write-Success "Limpo!"
}

function Build-Images {
    Write-Header "Construindo Imagens"
    Test-DockerRunning
    docker compose build
    Write-Success "Imagens construidas!"
}

function Test-Health {
    Write-Header "Verificando Saude"

    Write-Host "Frontend..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5 | Out-Null
        Write-Success "Frontend OK"
    } catch {
        Write-Host "[ERRO] Frontend nao respondeu" -ForegroundColor Red
    }

    Write-Host "API..." -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5
        Write-Success "API OK"
    } catch {
        Write-Host "[ERRO] API nao respondeu" -ForegroundColor Red
    }

    Write-Host "Redis..." -ForegroundColor Yellow
    try {
        $result = docker compose exec -T redis redis-cli ping 2>$null
        if ($result -eq "PONG") {
            Write-Success "Redis OK"
        }
    } catch {
        Write-Host "[ERRO] Redis nao respondeu" -ForegroundColor Red
    }
}

# Main
switch ($Command) {
    "dev" { Start-Dev }
    "dev-mongo" { Start-DevMongo }
    "dev-full" { Start-DevFull }
    "prod" { Start-Prod }
    "stop" { Stop-All }
    "restart" { Restart-All }
    "logs" { Show-Logs }
    "logs-api" { Show-LogsApi }
    "logs-rpa" { Show-LogsRpa }
    "logs-frontend" { Show-LogsFrontend }
    "clean" { Clean-All }
    "build" { Build-Images }
    "health" { Test-Health }
    default { Show-Help }
}
