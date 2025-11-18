# Recruitment Company Filtering Feature

## Overview
Added automatic filtering to exclude job postings from recruitment agencies, ensuring only direct employer positions are saved to the Excel output.

## Implementation

### 1. Configuration (`scraper/config.py`)
Added a comprehensive list of top Australian recruitment companies:

```python
RECRUITMENT_COMPANIES = [
    'Hays Technology', 'Hays',
    'Robert Half Technology', 'Robert Half',
    'Michael Page Technology', 'Michael Page',
    'Paxus',
    'Talent International',
    'Peoplebank',
    'Finite IT',
    'Greythorn',
    'Halcyon Knights',
    'Lanson Partners',
    'Ignite',
    'Morgan McKinley Technology', 'Morgan McKinley',
    'Clicks IT Recruitment', 'Clicks IT',
    'Ambition Technology', 'Ambition',
    'Davidson Technology', 'Davidson',
    'Charterhouse IT', 'Charterhouse',
    'Sirius Technology', 'Sirius',
    'Bluefin Resources', 'Bluefin',
    'Hudson Australia', 'Hudson',
    'Expert360'
]
```

### 2. Job Scraper (`scraper/job_scraper.py`)
Added filtering function and logic:

**New Function:**
```python
def is_recruitment_company(company_name):
    """
    Check if the company is a recruitment agency.
    Returns True if company matches any recruitment company (case-insensitive).
    """
    if not company_name or company_name == 'N/A':
        return False
    
    company_lower = company_name.lower().strip()
    
    for recruiter in RECRUITMENT_COMPANIES:
        if recruiter.lower() in company_lower:
            return True
    
    return False
```

**Updated scrape_job_details():**
- Extracts company name first
- Checks if it's a recruitment company
- Returns `None` if filtered (instead of job data)
- Continues with full extraction only for direct employers

### 3. Parallel Scraper (`scraper/parallel_scraper.py`)
Updated to handle filtered jobs:

```python
def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    # ... existing code ...
    
    # Check if job was filtered (recruitment company)
    if job_data is None:
        print(f"  🚫 [Job #{job_num}] Filtered (recruitment company)")
        return None
    
    print(f"  ✓ [Job #{job_num}] Completed")
    return job_data
```

- Displays 🚫 emoji for filtered jobs
- Returns `None` for filtered jobs
- Maintains job numbering for tracking

### 4. Data Export (`scraper/data_export.py`)
Enhanced statistics to show filtering results:

**Updated print_statistics():**
- Accepts `total_processed` and `filtered_count` parameters
- Shows how many jobs were filtered out
- Displays separate counts for processed vs saved jobs

### 5. Main Orchestration (`main.py`)
Added tracking and reporting:

```python
total_processed = len(all_job_links)
all_jobs_data = scrape_jobs_in_parallel(all_job_links, start_job, num_workers, filename)
filtered_count = total_processed - len(all_jobs_data)

print_statistics(df, filename, total_processed, filtered_count)
```

## How It Works

### Filtering Process
1. **Job page loads** → Company name extracted
2. **Company name checked** → Case-insensitive matching against recruitment list
3. **If recruitment company** → Job skipped, returns `None`
4. **If direct employer** → Full data extraction continues
5. **Final data** → Only non-recruitment jobs saved to Excel

### Matching Logic
- **Case-insensitive**: "HAYS", "Hays", "hays" all match
- **Partial matching**: "Hays Technology Pty Ltd" matches "Hays"
- **Both variants**: Includes both full names and short names
  - "Robert Half Technology" and "Robert Half"
  - "Michael Page Technology" and "Michael Page"

## Example Output

### Console Output
```
⚡ Scraping 500 jobs using 5 parallel browser(s)...
(Much faster with parallel processing!)
🚫 Filtering out recruitment companies...

  ✓ [Job #1] Completed
  🚫 [Job #2] Filtered (recruitment company)
  ✓ [Job #3] Completed
  🚫 [Job #4] Filtered (recruitment company)
  ✓ [Job #5] Completed
  ...
  Progress: 100/500 jobs completed (20.0%)
  ...

============================================================
✅ SUCCESS! Data exported to: seek_ict_jobs_melbourne_20251119_143022.xlsx
Total jobs processed: 500
Jobs filtered (recruitment companies): 87
Jobs saved to Excel: 413
Successfully extracted: 405
Failed to extract: 8
Jobs with email: 89
Jobs with phone: 143
Jobs with website: 267
============================================================
```

### Key Statistics
- **Total jobs processed**: All jobs scraped (500)
- **Jobs filtered**: Recruitment companies excluded (87)
- **Jobs saved to Excel**: Direct employers only (413)
- **Successfully extracted**: Jobs with valid data (405)
- **Failed to extract**: Jobs with errors (8)

## Benefits

### For Job Seekers
✅ **No recruiter spam**: Only see direct employer positions  
✅ **Higher quality leads**: Apply directly to hiring companies  
✅ **Save time**: Don't waste time on recruiter listings  
✅ **Better success rate**: Direct applications often have higher response rates

### For Data Quality
✅ **Cleaner dataset**: No duplicate roles from multiple recruiters  
✅ **Accurate company info**: Actual employer names only  
✅ **Better analytics**: Understand which companies are actually hiring  
✅ **Reduced noise**: Focus on real opportunities

## Customization

### Add More Recruitment Companies
Edit `scraper/config.py`:

```python
RECRUITMENT_COMPANIES = [
    # ... existing companies ...
    'New Recruitment Company',
    'Another Recruiter',
]
```

### Disable Filtering
Comment out the filter check in `scraper/job_scraper.py`:

```python
# if is_recruitment_company(job_data['company']):
#     return None
```

### Include Specific Recruiters
Remove them from the `RECRUITMENT_COMPANIES` list in `scraper/config.py`

## Testing Recommendations

1. **Test with small batch first**: Use "1-20" to verify filtering works
2. **Check console output**: Look for 🚫 indicators
3. **Verify Excel file**: Confirm no recruitment companies in company column
4. **Review statistics**: Check filtered count matches expectations

## Known Recruitment Companies Filtered

- Hays Technology / Hays
- Robert Half Technology / Robert Half
- Michael Page Technology / Michael Page
- Paxus
- Talent International
- Peoplebank
- Finite IT
- Greythorn
- Halcyon Knights
- Lanson Partners
- Ignite
- Morgan McKinley
- Clicks IT Recruitment
- Ambition
- Davidson
- Charterhouse
- Sirius Technology
- Bluefin Resources
- Hudson Australia
- Expert360

## Future Enhancements

Planned for AI integration (as mentioned in README):
- **AI Recruitment Detection**: Auto-detect new recruitment companies
- **Company Mapping**: Suggest actual employers behind recruiters
- **Smart Filtering**: Use ML to identify recruitment patterns
