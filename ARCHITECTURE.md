# Architecture Documentation

## Module Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           main.py                               │
│                    (Orchestration Layer)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────┐
    │              scraper package modules                     │
    └─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
    
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  config.py   │      │user_input.py │      │data_export.py│
│              │      │              │      │              │
│ - Constants  │      │ - Sort pref  │      │ - Save Excel │
│ - Timeouts   │      │ - Workers    │      │ - Statistics │
│ - URLs       │      │ - Job range  │      │ - Filenames  │
└──────────────┘      └──────────────┘      └──────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│driver_setup  │      │url_builder   │      │extractors.py │
│              │      │              │      │              │
│ - Chrome opt │      │ - Build URL  │      │ - Extract    │
│ - WebDriver  │      │ - Filters    │      │   email      │
│ - Anti-bot   │      │              │      │ - Extract    │
│              │      │              │      │   phone      │
│              │      │              │      │ - Extract    │
│              │      │              │      │   website    │
└──────────────┘      └──────────────┘      └──────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│page_parser   │      │link_collect  │      │job_scraper   │
│              │      │              │      │              │
│ - Job count  │◄─────│ - Collect    │      │ - Scrape job │
│ - Job links  │      │   links      │      │   details    │
│ - Pagination │      │ - Filter     │      │ - 12 fields  │
│              │      │   range      │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────┐
                                          │parallel_     │
                                          │scraper.py    │
                                          │              │
                                          │ - Thread     │
                                          │   pool       │
                                          │ - Checkpoint │
                                          │ - Progress   │
                                          └──────────────┘
```

## Data Flow

```
User Input
   │
   ├─► Sort Preference (y/n)
   ├─► Number of Workers (1-10)
   └─► Job Range (e.g., "1-100")
       │
       ▼
Build Search URL ──► Navigate to Seek
       │
       ▼
Parse Page ──► Get Total Jobs
       │
       ▼
Collect Links (pagination loop)
       │
       ├─► Page 1 links
       ├─► Page 2 links
       └─► Page N links
           │
           ▼
Filter Job Range (start_job to end_job)
           │
           ▼
┌──────────────────────────────────────┐
│    Parallel Scraping (ThreadPool)    │
│                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │Browser1│ │Browser2│ │BrowserN│  │
│  │        │ │        │ │        │  │
│  │ Job 1  │ │ Job 2  │ │ Job N  │  │
│  │ Job 11 │ │ Job 12 │ │ Job... │  │
│  └────────┘ └────────┘ └────────┘  │
│                                      │
│  [Thread-safe data collection]      │
│  [Checkpoint every 100 jobs]        │
└──────────────────────────────────────┘
           │
           ▼
Save to Excel ──► Statistics Report
```

## Dependency Graph

```
main.py depends on:
    scraper.driver_setup     (setup_driver)
    scraper.url_builder      (build_search_url)
    scraper.page_parser      (get_total_jobs)
    scraper.link_collector   (collect_job_links, filter_job_range)
    scraper.parallel_scraper (scrape_jobs_in_parallel)
    scraper.user_input       (get_sort_preference, get_parallel_workers, get_job_range)
    scraper.data_export      (create_filename, save_to_excel, print_statistics, save_partial_data)

parallel_scraper.py depends on:
    scraper.driver_setup     (setup_driver)
    scraper.job_scraper      (scrape_job_details, create_empty_job_data)
    scraper.config           (COLUMNS)

job_scraper.py depends on:
    scraper.extractors       (extract_contact_info)
    scraper.config           (BRIEF_PAUSE, ELEMENT_WAIT_TIMEOUT, COLUMNS)

page_parser.py depends on:
    scraper.config           (ELEMENT_WAIT_TIMEOUT, PAGINATION_SCROLL)

link_collector.py depends on:
    scraper.page_parser      (get_job_links_on_page, click_next_page)
    scraper.config           (MAX_PAGES)

data_export.py depends on:
    scraper.config           (COLUMNS)
```

## Benefits of Refactoring

### Before (677 lines, single file)
- ❌ Hard to test individual components
- ❌ Difficult to locate and fix bugs
- ❌ Mixed concerns (UI, scraping, data, config)
- ❌ Hard to reuse code
- ❌ Cognitive overload

### After (11 files, modular)
- ✅ Each module is ~50-150 lines
- ✅ Easy to test individual functions
- ✅ Clear separation of concerns
- ✅ Easy to modify configuration
- ✅ Reusable components
- ✅ Easy to understand and maintain
- ✅ Can swap implementations easily

## Cohesion Examples

**High Cohesion** (Good):
- `extractors.py` - All functions deal with text extraction
- `user_input.py` - All functions handle user prompts
- `data_export.py` - All functions handle Excel output

**Low Coupling** (Good):
- `job_scraper` doesn't know about parallel execution
- `extractors` doesn't know about Selenium
- `config` is pure data, no logic

## Testing Strategy

Each module can now be tested independently:

```python
# Test extractors
from scraper.extractors import extract_email
assert extract_email("Contact us at test@example.com") == "test@example.com"

# Test URL builder
from scraper.url_builder import build_search_url
assert "ListedDate" in build_search_url(sort_by_date=True)

# Test data export
from scraper.data_export import create_filename
assert "interrupted" in create_filename(interrupted=True)
```
