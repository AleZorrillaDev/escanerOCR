# Instalador automático de Poppler para Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalador de Poppler para Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si winget está disponible
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "✅ winget detectado, instalando Poppler..." -ForegroundColor Green
    winget install --id=sharkdp.poppler -e
} else {
    Write-Host "⚠️  winget no está disponible" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📥 Descarga manual de Poppler:" -ForegroundColor Cyan
    Write-Host "https://github.com/oschwartz10612/poppler-windows/releases/" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Pasos:" -ForegroundColor Cyan
    Write-Host "1. Descarga 'Release-XX.XX.X-0.zip'" -ForegroundColor White
    Write-Host "2. Extrae el archivo a C:\poppler" -ForegroundColor White
    Write-Host "3. Agrega al PATH: C:\poppler\Library\bin" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "¿Deseas abrir la página de descarga? (S/N)"
    if ($response -eq "S" -or $response -eq "s") {
        Start-Process "https://github.com/oschwartz10612/poppler-windows/releases/"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
