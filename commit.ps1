# Helper script to commit with pre-commit hooks (PowerShell)
# This runs pre-commit first, stages any changes, then shows status

Write-Host "Running pre-commit hooks..." -ForegroundColor Yellow
pre-commit run --all-files

Write-Host "Staging changes made by pre-commit..." -ForegroundColor Yellow
git add -A

# Check if there are staged changes
$staged = git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nChanges to be committed:" -ForegroundColor Green
    git diff --cached --stat
    Write-Host "`nReady to commit. Run: git commit -m 'Your message'" -ForegroundColor Cyan
} else {
    Write-Host "No changes to commit." -ForegroundColor Green
}
