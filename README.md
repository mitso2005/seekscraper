# Seek Web Scraper - ICT Jobs Melbourne

Automated web scraper for ICT jobs in Melbourne. Filters agencies, extracts contact info, exports to Excel.

## Features

- Scrapes 12 fields: title, company, location, classification, work type, salary, time posted, email, phone, office phone, website, URL
- Filters recruitment agencies, contract/temp roles, large companies (1000+ employees)
- Google Business phone enrichment (optional)
- Parallel processing (1-20 browsers)
- Auto-resume from checkpoints

## Installation

### Docker (Recommended)
```bash
docker-compose build
```

### Local Python
```bash
pip install -r requirements.txt
```

## Usage

### Docker - Interactive Mode
```bash
docker-compose run --rm scraper
```
Prompts you for: sort by date (y/n), browser count (1-20), job range (1-1000, all)

### Docker - Automatic Mode
```bash
docker-compose up scraper-auto
```
Defaults: sort by date (y), browser count (20), all jobs

### Local Python
```bash
python main.py
```

## Output

Excel files saved to `data/seek_ict_jobs_melbourne_YYYYMMDD_HHMMSS.xlsx`

## Limitations

Seek limits pagination to ~550 jobs (25 pages). Total may show more but only first 550 are accessible.

## Disclaimer

Educational purposes only. Review Seek's Terms of Service before use.
