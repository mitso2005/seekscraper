"""Streaming parallel scraper that starts processing immediately."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
import signal
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .google_enrichment import search_google_business_phone
from .config import COLUMNS, ENABLE_GOOGLE_ENRICHMENT, CHECKPOINT_INTERVAL
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


def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    """Scrape a single job in a separate browser instance (for parallel execution)."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
        
        # Track driver globally for cleanup
        with drivers_lock:
            active_drivers.append(driver)
        
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
        
        driver.quit()
        
        # Remove from active list
        with drivers_lock:
            if driver in active_drivers:
                active_drivers.remove(driver)
        
        # Check if job was filtered
        if job_data is None:
            print(f"  🚫 [Job #{job_num}] Filtered")
            return None
        
        # Show office phone status
        office_phone_status = "📞" if job_data.get('office_phone') else ""
        print(f"  ✓ [Job #{job_num}] Completed {office_phone_status}")
        return job_data
    except Exception as e:
        if driver:
            try:
                driver.quit()
                with drivers_lock:
                    if driver in active_drivers:
                        active_drivers.remove(driver)
            except:
                pass
        print(f"  ✗ [Job #{job_num}] Failed: {e}")
        return create_empty_job_data(job_url)


def scrape_jobs_streaming(driver, start_job, end_job, num_workers, filename):
    """
    Scrape jobs using streaming approach - starts scraping while still collecting links.
    Auto-resumes from checkpoint if available.
    
    Args:
        driver: Selenium WebDriver for link collection
        start_job: Starting job number (1-indexed) - e.g., 1050
        end_job: Ending job number (inclusive) - e.g., 1550
        num_workers: Number of parallel browser instances
        filename: Output Excel filename
    
    Returns:
        Tuple of (all_jobs_data, all_job_urls)
    """
    global current_executor
    
    # Initialize resume manager
    resume_mgr = ResumeManager(filename)
    
    all_jobs_data = []
    all_job_urls = []
    completed = 0
    
    # Create thread pool for scraping
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        current_executor = executor
        futures = {}
        job_index = 0
        
        # Stream links and submit jobs as we get them
        for batch_links in stream_job_links(driver, end_job):
            all_job_urls.extend(batch_links)
            
            # Submit this batch for scraping immediately
            for job_url in batch_links:
                # Calculate actual job number (1-indexed position in ALL jobs)
                current_job_num = len(all_job_urls) - len(batch_links) + job_index + 1
                
                # Only scrape if within requested range AND not already completed
                if current_job_num >= start_job and current_job_num <= end_job:
                    if not resume_mgr.is_completed(job_url):
                        future = executor.submit(scrape_job_parallel, job_url, current_job_num, end_job, headless=True)
                        futures[future] = len(futures)
                    else:
                        print(f"  ⏭️  [Job #{current_job_num}] Already completed (skipped)")
                
                job_index += 1
            
            jobs_to_scrape = len(futures)
            already_done = len(resume_mgr.completed_urls)
            print(f"  ⚡ Batch collected. To scrape: {jobs_to_scrape}, Already done: {already_done}")
        
        # Close the search driver now that we're done collecting
        print(f"\n✅ Link collection complete! {len(all_job_urls)} total links found.")
        print(f"📌 Job range {start_job}-{end_job}: {len(futures)} jobs to scrape")
        if len(resume_mgr.completed_urls) > 0:
            print(f"♻️  Resuming: {len(resume_mgr.completed_urls)} jobs already completed")
        print(f"⚡ Scraping in progress with {num_workers} parallel browsers...\n")
        driver.quit()
        
        # Initialize results array
        all_jobs_data = [None] * len(futures)
        
        # Collect results as they complete
        for future in as_completed(futures):
            idx = futures[future]
            try:
                job_data = future.result()
                all_jobs_data[idx] = job_data
                completed += 1
                
                # Progress update
                if completed % 10 == 0 or completed == len(futures):
                    total_done = completed + len(resume_mgr.completed_urls)
                    print(f"  Progress: {completed}/{len(futures)} jobs completed this session ({(completed/len(futures)*100):.1f}%) | Total: {total_done}")
                
                # Save checkpoint using CHECKPOINT_INTERVAL
                if completed % CHECKPOINT_INTERVAL == 0:
                    # Filter valid data
                    valid_data = [j for j in all_jobs_data if j is not None]
                    # Merge with existing checkpoint
                    merged_data = resume_mgr.merge_with_existing(valid_data)
                    # Save checkpoint
                    df_checkpoint = pd.DataFrame(merged_data, columns=COLUMNS)
                    df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
                    # Save progress tracking
                    resume_mgr.save_progress(valid_data)
                    print(f"  💾 Checkpoint saved: {len(merged_data)} total jobs")
                    
            except Exception as e:
                print(f"  ✗ Job {idx+1} failed: {e}")
                if idx < len(all_job_urls):
                    all_jobs_data[idx] = create_empty_job_data(all_job_urls[idx])
    
    current_executor = None
    
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
