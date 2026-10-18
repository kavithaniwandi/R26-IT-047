#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Enables WSL 2 and Virtual Machine Platform — required for Docker Desktop.
    RUN THIS SCRIPT AS ADMINISTRATOR.
.NOTES
    After running, restart your PC, then start Docker Desktop.
#>

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Docker Prerequisites Setup (Run as Admin)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Enable Virtual Machine Platform
Write-Host "`n[1/3] Enabling Virtual Machine Platform..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
Write-Host "     Done." -ForegroundColor Green

# Step 2: Enable WSL feature
Write-Host "`n[2/3] Enabling Windows Subsystem for Linux..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
Write-Host "     Done." -ForegroundColor Green

# Step 3: Download and install WSL 2 kernel update
Write-Host "`n[3/3] Downloading WSL 2 Linux Kernel..." -ForegroundColor Yellow
$kernelUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$kernelMsi = "$env:TEMP\wsl_update_x64.msi"
Invoke-WebRequest -Uri $kernelUrl -OutFile $kernelMsi -UseBasicParsing
Start-Process msiexec.exe -ArgumentList "/i $kernelMsi /quiet /norestart" -Wait
Write-Host "     Done." -ForegroundColor Green

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host " SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host " NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. RESTART your computer" -ForegroundColor White
Write-Host "  2. After restart, open Docker Desktop from Start Menu" -ForegroundColor White
Write-Host "  3. In Docker Desktop: Settings > General > Use WSL 2 backend (check it)" -ForegroundColor White
Write-Host "  4. Then run in this project folder:" -ForegroundColor White
Write-Host "     docker-compose --env-file .env.docker up --build -d" -ForegroundColor Cyan
Write-Host ""
Write-Host " Or use the helper script:" -ForegroundColor Yellow
Write-Host "     .\docker-start.ps1 up" -ForegroundColor Cyan
