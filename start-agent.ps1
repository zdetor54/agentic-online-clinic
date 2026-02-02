# Quick Start Script for Agent Testing

Write-Host "Starting Agentic Online Clinic..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: uv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .venv\Scripts\Activate.ps1

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ".env file not found!" -ForegroundColor Red
    Write-Host "Create .env file with your Azure OpenAI credentials" -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env
Write-Host "Loading environment variables from .env..." -ForegroundColor Green
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim('"')
        Set-Item -Path "env:$name" -Value $value
    }
}

Write-Host ""
Write-Host "Environment configured!" -ForegroundColor Green
Write-Host "   - Azure OpenAI Endpoint: $env:AZURE_OPENAI_ENDPOINT" -ForegroundColor Gray
Write-Host "   - Deployment: $env:AZURE_OPENAI_DEPLOYMENT_NAME" -ForegroundColor Gray
Write-Host ""

# Instructions
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start FastAPI server:" -ForegroundColor White
Write-Host "   .venv\Scripts\python.exe -m uvicorn src.api.main:app --reload" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Start Streamlit UI:" -ForegroundColor White
Write-Host "   .venv\Scripts\streamlit.exe run ui/clinic.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Open http://localhost:8501 and click Agent Mode" -ForegroundColor White
Write-Host ""
Write-Host "Test prompts:" -ForegroundColor Cyan
Write-Host "   - Find patient John Doe" -ForegroundColor Gray
Write-Host "   - Create patient Jane Smith born 1990-05-15" -ForegroundColor Gray
Write-Host ""
