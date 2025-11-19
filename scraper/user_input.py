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
    
    Args:
        total_jobs: Total number of jobs available
    
    Returns:
        Tuple of (start_job, end_job)
    """
    while True:
        range_input = input(f"\nWhich jobs to scrape? (e.g., '1-100', '50-250', or 'all' for all {total_jobs}): ").strip().lower()
        
        if range_input == 'all':
            print(f"Will scrape ALL jobs (1 to {total_jobs})")
            return 1, total_jobs
        elif '-' in range_input:
            try:
                parts = range_input.split('-')
                start_job = int(parts[0].strip())
                end_job = int(parts[1].strip())
                
                if start_job < 1 or end_job > total_jobs or start_job > end_job:
                    print(f"Invalid range. Must be between 1 and {total_jobs}, with start <= end.")
                    continue
                
                print(f"Will scrape jobs {start_job} to {end_job} ({end_job - start_job + 1} jobs)")
                return start_job, end_job
            except ValueError:
                print("Invalid format. Use format like '1-100' or 'all'.")
        else:
            print("Invalid input. Enter a range like '1-100' or 'all'.")
