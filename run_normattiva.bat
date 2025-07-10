@echo off
echo 🏛️ NORMATTIVA DATABASE POPULATION MENU
echo =====================================
echo.
echo Choose an option:
echo.
echo 1. Test with small dataset (5 docs per year, 2020-2024)
echo 2. Full population (340 docs total, 2020-2024)
echo 3. Custom year (specify year and document count)
echo 4. Clear database
echo 5. Run Legal AI Enhancer (add AI features)
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo 🧪 Running test with small dataset...
    python test_multi_year.py
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo 🚀 Running full population...
    python populate_multi_year.py
    goto :end
)

if "%choice%"=="3" (
    echo.
    set /p year="Enter year (e.g., 2024): "
    set /p docs="Enter number of documents (e.g., 50): "
    echo.
    echo 🎯 Processing year %year% with %docs% documents...
    python scraper_optimized.py %year% %docs%
    goto :end
)

if "%choice%"=="4" (
    echo.
    echo 🧹 Clearing database...
    python clear_database.py
    goto :end
)

if "%choice%"=="5" (
    echo.
    echo 🤖 Running Legal AI Enhancer...
    python legal_ai_enhancer.py
    goto :end
)

if "%choice%"=="6" (
    echo.
    echo 👋 Goodbye!
    goto :end
)

echo.
echo ❌ Invalid choice. Please try again.
pause

:end
echo.
echo ✅ Operation completed!
pause
