# NORMATTIVA DATABASE POPULATION MENU
# PowerShell version

function Show-Menu {
    Clear-Host
    Write-Host "🏛️ NORMATTIVA DATABASE POPULATION MENU" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Choose an option:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. Test with small dataset (5 docs per year, 2020-2024)" -ForegroundColor Green
    Write-Host "2. Full population (340 docs total, 2020-2024)" -ForegroundColor Yellow
    Write-Host "3. Custom year (specify year and document count)" -ForegroundColor Blue
    Write-Host "4. Clear database" -ForegroundColor Red
    Write-Host "5. Run Legal AI Enhancer (add AI features)" -ForegroundColor Magenta
    Write-Host "6. Exit" -ForegroundColor Gray
    Write-Host ""
}

function Test-SmallDataset {
    Write-Host "🧪 Running test with small dataset..." -ForegroundColor Green
    python test_multi_year.py
}

function Run-FullPopulation {
    Write-Host "🚀 Running full population..." -ForegroundColor Yellow
    python populate_multi_year.py
}

function Run-CustomYear {
    $year = Read-Host "Enter year (e.g., 2024)"
    $docs = Read-Host "Enter number of documents (e.g., 50)"
    
    Write-Host "🎯 Processing year $year with $docs documents..." -ForegroundColor Blue
    python scraper_optimized.py $year $docs
}

function Clear-Database {
    Write-Host "🧹 Clearing database..." -ForegroundColor Red
    python clear_database.py
}

function Run-AIEnhancer {
    Write-Host "🤖 Running Legal AI Enhancer..." -ForegroundColor Magenta
    python legal_ai_enhancer.py
}

# Main menu loop
do {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-6)"
    
    switch ($choice) {
        '1' {
            Test-SmallDataset
            break
        }
        '2' {
            Run-FullPopulation
            break
        }
        '3' {
            Run-CustomYear
            break
        }
        '4' {
            Clear-Database
            break
        }
        '5' {
            Run-AIEnhancer
            break
        }
        '6' {
            Write-Host "👋 Goodbye!" -ForegroundColor Gray
            exit
        }
        default {
            Write-Host "❌ Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Host ""
    Write-Host "✅ Operation completed!" -ForegroundColor Green
    Read-Host "Press Enter to continue"
    
} while ($choice -ne '6')
