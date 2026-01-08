# Setup pre-commit hooks for AutoLock integration (PowerShell)

Write-Host "Setting up pre-commit hooks..." -ForegroundColor Green

# Install pre-commit if not already installed
if (-not (Get-Command pre-commit -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pre-commit..." -ForegroundColor Yellow
    pip install pre-commit
}

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

Write-Host "Pre-commit hooks installed successfully!" -ForegroundColor Green
Write-Host "Hooks will now run automatically on git commit." -ForegroundColor Green

