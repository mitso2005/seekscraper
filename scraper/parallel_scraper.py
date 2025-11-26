"""Parallel scraping orchestration."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
import json
import os
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .google_enrichment import search_google_business_phone
from .config import COLUMNS, ENABLE_GOOGLE_ENRICHMENT, COMPANY_PHONE_CACHE_FILE

# Thread-safe lock for data collection
data_lock = Lock()
# Cache for company phone numbers (thread-safe)
company_phone_cache = {}
cache_lock = Lock()


def load_phone_cache():
    """Load company phone cache from JSON file."""
    global company_phone_cache
    if os.path.exists(COMPANY_PHONE_CACHE_FILE):
        try:
            with open(COMPANY_PHONE_CACHE_FILE, 'r', encoding='utf-8') as f:
                company_phone_cache = json.load(f)
            print(f"  📞 Loaded {len(company_phone_cache)} cached company phones")
        except Exception as e:
            print(f"  ⚠️  Could not load phone cache: {e}")
            company_phone_cache = {}
    else:
        company_phone_cache = {}


def save_phone_cache():
    """Save company phone cache to JSON file."""
    try:
        with cache_lock:
            with open(COMPANY_PHONE_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(company_phone_cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠️  Could not save phone cache: {e}")


def scrape_job_with_driver(driver, job_url, job_num):
    """Scrape a single job using an existing browser instance."""
    try:
        job_data = scrape_job_details(driver, job_url)
        
        # If job was not filtered and Google enrichment is enabled, get office phone
        if job_data is not None and ENABLE_GOOGLE_ENRICHMENT:
            company = job_data.get('company', '')
            location = job_data.get('location', '')
            
            if company and company != 'N/A':
                # Check cache first (thread-safe)
                with cache_lock:
                    if company in company_phone_cache:
                        job_data['office_phone'] = company_phone_cache[company]
                    else:
                        # Not in cache, search Google (still using same driver)
                        office_phone = search_google_business_phone(driver, company, location)
                        job_data['office_phone'] = office_phone
                        company_phone_cache[company] = office_phone
                        # Save cache immediately after finding new phone
                        save_phone_cache()
        
        # Check if job was filtered
        if job_data is None:
            print(f"  🚫 [Job #{job_num}] Filtered")
            return None
        
        # Show office phone status
        office_phone_status = "📞" if job_data.get('office_phone') else ""
        print(f"  ✓ [Job #{job_num}] Completed {office_phone_status}")
        return job_data
    except Exception as e:
        print(f"  ✗ [Job #{job_num}] Failed: {e}")
        return create_empty_job_data(job_url)


def persistent_worker(jobs_queue, results, headless=True):
    """Worker that maintains a persistent browser for multiple jobs."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
        while True:
            job_item = jobs_queue.get()
            if job_item is None:  # Shutdown signal
                break
            
            idx, job_url, job_num = job_item
            job_data = scrape_job_with_driver(driver, job_url, job_num)
            results[idx] = job_data
            
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def scrape_jobs_in_parallel(job_urls, start_job, num_workers, filename):
    """
    Scrape jobs in parallel using persistent browser instances (connection pooling).
    
    Args:
        job_urls: List of job URLs to scrape
        start_job: Starting job number for display
        num_workers: Number of parallel browser instances
        filename: Output Excel filename
    
    Returns:
        List of job data dictionaries
    """
    from queue import Queue
    from threading import Thread
    
    # Load phone cache at startup
    load_phone_cache()
    
    all_jobs_data = [None] * len(job_urls)
    jobs_queue = Queue()
    completed = [0]  # Use list for mutable counter
    
    # Enqueue all jobs
    for idx, job_url in enumerate(job_urls):
        jobs_queue.put((idx, job_url, start_job + idx))
    
    # Add shutdown signals
    for _ in range(num_workers):
        jobs_queue.put(None)
    
    # Start persistent worker threads
    workers = []
    for _ in range(num_workers):
        worker = Thread(target=persistent_worker, args=(jobs_queue, all_jobs_data, True))
        worker.start()
        workers.append(worker)
    
    # Monitor progress
    import time
    while any(w.is_alive() for w in workers):
        time.sleep(0.5)
        current_completed = sum(1 for job in all_jobs_data if job is not None)
        if current_completed != completed[0]:
            completed[0] = current_completed
            
            # Progress update
            if completed[0] % 10 == 0 or completed[0] == len(job_urls):
                print(f"  Progress: {completed[0]}/{len(job_urls)} jobs completed ({(completed[0]/len(job_urls)*100):.1f}%)")
            
            # Save checkpoint every 100 jobs
            if completed[0] % 100 == 0:
                save_checkpoint(all_jobs_data, filename)
                print(f"  💾 Checkpoint saved: {completed[0]} jobs")
    
    # Wait for all workers to finish
    for worker in workers:
        worker.join()
    
    # Remove any None values with progress feedback
    print("\n  📊 Processing scraped data...")
    all_jobs_data = [j for j in all_jobs_data if j is not None]
    
    # Report enrichment statistics if enabled
    if ENABLE_GOOGLE_ENRICHMENT:
        phones_found = sum(1 for job in all_jobs_data if job.get('office_phone'))
        unique_companies = len(company_phone_cache)
        print(f"  📞 Office phones found: {phones_found}/{len(all_jobs_data)} jobs ({unique_companies} unique companies)")
    
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
