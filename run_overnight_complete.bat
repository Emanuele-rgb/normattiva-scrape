@echo off
echo ==========================================
echo  NORMATTIVA OVERNIGHT COMPLETE SCRAPING
echo ==========================================
echo.
echo This will download ALL normattiva documents
echo from 2020 to 2025 (6 years of complete data)
echo.
echo WARNINGS:
echo - This process takes SEVERAL HOURS
echo - It will download THOUSANDS of documents
echo - Designed for overnight execution
echo.
pause

echo Starting overnight complete scraping...
echo %date% %time% - Starting overnight complete scraping >> overnight_log.txt

python populate_multi_year.py

echo %date% %time% - Overnight complete scraping finished >> overnight_log.txt
echo.
echo Process completed! Check overnight_log.txt for details.
echo.
pause
