# Script de Setup Rápido para GitHub
# Execute este script para configurar o repositório Git local

Write-Host "🚀 Configurando repositório Git para GitHub Actions..." -ForegroundColor Green
Write-Host ""

# Verificar se já existe um repositório Git
if (Test-Path ".git") {
    Write-Host "✅ Repositório Git já existe" -ForegroundColor Yellow
} else {
    Write-Host "📦 Inicializando repositório Git..." -ForegroundColor Cyan
    git init
    Write-Host "✅ Repositório inicializado" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Arquivos criados:" -ForegroundColor Cyan
Write-Host "  ✓ requirements.txt"
Write-Host "  ✓ .github/workflows/scraper.yml"
Write-Host "  ✓ .gitignore"
Write-Host "  ✓ README_GITHUB_ACTIONS.md"

Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Crie um repositório no GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Execute os seguintes comandos:" -ForegroundColor White
Write-Host ""
Write-Host "   git add ." -ForegroundColor Green
Write-Host "   git commit -m '🚀 Configuração inicial do scraper com GitHub Actions'" -ForegroundColor Green
Write-Host "   git remote add origin https://github.com/SEU_USUARIO/NOME_REPO.git" -ForegroundColor Green
Write-Host "   git branch -M main" -ForegroundColor Green
Write-Host "   git push -u origin main" -ForegroundColor Green
Write-Host ""
Write-Host "3. Configure as permissões no GitHub:" -ForegroundColor White
Write-Host "   Settings → Actions → General → Workflow permissions" -ForegroundColor Cyan
Write-Host "   Marque: 'Read and write permissions'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Teste a execução manual:" -ForegroundColor White
Write-Host "   Actions → Scraper Pavão → Run workflow" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Leia o README_GITHUB_ACTIONS.md para mais detalhes!" -ForegroundColor Yellow
Write-Host ""
