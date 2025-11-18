# Seek Job Scraper - ICT Jobs Melbourne

## What This Does (Non-Technical Summary)

This automated tool visits Seek.com.au and collects detailed information from hundreds of technology job listings in Melbourne, saving everything to an Excel spreadsheet so you can easily review opportunities without manually clicking through each posting. It works like a smart assistant that reads job ads for you and organizes all the important details (titles, companies, salaries, contact info) in one convenient place.

## Overview

This Python-based web scraper uses Selenium to collect **Information & Communication Technology** job postings from [Seek](https://www.seek.com.au) in the **All Melbourne VIC** region. It extracts comprehensive job details including titles, company names, salaries, work arrangements, and contact information from each listing and exports the data to an Excel file with parallel processing for 4-8x faster performance.

> **⚠️ Educational Use Only:** This scraper ignores robots.txt and is intended for learning purposes only. Please respect Seek's terms of service and rate limits.

## Features

### Core Capabilities
- **Parallel Processing**: Use 1-10 concurrent browsers for 4-8x faster scraping (recommended: 5 workers)
- **Targeted Search**: Automatically searches ICT jobs in All Melbourne VIC
- **Full Pagination**: Scrapes all available job listings (supports 1750+ jobs)
- **Job Range Selection**: Choose specific ranges (e.g., "1-100", "33-233") or scrape all
- **Sort by Date**: Option to sort by newest jobs first

### Data Extraction (12 Fields)
- **Job Information**: Title, company, location, classification, work type
- **Compensation**: Salary ranges (both listed and predicted)
- **Timing**: Time posted, application volume indicators
- **Contact Details**: Email addresses, phone numbers, and websites from job descriptions
- **Job URL**: Direct link to each posting

### Performance & Reliability
- **Fast Execution**: 5 parallel browsers scrape 500 jobs in ~5-8 minutes (vs ~25-40 minutes sequentially)
- **Checkpoint Saving**: Automatic saves every 100 jobs to prevent data loss
- **Crash Recovery**: Graceful interrupt handling preserves partial data
- **Anti-Detection**: Built-in bot evasion with disabled images/CSS for faster loading
- **Excel Export**: Outputs to timestamped Excel file (.xlsx) with proper column ordering

## Installation

### Prerequisites

Ensure you have the following installed:

- **Python 3.7+** (Python 3.8+ recommended)
- **Google Chrome** (latest version)
- **ChromeDriver** (automatically managed by webdriver-manager)

### Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/mitso2005/seekscraper.git
   cd seekscraper
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

   This will install:
   - `selenium>=4.15.0` - Web automation framework
   - `webdriver-manager>=4.0.1` - Automatic ChromeDriver management
   - `pandas>=2.0.0` - Data manipulation and analysis
   - `openpyxl>=3.1.0` - Excel file writing
   - `python-dotenv>=1.0.0` - Environment variable management

## Usage

Run the scraper:

```sh
python main.py
```

### Interactive Prompts

The scraper will ask you:

1. **Sort by newest jobs first?** (y/n)
   - Choose 'y' to see recently posted jobs first
   - Choose 'n' for default relevance sorting

2. **How many parallel browsers?** (1-10, recommended: 5)
   - More browsers = faster scraping (5 workers ≈ 5x speed increase)
   - Use 1 worker for debugging or slower connections
   - Use 5-10 workers for maximum speed

3. **Which jobs to scrape?** (e.g., "1-100", "50-250", or "all")
   - Enter a range like "1-100" to scrape jobs 1 through 100
   - Enter "all" to scrape all available jobs
   - Useful for testing with smaller batches first

### Scraping Process

The scraper will:
1. Navigate to the ICT jobs search page for All Melbourne VIC
2. Display the total number of jobs available
3. Collect all job listing URLs from paginated results
4. Scrape detailed information using parallel browsers
5. Save checkpoints every 100 jobs automatically
6. Export all data to `seek_ict_jobs_melbourne_YYYYMMDD_HHMMSS.xlsx`

### Data Fields Extracted

The Excel file contains **12 columns**:
- `job_title` - Job position title
- `company` - Hiring company name
- `location` - Job location (suburb/area)
- `classification` - Job category/classification
- `work_type` - Full-time, Part-time, Contract, Casual
- `salary` - Salary range (if available, including predicted ranges)
- `time_posted` - When the job was posted (e.g., "Posted 2 days ago")
- `application_volume` - Application volume indicator (Low/Medium/High)
- `email` - Contact email (if found in job description)
- `phone` - Contact phone number (if found, Australian format)
- `website` - Company/contact website (if found)
- `url` - Direct link to the job posting

### Sample Output

```
============================================================
SEEK Web Scraper - ICT Jobs in All Melbourne VIC
============================================================

NOTE: This scraper is for educational purposes only.

Sort by newest jobs first? (y/n): y

How many parallel browsers? (1-10, recommended: 5): 5

⚡ Using 5 parallel browser(s) for faster scraping!

Initializing...

Navigating to: https://www.seek.com.au/information-communication-technology-jobs/in-All-Melbourne-VIC?sortmode=ListedDate

Waiting for page to load...

📊 Total ICT jobs available: 1750

Which jobs to scrape? (e.g., '1-100', '50-250', or 'all' for all 1750): 1-500
Will scrape jobs 1 to 500 (500 jobs)

Collecting job links from search results...
  Scraping page 1... (collected 0 links so far)
  Scraping page 2... (collected 22 links so far)
  ...
  Scraping page 23... (collected 506 links so far)
  Collected enough jobs to cover range (up to job 500).

Total job links collected: 506
Selected range: 500 jobs (from job 1 to job 500)

⚡ Scraping 500 jobs using 5 parallel browser(s)...
(Much faster with parallel processing!)

  ✓ [Job #1] Completed
  ✓ [Job #3] Completed
  ✓ [Job #2] Completed
  ...
  Progress: 100/500 jobs completed (20.0%)
  💾 Checkpoint saved: 100 jobs
  ...
  Progress: 500/500 jobs completed (100.0%)

============================================================
✅ SUCCESS! Data exported to: seek_ict_jobs_melbourne_20251118_143022.xlsx
Total jobs scraped: 500
Successfully extracted: 487
Failed to extract: 13
Jobs with email: 89
Jobs with phone: 143
Jobs with website: 267
============================================================
```

## Performance Metrics

| Workers | Jobs | Time | Speed |
|---------|------|------|-------|
| 1 (Sequential) | 500 | ~25-40 min | ~3-5 sec/job |
| 5 (Parallel) | 500 | ~8-12 min | ~1 sec/job |
| 10 (Parallel) | 500 | ~5-8 min | ~0.6 sec/job |

**Note**: Actual performance varies based on internet speed and Seek's response times.

## Project Structure

The scraper uses a **modular architecture** for maintainability and extensibility:

```
seek-webscraper/
├── main.py                      # Entry point and orchestration (92 lines)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture documentation
└── scraper/                     # Modular scraper package
    ├── config.py                # Configuration and constants
    ├── driver_setup.py          # WebDriver initialization
    ├── url_builder.py           # Search URL construction
    ├── extractors.py            # Contact info extraction (email, phone, website)
    ├── page_parser.py           # Page parsing (job count, links, pagination)
    ├── job_scraper.py           # Job details scraping (12 fields)
    ├── parallel_scraper.py      # Parallel execution logic
    ├── link_collector.py        # Job link collection
    ├── user_input.py            # User input handling
    └── data_export.py           # Excel export and statistics
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module documentation and design patterns.

## Customization

### Change Search Criteria

Edit `scraper/config.py` to modify search parameters:

```python
# Search configuration
CLASSIFICATION = "information-communication-technology"  # Change job category
LOCATION = "All-Melbourne-VIC"                          # Change location
BASE_URL = "https://www.seek.com.au"
```

### Adjust Performance Settings

Modify timeout and worker values in `scraper/config.py`:

```python
# Scraping settings
DEFAULT_WORKERS = 5          # Default number of parallel browsers
MAX_WORKERS = 10             # Maximum allowed workers
CHECKPOINT_INTERVAL = 100    # Save checkpoint every N jobs

# Timeout settings (in seconds)
PAGE_LOAD_TIMEOUT = 2        # Wait time for page load
ELEMENT_WAIT_TIMEOUT = 2     # Wait time for elements
```

## Troubleshooting

### Common Issues

**ChromeDriver Issues:**
- The script uses `webdriver-manager` to automatically download the correct ChromeDriver version
- If you encounter issues, ensure Google Chrome is up to date
- Try deleting the ChromeDriver cache: `~/.wdm/` (Linux/Mac) or `%USERPROFILE%\.wdm\` (Windows)

**No Jobs Found / Job Count is 0:**
- Check if Seek is accessible in your region
- Look at the saved screenshot: `debug_screenshot.png`
- Verify the search URL in `scraper/config.py` is correct
- Seek may have implemented CAPTCHA - try reducing workers to 1

**Timeout Errors:**
- Increase timeout values in `scraper/config.py`
- Reduce the number of parallel workers (try 1-3 instead of 5-10)
- Check your internet connection speed

**Browser Crashes or "Connection Refused" Errors:**
- Reduce the number of parallel workers
- The scraper automatically restarts browsers every 100 jobs
- Checkpoint saves prevent data loss

**No Contact Information Found:**
- Many job postings don't include direct contact info (this is normal)
- Empty fields are expected - recruiters often hide contact details
- Contact info is only extracted from job descriptions, not meta tags

**Interrupt Handling (Ctrl+C):**
- Press Ctrl+C to stop scraping gracefully
- Partial data is automatically saved to an Excel file
- Look for files named `seek_ict_jobs_melbourne_interrupted_*.xlsx`

### Debug Mode

To debug issues, run with 1 worker and check the output:
```sh
python main.py
# When prompted, enter: 1 (for workers)
```

Screenshots are saved automatically:
- `debug_screenshot.png` - When job count fails
- `debug_first_page.png` - When no links found on first page

## Important Notes

- **Speed**: With 5 parallel browsers, scraping 500 jobs takes ~5-8 minutes (vs ~25-40 minutes sequentially)
- **Headless Mode**: All browsers run in headless mode (no visible windows) for better performance
- **Progress Tracking**: Real-time progress updates show completion percentage
- **Checkpoint Saving**: Data is automatically saved every 100 jobs to prevent loss
- **Timestamped Files**: Each run creates a new Excel file with timestamp
- **Interrupt Safety**: Press Ctrl+C to stop gracefully - partial data is saved automatically
- **Anti-Detection**: Images and CSS are disabled for faster loading and bot evasion
- **Contact Info Accuracy**: Advanced regex filters prevent false positives from meta tags

## Future Enhancements

### Planned Features

- **AI Recruitment Detection**: Use AI to identify recruiting firms and suggest the potential companies they're hiring for
  - Example: "Robert Half" detected → suggest potential client companies based on job descriptions
  - Helps job seekers understand the actual employer behind recruitment agencies

- **AI Manager Identification**: Leverage AI to suggest potential hiring managers to contact for specific roles
  - Analyzes job descriptions and company information
  - Provides suggested contact details and outreach strategies
  - Helps with targeted networking and direct applications

### Potential Improvements

- **Resume Capability**: Continue scraping from where you left off using checkpoint files
- **Proxy Rotation**: Add proxy support for higher volume scraping
- **GUI Interface**: Desktop application with progress bars and configuration
- **CSV Export**: Additional export format option
- **Email Notifications**: Get notified when scraping completes
- **Job Filtering**: Filter by keywords, salary ranges, or work type
- **Duplicate Detection**: Identify and merge duplicate job postings

## Connect with Me

If you find this project useful, let's connect!

- [Instagram](https://www.instagram.com/dimitri_petrakis)
- [LinkedIn](https://www.linkedin.com/in/dimitrios-petrakis-719443269/)
- [TikTok](https://www.tiktok.com/@dimitri_petrakis)
- [Portfolio](https://dimitripetrakis.com/)

---

Feel free to contribute or suggest improvements!

