# Scripts Directory

This directory contains standalone scraping scripts.

## Scripts

### scrape_companies.py
Scrapes jobs from specific companies (e.g., Victorian Government departments).

**Usage:**
```bash
python scripts/scrape_companies.py
```

**Configuration:**
- Edit `scraper/config.py` to modify `GOV_COMPANIES` list
- Adjust `max_jobs_per_company` parameter as needed
- Output saved to `data/vic_gov_ict_jobs.xlsx`

## Notes

- Scripts use the main scraper engine from the `scraper/` module
- Run from project root directory
- All output files go to `data/` directory
