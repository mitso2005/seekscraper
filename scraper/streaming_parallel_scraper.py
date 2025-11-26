"""Streaming parallel scraper that starts processing immediately."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
import signal
import time
import json
import os
from datetime import datetime, timedelta
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .google_enrichment import search_google_business_phone
from .config import COLUMNS, ENABLE_GOOGLE_ENRICHMENT, CHECKPOINT_INTERVAL, COMPANY_PHONE_CACHE_FILE
from .streaming_collector import stream_job_links
from .link_collector import filter_job_range
from .resume_manager import ResumeManager

# Thread-safe lock for data collection
data_lock = Lock()
# Cache for company phone numbers (thread-safe)
company_phone_cache = {}
cache_lock = Lock()
# Global executor for cleanup
current_executor = None
active_drivers = []
drivers_lock = Lock()
# Quota error tracking
quota_errors = 0
quota_lock = Lock()
MAX_QUOTA_ERRORS = 5  # Trigger pause after this many errors


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


def cleanup_all_browsers():
    """Force cleanup of all active browser instances."""
    global current_executor, active_drivers
    
    # Shutdown executor
    if current_executor:
        current_executor.shutdown(wait=False, cancel_futures=True)
    
    # Close all active drivers
    with drivers_lock:
        for driver in active_drivers:
            try:
                driver.quit()
            except:
                pass
        active_drivers.clear()


def wait_for_quota_reset(wait_minutes=5):
    """Wait for Google quota to reset."""
    global quota_errors
    
    print(f"\n{'='*60}")
    print(f"⏸️  GOOGLE QUOTA LIMIT - Pausing for {wait_minutes} minutes")
    print(f"{'='*60}\n")
    
    cleanup_all_browsers()
    
    # Countdown
    for remaining in range(wait_minutes * 60, 0, -30):
        mins = remaining // 60
        secs = remaining % 60
        print(f"⏳ Resuming in: {mins:02d}:{secs:02d}", end='\r', flush=True)
        time.sleep(30)
    
    print(f"\n\n✅ Quota reset! Restarting browsers...\n")
    
    # Reset quota counter
    with quota_lock:
        quota_errors = 0


def check_quota_exceeded():
    """Check if quota threshold reached."""
    with quota_lock:
        return quota_errors >= MAX_QUOTA_ERRORS


def scrape_job_with_driver(driver, job_url, job_num):
    """Scrape a single job using an existing browser instance."""
    global quota_errors
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
                        # Not in cache, search Google
                        try:
                            office_phone = search_google_business_phone(driver, company, location)
                            job_data['office_phone'] = office_phone
                            company_phone_cache[company] = office_phone
                            # Save cache immediately after finding new phone
                            save_phone_cache()
                        except Exception as google_err:
                            # Track quota errors
                            if 'quota' in str(google_err).lower() or 'rate' in str(google_err).lower():
                                with quota_lock:
                                    quota_errors += 1
                                    print(f"  ⚠️  Quota error ({quota_errors}/{MAX_QUOTA_ERRORS})")
                            job_data['office_phone'] = ''
        
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
        
        # Track driver globally for cleanup
        with drivers_lock:
            active_drivers.append(driver)
        
        while True:
            job_item = jobs_queue.get()
            if job_item is None:  # Shutdown signal
                break
            
            idx, job_url, job_num = job_item
            job_data = scrape_job_with_driver(driver, job_url, job_num)
            results[idx] = job_data
            jobs_queue.task_done()
            
    finally:
        if driver:
            try:
                driver.quit()
                with drivers_lock:
                    if driver in active_drivers:
                        active_drivers.remove(driver)
            except:
                pass


def scrape_jobs_streaming(driver, start_job, end_job, num_workers, filename, use_page_based=False, start_page=1, end_page=None, sort_by_date=False):
    """
    Scrape jobs using streaming approach with persistent browsers (connection pooling).
    Auto-resumes from checkpoint if available.
    
    Supports both job-based (legacy) and page-based (new) collection strategies.
    
    Args:
        driver: Selenium WebDriver for link collection
        start_job: Starting job number (1-indexed) - e.g., 1050
        end_job: Ending job number (inclusive) - e.g., 1550
        num_workers: Number of parallel browser instances
        filename: Output Excel filename
        use_page_based: If True, use page-based navigation (direct page parameter)
        start_page: Page number to start from (default: 1)
        end_page: Page number to stop at (inclusive). If None, uses end_job as link count threshold.
        sort_by_date: Sort by listing date when navigating (default: False)
    
    Returns:
        Tuple of (all_jobs_data, all_job_urls)
    """
    from queue import Queue
    from threading import Thread
    
    # Load phone cache at startup
    load_phone_cache()
    
    # Initialize resume manager
    resume_mgr = ResumeManager(filename)
    
    all_jobs_data = []
    all_job_urls = []
    jobs_queue = Queue()
    job_index_map = {}  # Map queue items to result indices
    next_idx = [0]  # Mutable counter for indexing
    
    # Start persistent worker threads
    workers = []
    for _ in range(num_workers):
        worker = Thread(target=persistent_worker, args=(jobs_queue, all_jobs_data, True))
        worker.daemon = True
        worker.start()
        workers.append(worker)
    
    # Stream links and submit jobs as we get them
    for batch_links in stream_job_links(driver, end_job, start_page=start_page, sort_by_date=sort_by_date, end_page=end_page):
        all_job_urls.extend(batch_links)
        
        # Submit this batch for scraping immediately
        for job_url in batch_links:
            # Calculate actual job number (1-indexed position in ALL jobs)
            current_job_num = len(all_job_urls) - len(batch_links) + (len(batch_links) - batch_links[::-1].index(job_url) - 1) + 1
            
            # Only scrape if within requested range AND not already completed
            if current_job_num >= start_job and current_job_num <= end_job:
                if not resume_mgr.is_completed(job_url):
                    idx = next_idx[0]
                    next_idx[0] += 1
                    all_jobs_data.append(None)  # Pre-allocate slot
                    jobs_queue.put((idx, job_url, current_job_num))
                else:
                    print(f"  ⏭️  [Job #{current_job_num}] Already completed (skipped)")
        
        jobs_to_scrape = next_idx[0]
        already_done = len(resume_mgr.completed_urls)
        print(f"  ⚡ Batch collected. To scrape: {jobs_to_scrape}, Already done: {already_done}")
    
    # Close the search driver now that we're done collecting
    print(f"\n✅ Link collection complete! {len(all_job_urls)} total links found.")
    print(f"📌 Job range {start_job}-{end_job}: {next_idx[0]} jobs to scrape")
    if len(resume_mgr.completed_urls) > 0:
        print(f"♻️  Resuming: {len(resume_mgr.completed_urls)} jobs already completed")
    print(f"⚡ Scraping in progress with {num_workers} persistent browsers...\n")
    driver.quit()
    
    # Monitor progress
    completed = [0]
    total_jobs = next_idx[0]
    
    while jobs_queue.unfinished_tasks > 0 or any(w.is_alive() for w in workers):
        time.sleep(0.5)
        current_completed = sum(1 for job in all_jobs_data if job is not None)
        
        if current_completed != completed[0]:
            completed[0] = current_completed
            
            # Check quota threshold
            if check_quota_exceeded():
                print("\n⚠️  Quota threshold reached - triggering pause...")
                # Save checkpoint before pausing
                valid_data = [j for j in all_jobs_data if j is not None]
                merged_data = resume_mgr.merge_with_existing(valid_data)
                df_checkpoint = pd.DataFrame(merged_data, columns=COLUMNS)
                df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
                resume_mgr.save_progress(valid_data)
                wait_for_quota_reset(wait_minutes=5)
            
            # Progress update
            if completed[0] % 10 == 0 or completed[0] == total_jobs:
                total_done = completed[0] + len(resume_mgr.completed_urls)
                print(f"  Progress: {completed[0]}/{total_jobs} jobs completed this session ({(completed[0]/total_jobs*100):.1f}%) | Total: {total_done}")
            
            # Save checkpoint using CHECKPOINT_INTERVAL
            if completed[0] % CHECKPOINT_INTERVAL == 0:
                valid_data = [j for j in all_jobs_data if j is not None]
                merged_data = resume_mgr.merge_with_existing(valid_data)
                df_checkpoint = pd.DataFrame(merged_data, columns=COLUMNS)
                df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
                resume_mgr.save_progress(valid_data)
                print(f"  💾 Checkpoint saved: {len(merged_data)} total jobs")
        
        if jobs_queue.empty() and completed[0] >= total_jobs:
            break
    
    # Send shutdown signals
    for _ in range(num_workers):
        jobs_queue.put(None)
    
    # Wait for all workers to finish
    for worker in workers:
        worker.join(timeout=5)
    
    # Remove any None values with progress feedback
    print("\n  📊 Processing scraped data...")
    all_jobs_data = [j for j in all_jobs_data if j is not None]
    
    # Merge with existing data
    final_data = resume_mgr.merge_with_existing(all_jobs_data)
    
    # Report enrichment statistics if enabled
    if ENABLE_GOOGLE_ENRICHMENT:
        phones_found = sum(1 for job in final_data if job.get('office_phone'))
        unique_companies = len(company_phone_cache)
        print(f"  📞 Office phones found: {phones_found}/{len(final_data)} jobs ({unique_companies} unique companies)")
    
    print(f"  ✅ Data processing complete: {len(final_data)} jobs ready for export")
    
    # Cleanup progress file on successful completion
    resume_mgr.cleanup_progress_file()
    
    # Return the URLs that were actually scraped
    filtered_urls = filter_job_range(all_job_urls, start_job, end_job)
    
    return final_data, filtered_urls


def save_checkpoint(all_jobs_data, filename):
    """Save a checkpoint of the current scraping progress."""
    with data_lock:
        # Filter None values efficiently
        valid_data = [j for j in all_jobs_data if j is not None]
        if valid_data:
            # Create DataFrame only once and save
            df_checkpoint = pd.DataFrame(valid_data, columns=COLUMNS)
            df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
