# Seek Job Scraper - ICT Jobs Melbourne

## Overview

This Python-based web scraper uses Selenium to collect **Information & Communication Technology** job postings from [Seek](https://www.seek.com.au) in the **All Melbourne VIC** region. It extracts job titles, company names, and contact information (email, phone, website) from each listing and exports the data to an Excel file.

> **⚠️ Educational Use Only:** This scraper ignores robots.txt and is intended for learning purposes only. Please respect Seek's terms of service and rate limits.

## Features

- **Targeted Search**: Automatically searches ICT jobs in All Melbourne VIC
- **Full Pagination**: Scrapes all available job listings (supports 1750+ jobs)
- **Contact Extraction**: Extracts email addresses, phone numbers, and websites from job descriptions
- **Excel Export**: Outputs data to a timestamped Excel file (.xlsx)
- **Headless Mode**: Runs Chrome in headless mode for background scraping
- **Progress Tracking**: Real-time progress updates during scraping

## Installation

### Prerequisites

Ensure you have the following installed:

- **Python 3.8+** 
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
   - `selenium` - Web automation framework
   - `webdriver-manager` - Automatic ChromeDriver management
   - `pandas` - Data manipulation and analysis
   - `openpyxl` - Excel file writing

## Usage

Simply run the script:

```sh
python main.py
```

The scraper will:
1. Navigate to the ICT jobs search page for All Melbourne VIC
2. Collect all job listing URLs from paginated results
3. Visit each job page and extract:
   - Job title
   - Company name
   - Email address (if available)
   - Phone number (if available)
   - Website URL (if available)
4. Export all data to `seek_ict_jobs_melbourne_YYYYMMDD_HHMMSS.xlsx`

### Output

The Excel file contains the following columns:
- `job_title` - Job position title
- `company` - Hiring company name
- `email` - Contact email (empty if not found)
- `phone` - Contact phone number (empty if not found)
- `website` - Company/contact website (empty if not found)
- `url` - Direct link to the job posting

### Sample Output

```
============================================================
SEEK Web Scraper - ICT Jobs in All Melbourne VIC
============================================================

NOTE: This scraper is for educational purposes only.
Initializing...

Navigating to: https://www.seek.com.au/information-communication-technology-jobs/in-All-Melbourne-VIC

Total ICT jobs in All Melbourne VIC: 1750

Collecting job links from search results...
  Scraping page 1... (collected 0 links so far)
  Scraping page 2... (collected 22 links so far)
  ...

Total job links collected: 1750

Scraping individual job details...
  [1/1750] Scraping job...
  [2/1750] Scraping job...
  ...
  Progress: 50/1750 jobs scraped
  ...

============================================================
SUCCESS! Data exported to: seek_ict_jobs_melbourne_20251118_143022.xlsx
Total jobs scraped: 1750
Jobs with email: 342
Jobs with phone: 521
Jobs with website: 873
============================================================
```

## Customization

To modify the search criteria, edit the `build_search_url()` function in `main.py`:

```python
def build_search_url():
    """Build the Seek URL for ICT jobs in All Melbourne VIC."""
    # Change the URL to match your desired classification and location
    base_url = "https://www.seek.com.au/information-communication-technology-jobs/in-All-Melbourne-VIC"
    return base_url
```

## Troubleshooting

**ChromeDriver Issues:**
- The script uses `webdriver-manager` to automatically download the correct ChromeDriver version
- If you encounter issues, ensure Chrome is up to date

**Timeout Errors:**
- Seek may throttle requests if you scrape too quickly
- The script includes delays between requests
- If errors persist, increase `time.sleep()` values

**No Contact Information:**
- Many job postings don't include direct contact info
- Empty fields are expected and normal

## Notes

- Scraping ~1750 jobs may take 2-3 hours depending on your internet speed
- The script runs in headless mode (no browser window visible)
- Progress is printed to the console in real-time
- Each run creates a new timestamped Excel file

1. Scrape a single job posting and extract its description.
2. Detect a specified keyword within the job description.
3. Detect multiple keywords.
4. Allow users to specify the number of job postings to scrape.
5. Format the output for readability.
6. **(Future Update)** Store results in a CSV file.

## Future Enhancements

- **Fix job count limitation** (scraping only 22 jobs at a time).
- **Improve efficiency** by optimizing Selenium operations.
- **CSV export** for easier data analysis.
- **Add GUI support** for easier user interaction.

## Connect with Me

If you find this project useful, let's connect!

- [Instagram](https://www.instagram.com/dimitri_petrakis)
- [LinkedIn](https://www.linkedin.com/in/dimitrios-petrakis-719443269/)
- [TikTok](https://www.tiktok.com/@dimitri_petrakis)
- [Portfolio](https://dimitripetrakis.com/)

---

Feel free to contribute or suggest improvements!

