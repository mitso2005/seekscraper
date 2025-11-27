"""Parallel scraping orchestration."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .google_enrichment import search_google_business_phone
from .config import COLUMNS, ENABLE_GOOGLE_ENRICHMENT
from .phone_cache import PhoneCache

# Thread-safe lock for data collection
data_lock = Lock()
# Persistent cache for company phone numbers
phone_cache = PhoneCache()


def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    """Scrape a single job in a separate browser instance."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
        job_data = scrape_job_details(driver, job_url)
        
        if job_data is not None and ENABLE_GOOGLE_ENRICHMENT:
            company = job_data.get('company', '')
            location = job_data.get('location', '')
            
            if company and company != 'N/A':
                cached_phone = phone_cache.get(company)
                
                if cached_phone is not None:
                    job_data['office_phone'] = cached_phone
                else:
                    office_phone = search_google_business_phone(driver, company, location)
                    job_data['office_phone'] = office_phone
                    phone_cache.set(company, office_phone, location)
        
        driver.quit()
        
        if job_data is None:
            print(f"  [Job #{job_num}] Filtered")
            return None
        
        office_phone_status = " (phone)" if job_data.get('office_phone') else ""
        print(f"  [Job #{job_num}] Completed{office_phone_status}")
        return job_data
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"  [Job #{job_num}] Failed: {e}")
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
                
                if completed % 10 == 0 or completed == len(job_urls):
                    print(f"  Progress: {completed}/{len(job_urls)} jobs completed ({(completed/len(job_urls)*100):.1f}%)")
                
                if completed % 100 == 0:
                    save_checkpoint(all_jobs_data, filename)
                    print(f"  Checkpoint saved: {completed} jobs")
                    
            except Exception as e:
                print(f"  ✗ Job {idx+1} failed: {e}")
                all_jobs_data[idx] = create_empty_job_data(job_urls[idx])
    
    print("\nProcessing scraped data...")
    all_jobs_data = [j for j in all_jobs_data if j is not None]
    
    if ENABLE_GOOGLE_ENRICHMENT:
        phones_found = sum(1 for job in all_jobs_data if job.get('office_phone'))
        cache_stats = phone_cache.get_stats()
        print(f"  Office phones found: {phones_found}/{len(all_jobs_data)} jobs")
        print(f"  Cache: {cache_stats['total_companies']} companies ({cache_stats['with_phone']} with phones)")
    
    print(f"  Data processing complete: {len(all_jobs_data)} jobs ready for export")
    
    return all_jobs_data


def save_checkpoint(all_jobs_data, filename):
    """Save a checkpoint of the current scraping progress."""
    with data_lock:
        valid_data = [j for j in all_jobs_data if j is not None]
        if valid_data:
            df_checkpoint = pd.DataFrame(valid_data, columns=COLUMNS)
            df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
