"""User input handling and validation."""

from .config import DEFAULT_WORKERS, MAX_WORKERS


def get_sort_preference():
    """Ask user if they want to sort by newest jobs first."""
    while True:
        sort_input = input("\nSort by newest jobs first? (y/n): ").strip().lower()
        if sort_input in ['y', 'n']:
            return sort_input == 'y'
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def get_parallel_workers():
    """Ask user how many parallel browsers to use."""
    while True:
        parallel_input = input(f"\nHow many parallel browsers? (1-{MAX_WORKERS}, recommended: {DEFAULT_WORKERS}): ").strip()
        if parallel_input.isdigit() and 1 <= int(parallel_input) <= MAX_WORKERS:
            return int(parallel_input)
        else:
            print(f"Invalid input. Enter a number between 1 and {MAX_WORKERS}.")


def get_scraping_mode():
    """Ask user if they want to use streaming mode (faster initial start)."""
    while True:
        mode_input = input("\nUse streaming mode? (faster, scrapes while collecting links) (y/n, default: y): ").strip().lower()
        if mode_input == '' or mode_input == 'y':
            return True
        elif mode_input == 'n':
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def get_job_range(total_jobs):
    """
    Ask user which jobs to scrape.
    Supports both job-based ranges (legacy) and page-based ranges (new).
    
    Args:
        total_jobs: Total number of jobs available
    
    Returns:
        Tuple of (start_job, end_job, use_page_based, start_page)
        - start_job: Job number to start from
        - end_job: Job number to end at
        - use_page_based: Boolean indicating if page-based search should be used
        - start_page: Page number to start from (only relevant if use_page_based=True)
    """
    while True:
        print("\n" + "="*60)
        print("SEARCH MODE OPTIONS:")
        print("="*60)
        print("1. Job-based search (legacy):  '1-100', '600-700'")
        print("   - Clicks through all pages sequentially")
        print("\n2. Page-based search (new):    'page:15-20', 'page:8'")
        print("   - Navigates directly to page 15+ (faster for high ranges)")
        print("   - Example: 'page:15-20' means collect jobs from page 15 onward")
        print("   - Collects ~20 jobs per page, adjust range as needed")
        print("="*60)
        
        range_input = input(f"\nEnter search range (or 'all' for jobs 1-{total_jobs}): ").strip().lower()
        
        if range_input == 'all':
            print(f"Will scrape ALL jobs (1 to {total_jobs})")
            return 1, total_jobs, False, 1, None
        
        # Page-based search
        elif range_input.startswith('page:'):
            try:
                page_range = range_input[5:].strip()
                
                if '-' in page_range:
                    # Range of pages: 'page:15-20'
                    parts = page_range.split('-')
                    start_page = int(parts[0].strip())
                    end_page = int(parts[1].strip())
                    
                    if start_page < 1 or end_page < start_page:
                        print("Invalid page range. Start page must be >= 1 and start <= end.")
                        continue
                    
                    # For page-based search, use a large end_job to not limit by job count
                    estimated_end_job = 999999  # Very large number, use end_page instead
                    num_pages = end_page - start_page + 1
                    estimated_jobs = num_pages * 22
                    print(f"Will scrape pages {start_page} to {end_page} ({num_pages} pages)")
                    print(f"(Estimated: approximately {estimated_jobs} jobs ({num_pages} pages × ~20 jobs/page))")
                    return 1, estimated_end_job, True, start_page, end_page
                else:
                    # Single page: 'page:15' means start from page 15
                    start_page = int(page_range)
                    
                    if start_page < 1:
                        print("Invalid page number. Must be >= 1.")
                        continue
                    
                    # Collect many jobs from this page onward (no end_page limit)
                    estimated_end_job = 999999  # Very large number, will use MAX_PAGES limit instead
                    print(f"Will scrape jobs starting from page {start_page} onward")
                    print(f"(Will collect ~20 jobs per page until reaching end of results)")
                    return 1, estimated_end_job, True, start_page, None
                    
            except ValueError:
                print("Invalid page format. Use 'page:15' or 'page:15-20'")
                continue
        
        # Job-based search (legacy)
        elif '-' in range_input:
            try:
                parts = range_input.split('-')
                start_job = int(parts[0].strip())
                end_job = int(parts[1].strip())
                
                if start_job < 1 or end_job > total_jobs or start_job > end_job:
                    print(f"Invalid range. Must be between 1 and {total_jobs}, with start <= end.")
                    continue
                
                print(f"Will scrape jobs {start_job} to {end_job} ({end_job - start_job + 1} jobs)")
                print("(Using job-based search: will click through all pages sequentially)")
                return start_job, end_job, False, 1, None
            except ValueError:
                print("Invalid format. Use format like '1-100' or 'all'.")
        else:
            print("Invalid input. Use formats: '1-100', 'all', 'page:15', or 'page:15-20'.")
