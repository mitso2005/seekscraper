# Seek Web Scraper - ICT Jobs Melbourne

## Overview

Automated web scraper for collecting ICT job listings from Seek.com.au (Melbourne area). Extracts job details and contact information, exports to Excel.

## Project Structure

```
seek-webscraper/
├── scraper/           # Core scraping engine modules
├── data/              # Output Excel files
├── cache/             # Phone cache and progress files
├── scripts/           # Standalone scraping scripts
├── main.py            # Main entry point
└── requirements.txt   # Python dependencies
```

## Features

- Scrapes 12 data fields per job: title, company, location, classification, work type, salary, time posted, email, phone, office phone, website, URL
- Filters recruitment agencies, contract/temp roles, and large companies (1000+ employees)
- Google Business phone number enrichment (optional)
- Parallel processing with configurable worker count (1-20 browsers)
- Checkpoint-based resume capability
- Two search modes: job-based range or page-based range

## Requirements

- Python 3.7+
- Selenium WebDriver
- Chrome/ChromeDriver (managed by webdriver-manager)
- Pandas & OpenPyXL

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Configuration prompts:
1. Sort by date (y/n)
2. Parallel browser count (1-20, recommended: 12)
3. Streaming mode (y/n)
4. Search range: `1-100`, `page:15-50`, or `all`

## Technical Details

- Headless Chrome via Selenium
- Multi-threaded scraping (ThreadPoolExecutor)
- Automatic checkpoint saves every 50 jobs
- Persistent phone number cache (JSON)
- Rate limit handling with quota detection

## Limitations

- Recent jobs (1-540): use job number range
- Older jobs (540+): use page number range
- Maximum practical limit: ~540 jobs or ~25 pages
- Rate limiting may cause incomplete results beyond these thresholds

## Disclaimer

For educational and research purposes only. Ignores robots.txt. Review Seek's Terms of Service before use.
