"""Parallel scraping orchestration."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .config import COLUMNS

# Thread-safe lock for data collection
data_lock = Lock()


def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    """Scrape a single job in a separate browser instance (for parallel execution)."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
        job_data = scrape_job_details(driver, job_url)
        driver.quit()
        
        # Check if job was filtered (recruitment company)
        if job_data is None:
            print(f"  🚫 [Job #{job_num}] Filtered (recruitment company)")
            return None
        
        print(f"  ✓ [Job #{job_num}] Completed")
        return job_data
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"  ✗ [Job #{job_num}] Failed: {e}")
        return create_empty_job_data(job_url)


def scrape_jobs_in_parallel(job_urls, start_job, num_workers, filename):
    """
    Scrape jobs in parallel using multiple browser instances.
    
    Args:
        job_urls: List of job URLs to scrape
        start_job: Starting job number for display
        num_workers: Number of parallel browser instances
        filename: Output Excel filename
    
    Returns:
        List of job data dictionaries
    """
    all_jobs_data = [None] * len(job_urls)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all jobs
        future_to_index = {
            executor.submit(scrape_job_parallel, job_url, start_job + idx, len(job_urls), headless=True): idx 
            for idx, job_url in enumerate(job_urls)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                job_data = future.result()
                all_jobs_data[idx] = job_data
                completed += 1
                
                # Progress update
                if completed % 10 == 0 or completed == len(job_urls):
                    print(f"  Progress: {completed}/{len(job_urls)} jobs completed ({(completed/len(job_urls)*100):.1f}%)")
                
                # Save checkpoint every 100 jobs
                if completed % 100 == 0:
                    save_checkpoint(all_jobs_data, filename)
                    print(f"  💾 Checkpoint saved: {completed} jobs")
                    
            except Exception as e:
                print(f"  ✗ Job {idx+1} failed: {e}")
                all_jobs_data[idx] = create_empty_job_data(job_urls[idx])
    
    # Remove any None values with progress feedback
    print("\n  📊 Processing scraped data...")
    all_jobs_data = [j for j in all_jobs_data if j is not None]
    print(f"  ✅ Data processing complete: {len(all_jobs_data)} jobs ready for export")
    
    return all_jobs_data


def save_checkpoint(all_jobs_data, filename):
    """Save a checkpoint of the current scraping progress."""
    with data_lock:
        # Filter None values efficiently
        valid_data = [j for j in all_jobs_data if j is not None]
        if valid_data:
            # Create DataFrame only once and save
            df_checkpoint = pd.DataFrame(valid_data, columns=COLUMNS)
            df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
