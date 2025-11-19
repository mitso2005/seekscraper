"""Streaming parallel scraper that starts processing immediately."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
from .driver_setup import setup_driver
from .job_scraper import scrape_job_details, create_empty_job_data
from .google_enrichment import search_google_business_phone
from .config import COLUMNS, ENABLE_GOOGLE_ENRICHMENT
from .streaming_collector import stream_job_links

# Thread-safe lock for data collection
data_lock = Lock()
# Cache for company phone numbers (thread-safe)
company_phone_cache = {}
cache_lock = Lock()


def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    """Scrape a single job in a separate browser instance (for parallel execution)."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
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
            except:
                pass
        print(f"  ✗ [Job #{job_num}] Failed: {e}")
        return create_empty_job_data(job_url)


def scrape_jobs_streaming(driver, end_job, start_job, num_workers, filename):
    """
    Scrape jobs using streaming approach - starts scraping while still collecting links.
    
    Args:
        driver: Selenium WebDriver for link collection
        end_job: Total number of jobs to collect
        start_job: Starting job number for display
        num_workers: Number of parallel browser instances
        filename: Output Excel filename
    
    Returns:
        List of job data dictionaries
    """
    all_jobs_data = []
    all_job_urls = []
    completed = 0
    
    # Create thread pool for scraping
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        
        # Stream links and submit jobs as we get them
        for batch_links in stream_job_links(driver, end_job):
            all_job_urls.extend(batch_links)
            
            # Submit this batch for scraping immediately
            for job_url in batch_links:
                job_num = start_job + len(futures)
                future = executor.submit(scrape_job_parallel, job_url, job_num, end_job, headless=True)
                futures[future] = len(futures)
            
            print(f"  ⚡ Submitted {len(batch_links)} jobs for scraping (total queued: {len(futures)})")
        
        # Close the search driver now that we're done collecting
        print(f"\n✅ Link collection complete! {len(all_job_urls)} links found.")
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
                    print(f"  Progress: {completed}/{len(futures)} jobs completed ({(completed/len(futures)*100):.1f}%)")
                
                # Save checkpoint every 100 jobs
                if completed % 100 == 0:
                    save_checkpoint(all_jobs_data, filename)
                    print(f"  💾 Checkpoint saved: {completed} jobs")
                    
            except Exception as e:
                print(f"  ✗ Job {idx+1} failed: {e}")
                all_jobs_data[idx] = create_empty_job_data(all_job_urls[idx])
    
    # Remove any None values with progress feedback
    print("\n  📊 Processing scraped data...")
    all_jobs_data = [j for j in all_jobs_data if j is not None]
    
    # Report enrichment statistics if enabled
    if ENABLE_GOOGLE_ENRICHMENT:
        phones_found = sum(1 for job in all_jobs_data if job.get('office_phone'))
        unique_companies = len(company_phone_cache)
        print(f"  📞 Office phones found: {phones_found}/{len(all_jobs_data)} jobs ({unique_companies} unique companies)")
    
    print(f"  ✅ Data processing complete: {len(all_jobs_data)} jobs ready for export")
    
    return all_jobs_data, all_job_urls


def save_checkpoint(all_jobs_data, filename):
    """Save a checkpoint of the current scraping progress."""
    with data_lock:
        # Filter None values efficiently
        valid_data = [j for j in all_jobs_data if j is not None]
        if valid_data:
            # Create DataFrame only once and save
            df_checkpoint = pd.DataFrame(valid_data, columns=COLUMNS)
            df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
