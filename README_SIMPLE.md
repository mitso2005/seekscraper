# Seek Web Scraper - ICT Jobs Melbourne

## Purpose

This tool automatically collects Information & Communication Technology job postings from Seek.com.au for the Melbourne area. It extracts detailed job information including titles, companies, salaries, and contact details, then exports everything to an Excel spreadsheet.

Instead of manually clicking through hundreds of job listings, this scraper does it for you in minutes.

## What It Does

- Navigates to Seek.com.au and collects ICT job listings
- Extracts 12 data fields per job: title, company, location, classification, work type, salary, time posted, email, phone, office phone, website, and job URL
- Filters out recruitment agencies, contract/temp roles, and large companies (1000+ employees)
- Enriches job data by looking up company phone numbers via Google Business
- Saves results to a timestamped Excel file
- Supports searching by job number range or page range
- Can resume from checkpoints if interrupted

## Technology Stack

- **Selenium WebDriver** - Controls a headless Chrome browser to navigate Seek
- **Python 3.7+** - Core programming language
- **Pandas & OpenPyXL** - Excel file generation and manipulation
- **Chrome/ChromeDriver** - Automated browser (managed by webdriver-manager)
- **Threading** - Parallel processing with up to 20 concurrent browsers for 4-8x faster scraping

## How to Use

1. Install dependencies: `pip install -r requirements.txt`
2. Run the scraper: `python main.py`
3. Choose preferences:
   - Sort by newest jobs first (y/n)
   - Number of parallel browsers (1-20, recommended: 12)
   - Streaming mode for faster startup (y/n)
4. Choose search range:
   - Job-based: `1-100` or `600-700`
   - Page-based: `page:15-50` or `page:25`
   - All jobs: `all`
5. Wait for results to save as Excel file

## Key Features

- **Parallel Processing** - Uses multiple browsers simultaneously for 4-8x faster scraping vs sequential
- **Checkpoint Saving** - Automatically saves every 50 jobs to prevent data loss
- **Two Search Modes** - Job-based for recent listings, page-based for historical data
- **Anti-Detection** - Mimics real browser behavior with disabled images/CSS and proper delays
- **Data Filtering** - Automatically removes recruitment companies, contract roles, and large corporates

## Current Limitations

Due to Seek.com.au rate limiting and Google restrictions, the following limitations exist:

- Searches for recent job listings (job numbers 1-540) should be done by job number range (e.g., `1-100`)
- Searches for older job listings (beyond job 540) should be done by page number range (e.g., `page:25-50`)
- Maximum practical search range is approximately 540 jobs or 25 pages
- Attempting to exceed these limits will result in incomplete data collection or rate limit blocks
- This is the primary constraint of the current implementation

## Educational Use Only

This scraper ignores robots.txt and is intended for learning and research purposes only. Please review Seek's Terms of Service before using this tool.
