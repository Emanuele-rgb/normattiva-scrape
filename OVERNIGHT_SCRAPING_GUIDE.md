# 🌙 NORMATTIVA OVERNIGHT COMPLETE SCRAPING GUIDE

## Overview

This guide helps you download ALL normattiva documents from 2020 to 2025 in a comprehensive overnight process.

## ⚠️ IMPORTANT WARNINGS

- **Duration**: This process takes **SEVERAL HOURS** (designed for overnight execution)
- **Data Volume**: Will download **THOUSANDS** of documents
- **Disk Space**: Ensure you have sufficient disk space (several GB)
- **Network**: Stable internet connection required

## 🚀 Quick Start (Recommended)

### Option 1: PowerShell (Recommended for Windows)

```powershell
.\run_overnight_complete.ps1
```

### Option 2: Batch File

```cmd
run_overnight_complete.bat
```

### Option 3: Python Direct

```bash
python populate_multi_year.py
```

## 📋 What Will Be Downloaded

The script will process:

- **2020**: ALL available documents
- **2021**: ALL available documents
- **2022**: ALL available documents
- **2023**: ALL available documents
- **2024**: ALL available documents
- **2025**: ALL available documents (current year)

## 🔧 Configuration

### Years to Process

The script is configured to download from 2020-2025. To modify years, edit `populate_multi_year.py`:

```python
years_config = {
    2025: -1,  # -1 means ALL documents
    2024: -1,
    2023: -1,
    2022: -1,
    2021: -1,
    2020: -1,
}
```

### Limiting Documents (for testing)

If you want to test with fewer documents first:

```python
years_config = {
    2024: 50,  # Only 50 documents for testing
    2023: 30,
}
```

## 📊 Monitoring Progress

### Real-time Monitoring

Open a new terminal and run:

```bash
python monitor_overnight.py
```

This will show:

- Current document count
- Documents per year
- Recent activity
- Processing rate

### Log Files

The process creates detailed log files:

- `multi_year_population_YYYYMMDD_HHMMSS.log` - Main process log
- `overnight_log.txt` - Simple start/stop log

## 🛠️ Database Management

### Before Starting

```bash
# Check current database status
python check_status.py

# Clear database (recommended for fresh start)
python clear_database.py
```

### During Process

```bash
# Monitor progress
python monitor_overnight.py

# Check database stats
python check_status.py
```

## 🎯 Individual Year Processing

If you need to process specific years individually:

```bash
# Process all documents for 2024
python scraper_optimized.py 2024

# Process specific number of documents for 2023
python scraper_optimized.py 2023 100
```

## 🔄 Resume Failed Years

If some years fail, you can retry them individually:

```bash
# The script will show failed years like this:
# ❌ Failed to process 2 years: [2021, 2022]
# Then retry manually:
python scraper_optimized.py 2021
python scraper_optimized.py 2022
```

## 🚨 Error Handling

### Common Issues and Solutions

**Database Locked Error**:

```bash
# Close any database connections and retry
python clear_database.py
python populate_multi_year.py
```

**Network Timeout**:

- The script has 4-hour timeout per year
- Failed years can be retried individually
- Check your internet connection

**Disk Space**:

- Monitor disk space during process
- Each year can generate 100MB+ of data

**Memory Issues**:

- Process runs year by year to minimize memory usage
- Restart if memory issues occur

## 📈 After Completion

### 1. Verify Results

```bash
# Check final statistics
python check_status.py

# Show completion summary
python monitor_overnight.py summary
```

### 2. AI Enhancement (Optional)

```bash
# Add AI features (embeddings, classifications, etc.)
python legal_ai_enhancer.py
```

### 3. Data Analysis

Your database will contain:

- **documenti_normativi**: Complete document metadata
- **articoli**: Individual articles with full text
- **citazioni_normative**: Legal citations
- **categorie_documenti**: Document categorizations

## 🔍 Expected Results

After completion, you should have:

- **~10,000-50,000+ documents** (depending on year coverage)
- **~100,000+ articles** extracted
- **Complete legal database** ready for analysis
- **Structured data** for AI/ML applications

## 💡 Performance Tips

### Optimal Conditions

- Run during off-peak hours (overnight)
- Ensure stable internet connection
- Close unnecessary applications
- Monitor disk space

### Troubleshooting

- Check log files for detailed error information
- Monitor system resources
- Retry failed years individually
- Use smaller batches for testing

## 📞 Support

If you encounter issues:

1. Check the log files first
2. Verify database integrity with `check_status.py`
3. Try processing individual years
4. Clear database and restart if needed

## 🎉 Success Indicators

Process completed successfully when you see:

- ✅ All years processed successfully
- 📊 Final statistics showing document counts
- 🎯 Fonte origine population completed
- 📄 Database contains expected number of documents

Remember: This is a comprehensive data collection process designed for overnight execution. Plan accordingly and ensure your system is ready for extended operation.
