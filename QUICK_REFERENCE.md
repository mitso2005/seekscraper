# Quick Reference Guide

## Project Overview
Modular Seek web scraper for ICT jobs in Melbourne with parallel processing capabilities.

## File Structure
```
seek-webscraper/
├── main.py                    # Entry point (92 lines)
├── requirements.txt           # Dependencies
├── README.md                  # User documentation
├── ARCHITECTURE.md            # Architecture diagrams
├── REFACTORING_SUMMARY.md     # Refactoring details
├── BEFORE_AFTER.md            # Comparison
├── IMPORTS.md                 # Import structure
└── scraper/                   # Main package
    ├── config.py              # Constants & settings
    ├── driver_setup.py        # WebDriver initialization
    ├── url_builder.py         # URL construction
    ├── extractors.py          # Contact extraction
    ├── page_parser.py         # Page parsing
    ├── job_scraper.py         # Job details scraping
    ├── parallel_scraper.py    # Parallel execution
    ├── link_collector.py      # Link collection
    ├── user_input.py          # User prompts
    └── data_export.py         # Excel export
```

## Usage
```bash
python main.py
```

## Configuration (scraper/config.py)
```python
# Search settings
CLASSIFICATION = "information-communication-technology"
LOCATION = "All-Melbourne-VIC"
BASE_URL = "https://www.seek.com.au"

# Performance
DEFAULT_WORKERS = 5
MAX_WORKERS = 10
CHECKPOINT_INTERVAL = 100

# Timeouts (seconds)
PAGE_LOAD_TIMEOUT = 2
ELEMENT_WAIT_TIMEOUT = 2
```

## Module Quick Reference

### config.py
**Purpose**: Centralized configuration  
**Exports**: Constants, timeouts, column names  
**Dependencies**: None

### driver_setup.py
**Purpose**: WebDriver initialization  
**Key Functions**:
- `setup_driver(headless=False)` - Create Chrome driver
- `create_chrome_options(headless)` - Configure Chrome options  
**Dependencies**: selenium, config

### url_builder.py
**Purpose**: Search URL construction  
**Key Functions**:
- `build_search_url(sort_by_date=False)` - Build Seek URL  
**Dependencies**: config

### extractors.py
**Purpose**: Contact information extraction  
**Key Functions**:
- `extract_email(text)` - Extract email addresses
- `extract_phone(text)` - Extract Australian phone numbers
- `extract_website(text)` - Extract website URLs
- `extract_contact_info(text)` - Extract all contact info  
**Dependencies**: re, config

### page_parser.py
**Purpose**: Page DOM parsing  
**Key Functions**:
- `get_total_jobs(driver)` - Get job count
- `get_job_links_on_page(driver)` - Extract job URLs
- `click_next_page(driver)` - Navigate to next page  
**Dependencies**: selenium, config

### job_scraper.py
**Purpose**: Individual job detail extraction  
**Key Functions**:
- `scrape_job_details(driver, job_url)` - Scrape all job fields
- `create_empty_job_data(job_url)` - Empty job dict
- `extract_job_title(driver)` - Extract title
- `extract_company(driver)` - Extract company
- `extract_salary(driver)` - Extract salary
- (+ 8 more field extractors)  
**Dependencies**: selenium, config, extractors

### parallel_scraper.py
**Purpose**: Multi-threaded execution  
**Key Functions**:
- `scrape_jobs_in_parallel(urls, start, workers, filename)` - Main parallel function
- `scrape_job_parallel(url, num, total, headless)` - Single job in thread
- `save_checkpoint(data, filename)` - Save progress  
**Dependencies**: concurrent.futures, pandas, driver_setup, job_scraper, config

### link_collector.py
**Purpose**: Job link collection  
**Key Functions**:
- `collect_job_links(driver, end_job)` - Collect links from pages
- `filter_job_range(links, start, end)` - Filter to range  
**Dependencies**: page_parser, config

### user_input.py
**Purpose**: User interaction  
**Key Functions**:
- `get_sort_preference()` - Ask about sorting
- `get_parallel_workers()` - Ask about worker count
- `get_job_range(total_jobs)` - Ask about job range  
**Dependencies**: config

### data_export.py
**Purpose**: Excel export and statistics  
**Key Functions**:
- `create_filename(interrupted, error)` - Generate filename
- `save_to_excel(data, filename)` - Save DataFrame
- `print_statistics(df, filename)` - Print stats
- `save_partial_data(data, interrupted)` - Save on error  
**Dependencies**: pandas, datetime, config

## Common Tasks

### Change Search Criteria
Edit `scraper/config.py`:
```python
CLASSIFICATION = "your-classification"
LOCATION = "your-location"
```

### Adjust Performance
Edit `scraper/config.py`:
```python
DEFAULT_WORKERS = 5        # Number of parallel browsers
PAGE_LOAD_TIMEOUT = 2      # Wait time for page load
CHECKPOINT_INTERVAL = 100  # Save frequency
```

### Add New Data Field
1. Add to `config.py` COLUMNS list
2. Add extractor to `extractors.py` (if needed)
3. Update `job_scraper.py` scrape_job_details()

### Debug Issues
1. Set workers to 1: `parallel_input = "1"`
2. Check screenshots: `debug_screenshot.png`
3. Add print statements in relevant module
4. Check error messages for module name

### Run Tests (Future)
```python
# Unit test example
from scraper.extractors import extract_email

def test_extract_email():
    assert extract_email("Contact: test@example.com") == "test@example.com"
```

## Typical Workflow

```
User runs main.py
    │
    ├─► Get preferences (user_input)
    │   ├─► Sort by date? (y/n)
    │   ├─► How many workers? (1-10)
    │   └─► Job range? (1-100, all)
    │
    ├─► Setup (driver_setup, url_builder)
    │   ├─► Create driver
    │   └─► Build search URL
    │
    ├─► Collect links (link_collector, page_parser)
    │   ├─► Get total jobs
    │   ├─► Collect job URLs
    │   └─► Filter to range
    │
    ├─► Scrape jobs (parallel_scraper, job_scraper)
    │   ├─► Create thread pool
    │   ├─► Scrape in parallel
    │   └─► Save checkpoints
    │
    └─► Export (data_export)
        ├─► Save to Excel
        └─► Print statistics
```

## Performance Tips

1. **More workers = faster** (up to 10)
2. **Checkpoints save progress** (every 100 jobs)
3. **Images/CSS disabled** (faster loading)
4. **Headless mode** (lower resource usage)
5. **Short timeouts** (2s page load)

## Troubleshooting

| Issue | Module | Solution |
|-------|--------|----------|
| Can't find jobs | page_parser | Check selectors in get_total_jobs() |
| Contact info wrong | extractors | Adjust regex patterns |
| Scraping too slow | config | Increase workers in config.py |
| Browser crashes | driver_setup | Check Chrome options |
| Excel errors | data_export | Check pandas/openpyxl versions |
| Import errors | __init__.py | Ensure scraper/ is a package |

## Key Metrics

- **Main file**: 92 lines (was 677)
- **Modules**: 11 focused files
- **Avg module**: ~70 lines
- **Max module**: 156 lines (job_scraper)
- **Test coverage**: Ready for unit tests
- **Maintainability**: High
- **Extensibility**: High

## Next Steps

1. ✅ Refactoring complete
2. ⬜ Add unit tests
3. ⬜ Add type hints
4. ⬜ Add logging
5. ⬜ Create CLI interface
6. ⬜ Add configuration file

## Resources

- **ARCHITECTURE.md** - Detailed architecture diagrams
- **REFACTORING_SUMMARY.md** - Complete refactoring details
- **BEFORE_AFTER.md** - Side-by-side comparison
- **IMPORTS.md** - Import structure and dependencies
- **README.md** - User documentation
