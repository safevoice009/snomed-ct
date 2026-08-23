# scripts/run_eval.ps1
Write-Host "Running SICCE Clinical Evaluation Harness..." -ForegroundColor Cyan
uv run python eval/run_eval.py
