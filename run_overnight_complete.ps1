# NORMATTIVA OVERNIGHT COMPLETE SCRAPING
# ==========================================
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host " NORMATTIVA OVERNIGHT COMPLETE SCRAPING" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will download ALL normattiva documents" -ForegroundColor White
Write-Host "from 2020 to 2025 (6 years of complete data)" -ForegroundColor White
Write-Host ""
Write-Host "WARNINGS:" -ForegroundColor Red
Write-Host "- This process takes SEVERAL HOURS" -ForegroundColor Red
Write-Host "- It will download THOUSANDS of documents" -ForegroundColor Red
Write-Host "- Designed for overnight execution" -ForegroundColor Red
Write-Host ""

$confirmation = Read-Host "Are you sure you want to continue? (y/N)"
if ($confirmation -notmatch '^[Yy]$') {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Starting overnight complete scraping..." -ForegroundColor Green
"$(Get-Date) - Starting overnight complete scraping" | Out-File -FilePath "overnight_log.txt" -Append

# Run the Python script
python populate_multi_year.py

"$(Get-Date) - Overnight complete scraping finished" | Out-File -FilePath "overnight_log.txt" -Append

Write-Host ""
Write-Host "Process completed! Check overnight_log.txt for details." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
