"""Seek Web Scraper - ICT Jobs Melbourne."""

import time
import signal
import sys
from scraper.driver_setup import setup_driver
from scraper.url_builder import build_search_url
from scraper.page_parser import get_total_jobs
from scraper.link_collector import collect_job_links, filter_job_range
from scraper.parallel_scraper import scrape_jobs_in_parallel
from scraper.streaming_parallel_scraper import scrape_jobs_streaming, cleanup_all_browsers
from scraper.user_input import get_sort_preference, get_parallel_workers, get_job_range, get_scraping_mode
from scraper.data_export import create_filename, save_to_excel, print_statistics, save_partial_data
from scraper.config import ENABLE_GOOGLE_ENRICHMENT, CHECKPOINT_INTERVAL

def main():
    """Main execution function."""
    print("=" * 60)
    print("SEEK Web Scraper - ICT Jobs in All Melbourne VIC")
    print("=" * 60)
    print("\nNOTE: This scraper is for educational purposes only.")
    
    sort_by_date = get_sort_preference()
    num_workers = get_parallel_workers()
    use_streaming = get_scraping_mode()
    
    print(f"\nUsing {num_workers} parallel browser(s)")
    if use_streaming:
        print("Streaming mode enabled")
    print("\nInitializing...\n")
    
    driver = setup_driver(headless=True)
    all_jobs_data = []
    filename = None
    total_processed = 0
    filtered_count = 0
    
    try:
        # Navigate to search page
        search_url = build_search_url(sort_by_date=sort_by_date)
        print(f"Navigating to: {search_url}\n")
        driver.get(search_url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(2)
        
        # Get total jobs available
        total_jobs = get_total_jobs(driver)
        print(f"\nTotal ICT jobs available: {total_jobs}")
        
        if total_jobs == 0:
            print("\nWARNING: Could not detect jobs on the page.")
            print("The browser window is open - please check if:")
            print("  1. The page loaded correctly")
            print("  2. There's a CAPTCHA or bot detection")
            print("  3. The URL is correct")
            print("\nPress Enter to continue with link extraction anyway, or Ctrl+C to quit...")
            input()
            total_jobs = 9999
        
        # Get job range from user
        start_job, end_job = get_job_range(total_jobs)
        
        # Create filename
        filename = create_filename()
        
        google_status = "ON" if ENABLE_GOOGLE_ENRICHMENT else "OFF"
        print(f"\nFiltering: recruitment companies, contract/temp, large companies (1000+ employees)")
        print(f"Google Business enrichment: {google_status}\n")
        
        if use_streaming:
            print("Starting streaming scrape (links processed as found)...\n")
            all_jobs_data, all_job_links = scrape_jobs_streaming(
                driver, start_job, end_job, num_workers, filename, sort_by_date=sort_by_date
            )
            
            total_processed = len(all_job_links)
            filtered_count = total_processed - len(all_jobs_data)
        else:
            all_job_links = collect_job_links(driver, end_job, start_page=1, sort_by_date=sort_by_date)
            print(f"\nTotal job links collected: {len(all_job_links)}")
            
            if len(all_job_links) == 0:
                print("\nNo jobs found. Exiting.")
                driver.quit()
                return
            
            # Filter to requested range
            all_job_links = filter_job_range(all_job_links, start_job, end_job)
            print(f"Selected range: {len(all_job_links)} jobs (from job {start_job} to job {min(end_job, start_job + len(all_job_links) - 1)})")
            
            driver.quit()
            
            print(f"\nScraping {len(all_job_links)} jobs using {num_workers} parallel browsers...")
            
            total_processed = len(all_job_links)
            all_jobs_data = scrape_jobs_in_parallel(all_job_links, start_job, num_workers, filename)
            filtered_count = total_processed - len(all_jobs_data)
        
        # Save final results
        if all_jobs_data:
            df = save_to_excel(all_jobs_data, filename)
            print_statistics(df, filename, total_processed, filtered_count)
        else:
            print_statistics(None, None, total_processed, filtered_count)
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Shutting down all browsers...")
        cleanup_all_browsers()
        print("All browsers terminated.")
        print(f"\nAttempting to save {len(all_jobs_data)} jobs collected so far...")
        if all_jobs_data and filename:
            try:
                df = save_to_excel(all_jobs_data, filename)
                print(f"\nPartial data saved to: {filename}")
                print(f"Jobs saved: {len(all_jobs_data)}")
            except Exception as e:
                print(f"Error saving partial data: {e}")
        elif filename:
            import os
            if os.path.exists(filename):
                print(f"\nCheckpoint file already exists: {filename}")
                print(f"Data was saved during the last checkpoint (every {CHECKPOINT_INTERVAL} jobs)")
                try:
                    import pandas as pd
                    df_check = pd.read_excel(filename)
                    print(f"Jobs in checkpoint: {len(df_check)}")
                except:
                    pass
            else:
                print("\nNo data collected yet in this session.")
        else:
            print("\nNo data to save (scraping hadn't started yet)")
        sys.exit(0)
    
    except Exception as e:
        print(f"\nError during scraping: {e}")
        if all_jobs_data and filename:
            print(f"Attempting to save {len(all_jobs_data)} jobs before exit...")
            try:
                df = save_to_excel(all_jobs_data, filename)
                print(f"Partial data saved to: {filename}")
            except:
                pass
        raise

if __name__ == "__main__":
    main()
