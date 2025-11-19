"""
Seek Web Scraper - ICT Jobs in All Melbourne VIC

This scraper collects job postings from Seek for Information & Communication Technology
roles in the Melbourne area, extracting detailed information including contact details.
"""

import time
from scraper.driver_setup import setup_driver
from scraper.url_builder import build_search_url
from scraper.page_parser import get_total_jobs
from scraper.link_collector import collect_job_links, filter_job_range
from scraper.parallel_scraper import scrape_jobs_in_parallel
from scraper.user_input import get_sort_preference, get_parallel_workers, get_job_range
from scraper.data_export import create_filename, save_to_excel, print_statistics, save_partial_data
from scraper.config import ENABLE_GOOGLE_ENRICHMENT

def main():
    """Main execution function."""
    print("=" * 60)
    print("SEEK Web Scraper - ICT Jobs in All Melbourne VIC")
    print("=" * 60)
    print("\nNOTE: This scraper is for educational purposes only.")
    
    # Get user preferences
    sort_by_date = get_sort_preference()
    num_workers = get_parallel_workers()
    
    print(f"\n⚡ Using {num_workers} parallel browser(s) for faster scraping!")
    print("\nInitializing...\n")
    
    driver = setup_driver(headless=True)
    all_jobs_data = []
    
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
        print(f"\n📊 Total ICT jobs available: {total_jobs}")
        
        if total_jobs == 0:
            print("\n⚠️  Could not detect jobs on the page.")
            print("The browser window is open - please check if:")
            print("  1. The page loaded correctly")
            print("  2. There's a CAPTCHA or bot detection")
            print("  3. The URL is correct")
            print("\nPress Enter to continue with link extraction anyway, or Ctrl+C to quit...")
            input()
            total_jobs = 9999  # Fallback
        
        # Get job range from user
        start_job, end_job = get_job_range(total_jobs)
        
        # Collect job links
        all_job_links = collect_job_links(driver, end_job)
        print(f"\nTotal job links collected: {len(all_job_links)}")
        
        if len(all_job_links) == 0:
            print("\n❌ No jobs found. Exiting.")
            driver.quit()
            return
        
        # Filter to requested range
        all_job_links = filter_job_range(all_job_links, start_job, end_job)
        print(f"Selected range: {len(all_job_links)} jobs (from job {start_job} to job {min(end_job, start_job + len(all_job_links) - 1)})")
        
        # Close initial driver
        driver.quit()
        
        # Create filename
        filename = create_filename()
        
        # Scrape jobs in parallel
        print(f"\n⚡ Scraping {len(all_job_links)} jobs using {num_workers} parallel browser(s)...")
        print("(Much faster with parallel processing!)")
        
        google_status = "ON" if ENABLE_GOOGLE_ENRICHMENT else "OFF"
        print(f"🚫 Filtering: recruitment companies + contract/temp + large companies (1000+ employees)...")
        print(f"📞 Google Business enrichment: {google_status}\n")
        
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
        print("\n\n⚠️  Scraping interrupted by user.")
        save_partial_data(all_jobs_data, interrupted=True)
    
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        save_partial_data(all_jobs_data, interrupted=False)
        raise

if __name__ == "__main__":
    main()
