# scripts/test_rf2_ingest.ps1
Write-Host "Running RF2 Ingestion Dress Rehearsal Test..." -ForegroundColor Cyan
uv run pytest -v tests/test_rf2_rehearsal.py
