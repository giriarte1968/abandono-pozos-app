# WSL2 Installation Script for Podman
# Run this script as Administrator

Write-Host "=== Installing WSL2 for Podman ===" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Right-click on PowerShell" -ForegroundColor Yellow
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "3. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Installing WSL2..." -ForegroundColor Cyan
wsl --install

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! WSL2 installation initiated." -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT - Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Restart your computer NOW" -ForegroundColor Yellow
    Write-Host "2. After restart, Ubuntu will install automatically" -ForegroundColor Yellow
    Write-Host "3. Create a username and password when prompted" -ForegroundColor Yellow
    Write-Host "4. Then run: podman machine init" -ForegroundColor Yellow
    Write-Host ""
    
    $restart = Read-Host "Do you want to restart now? (Y/N)"
    if ($restart -eq 'Y' -or $restart -eq 'y') {
        Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Restart-Computer -Force
    }
} else {
    Write-Host ""
    Write-Host "ERROR: WSL installation failed." -ForegroundColor Red
    Write-Host "Error code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try this manual command as Administrator:" -ForegroundColor Yellow
    Write-Host "  wsl --install" -ForegroundColor Cyan
    Write-Host ""
}

Read-Host "Press Enter to exit"
