<#
.SYNOPSIS
    Docker management script for Disaster Relief API
.DESCRIPTION
    Helper commands to build, start, stop, and manage the dockerized stack.
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("up","down","restart","logs","ps","shell","db-shell","clean","rebuild")]
    [string]$Command = "up"
)

switch ($Command) {
    "up" {
        Write-Host "Starting all services..." -ForegroundColor Green
        docker-compose --env-file .env.docker up --build -d
        Write-Host ""
        Write-Host "Services started!" -ForegroundColor Green
        Write-Host "  API:     http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  Docs:    http://localhost:8000/api/docs" -ForegroundColor Cyan
        Write-Host "  Adminer: http://localhost:8080" -ForegroundColor Cyan
        Write-Host "  Health:  http://localhost:8000/health" -ForegroundColor Cyan
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker-compose down
    }
    "restart" {
        docker-compose down
        docker-compose --env-file .env.docker up --build -d
    }
    "logs" {
        docker-compose logs -f backend
    }
    "ps" {
        docker-compose ps
    }
    "shell" {
        docker exec -it disaster_relief_backend /bin/bash
    }
    "db-shell" {
        Write-Host "Connecting to MySQL (password: relief_pass)..." -ForegroundColor Yellow
        docker exec -it disaster_relief_db mysql -u relief_user -prelief_pass disaster_relief
    }
    "clean" {
        Write-Host "Stopping and removing containers + volumes..." -ForegroundColor Red
        docker-compose down -v --remove-orphans
        docker volume rm $(docker volume ls -q -f name=disaster) 2>$null
    }
    "rebuild" {
        docker-compose down
        docker-compose --env-file .env.docker build --no-cache
        docker-compose --env-file .env.docker up -d
    }
}
