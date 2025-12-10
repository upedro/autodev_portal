# =============================================================================
# RPA FluxLaw - Deploy Script (PowerShell)
# =============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod", "dev-mongo", "dev-monitor", "dev-full", "dev-portal", "prod-full", "prod-portal", "stop", "restart", "logs", "clean", "build", "health")]
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

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERRO] $Message" -ForegroundColor Red
}

function Show-Help {
    Write-Header "RPA FluxLaw - Comandos Disponiveis"
    Write-Host "  DESENVOLVIMENTO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 dev          - Inicia ambiente de desenvolvimento"
    Write-Host "    .\deploy.ps1 dev-mongo    - Inicia com MongoDB local"
    Write-Host "    .\deploy.ps1 dev-monitor  - Inicia com Flower (monitoramento)"
    Write-Host "    .\deploy.ps1 dev-portal   - Inicia com integracao Portal Web"
    Write-Host "    .\deploy.ps1 dev-full     - Inicia ambiente completo (todos os profiles)"
    Write-Host ""
    Write-Host "  PRODUCAO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 prod         - Inicia ambiente de producao"
    Write-Host "    .\deploy.ps1 prod-portal  - Producao + Portal Web"
    Write-Host "    .\deploy.ps1 prod-full    - Producao + MongoDB + Flower + Portal"
    Write-Host ""
    Write-Host "  GERENCIAMENTO:" -ForegroundColor Yellow
    Write-Host "    .\deploy.ps1 build        - Constroi as imagens Docker"
    Write-Host "    .\deploy.ps1 stop         - Para os containers"
    Write-Host "    .\deploy.ps1 restart      - Reinicia os containers"
    Write-Host "    .\deploy.ps1 logs         - Mostra logs"
    Write-Host "    .\deploy.ps1 clean        - Remove containers e volumes"
    Write-Host "    .\deploy.ps1 health       - Verifica saude dos servicos"
    Write-Host ""
}

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $true
    } catch {
        Write-Error-Message "Docker nao esta rodando. Por favor, inicie o Docker Desktop."
        exit 1
    }
}

function Start-Dev {
    Write-Header "Iniciando Ambiente de Desenvolvimento"
    Test-DockerRunning
    docker compose up -d api worker beat redis
    Write-Success "Ambiente de desenvolvimento iniciado!"
    Write-Info "API: http://localhost:8000"
    Write-Info "Docs: http://localhost:8000/docs"
}

function Start-DevMongo {
    Write-Header "Iniciando com MongoDB Local"
    Test-DockerRunning
    docker compose --profile with-mongodb up -d
    Write-Success "Ambiente com MongoDB local iniciado!"
    Write-Info "API: http://localhost:8000"
    Write-Info "MongoDB: localhost:27017"
}

function Start-DevMonitor {
    Write-Header "Iniciando com Monitoramento"
    Test-DockerRunning
    docker compose --profile monitoring up -d
    Write-Success "Ambiente com monitoramento iniciado!"
    Write-Info "API: http://localhost:8000"
    Write-Info "Flower: http://localhost:5555"
}

function Start-DevPortal {
    Write-Header "Iniciando com Integracao Portal Web"
    Test-DockerRunning
    docker compose --profile portal up -d
    Write-Success "Ambiente com Portal iniciado!"
    Write-Info "API: http://localhost:8000"
    Write-Info "Portal Worker: ativo (processa tasks do portal_rpa)"
    Write-Info "Portal Beat: a cada 5 min verifica novas solicitacoes"
}

function Start-DevFull {
    Write-Header "Iniciando Ambiente Completo"
    Test-DockerRunning
    docker compose --profile with-mongodb --profile monitoring --profile portal up -d
    Write-Success "Ambiente completo iniciado!"
    Write-Info "API: http://localhost:8000"
    Write-Info "MongoDB: localhost:27017"
    Write-Info "Flower: http://localhost:5555"
    Write-Info "Portal Worker: ativo"
}

function Start-Prod {
    Write-Header "Iniciando Ambiente de Producao"
    Test-DockerRunning
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d api worker beat redis
    Write-Success "Ambiente de producao iniciado!"
}

function Start-ProdPortal {
    Write-Header "Iniciando Producao com Portal"
    Test-DockerRunning
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile portal up -d
    Write-Success "Ambiente de producao com Portal iniciado!"
    Write-Info "Portal Worker: ativo"
}

function Start-ProdFull {
    Write-Header "Iniciando Producao Completa"
    Test-DockerRunning
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile with-mongodb --profile monitoring --profile portal up -d
    Write-Success "Ambiente de producao completo iniciado!"
}

function Stop-All {
    Write-Header "Parando Containers"
    docker compose --profile with-mongodb --profile monitoring --profile portal down
    Write-Success "Containers parados!"
}

function Restart-All {
    Write-Header "Reiniciando Containers"
    docker compose restart
    Write-Success "Containers reiniciados!"
}

function Show-Logs {
    Write-Header "Logs dos Servicos"
    docker compose logs -f
}

function Clean-All {
    Write-Header "Limpando Containers e Volumes"
    docker compose --profile with-mongodb --profile monitoring --profile portal down -v --remove-orphans
    Write-Success "Containers e volumes removidos!"
}

function Build-Images {
    Write-Header "Construindo Imagens Docker"
    Test-DockerRunning
    docker compose build
    Write-Success "Imagens construidas!"
}

function Test-Health {
    Write-Header "Verificando Saude dos Servicos"

    Write-Host "Testando API..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
        Write-Success "API: $($response.status)"
    } catch {
        Write-Error-Message "API nao respondeu"
    }

    Write-Host "Testando Redis..." -ForegroundColor Yellow
    try {
        $result = docker compose exec -T redis redis-cli ping 2>$null
        if ($result -eq "PONG") {
            Write-Success "Redis: OK"
        }
    } catch {
        Write-Error-Message "Redis nao respondeu"
    }
}

# Main execution
switch ($Command) {
    "dev" { Start-Dev }
    "dev-mongo" { Start-DevMongo }
    "dev-monitor" { Start-DevMonitor }
    "dev-portal" { Start-DevPortal }
    "dev-full" { Start-DevFull }
    "prod" { Start-Prod }
    "prod-portal" { Start-ProdPortal }
    "prod-full" { Start-ProdFull }
    "stop" { Stop-All }
    "restart" { Restart-All }
    "logs" { Show-Logs }
    "clean" { Clean-All }
    "build" { Build-Images }
    "health" { Test-Health }
    default { Show-Help }
}
