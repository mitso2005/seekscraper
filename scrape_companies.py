"""Scrape jobs from specific companies."""

from scraper.company_search import search_multiple_companies_parallel
from scraper.streaming_parallel_scraper import scrape_job_parallel, phone_cache
from scraper.config import (
    COLUMNS, GOV_COMPANIES, CLASSIFICATION, LOCATION,
    DEFAULT_WORKERS, ENABLE_GOOGLE_ENRICHMENT
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd


def scrape_company_jobs(companies=None, scrape_workers=None, search_workers=None, output_file="vic_gov_ict_jobs.xlsx"):
    """
    Scrape jobs from specific companies.
    
    Args:
        companies: List of company names (default: GOV_COMPANIES from config)
        scrape_workers: Number of parallel workers for scraping jobs (default: from config)
        search_workers: Number of parallel workers for searching companies (default: from config)
        output_file: Output Excel filename (default: vic_gov_ict_jobs.xlsx)
    """
    # Use config defaults if not specified
    if companies is None:
        companies = GOV_COMPANIES
    if scrape_workers is None:
        scrape_workers = DEFAULT_WORKERS
    if search_workers is None:
        search_workers = 20  # Use fewer workers for search
    
    # Step 1: Search for jobs from each company (parallel headless)
    print("=" * 60)
    print("🏢 VICTORIAN GOVERNMENT ICT JOB SCRAPER")
    print("=" * 60)
    print(f"Classification: {CLASSIFICATION}")
    print(f"Location: {LOCATION}")
    print(f"Companies: {len(companies)}")
    google_status = "ON" if ENABLE_GOOGLE_ENRICHMENT else "OFF"
    print(f"📞 Google Business enrichment: {google_status}")
    print(f"🚫 Filtering: recruitment companies + contract/temp + large companies (1000+ employees)")
    print()
    
    # Convert LOCATION from "All-Melbourne-VIC" to "Melbourne" for search
    location_search = LOCATION.replace("All-", "").replace("-VIC", "")
    
    company_jobs = search_multiple_companies_parallel(
        companies, 
        location=location_search,
        classification=CLASSIFICATION,
        num_workers=search_workers, 
        headless=True
    )
    
    # Flatten job list and track which company posted each job
    all_jobs = []
    job_to_company = {}
    
    for company, jobs in company_jobs.items():
        for job_url in jobs:
            all_jobs.append(job_url)
            job_to_company[job_url] = company
    
    if not all_jobs:
        print("\n❌ No jobs found!")
        return
    
    print(f"\n{'=' * 60}")
    print(f"⚡ SCRAPING {len(all_jobs)} JOBS")
    print(f"{'=' * 60}")
    print(f"Scrape Workers: {scrape_workers}")
    print(f"Output: {output_file}\n")
    
    # Step 2: Scrape jobs in parallel (with filtering)
    results = []
    completed = 0
    filtered_count = 0
    
    with ThreadPoolExecutor(max_workers=scrape_workers) as executor:
        futures = {
            executor.submit(scrape_job_parallel, url, i+1, len(all_jobs), headless=True): url
            for i, url in enumerate(all_jobs)
        }
        
        for future in as_completed(futures):
            job_url = futures[future]
            try:
                job_data = future.result()
                if job_data:
                    results.append(job_data)
                else:
                    filtered_count += 1
                
                completed += 1
                
                # Progress update
                if completed % 10 == 0 or completed == len(all_jobs):
                    print(f"  Progress: {completed}/{len(all_jobs)} ({completed/len(all_jobs)*100:.1f}%) | Valid: {len(results)} | Filtered: {filtered_count}")
                    
            except Exception as e:
                print(f"  ✗ Failed to scrape job: {e}")
    
    # Step 3: Save results
    print(f"\n{'=' * 60}")
    print("💾 SAVING RESULTS")
    print(f"{'=' * 60}\n")
    
    if results:
        df = pd.DataFrame(results, columns=COLUMNS)
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✅ Saved {len(results)} jobs to {output_file}")
        print(f"🚫 Filtered out: {filtered_count} jobs (recruitment/contract/temp/large companies)")
        
        # Show cache stats
        stats = phone_cache.get_stats()
        print(f"📞 Phone cache: {stats['with_phone']}/{stats['total_companies']} companies have phone numbers")
        
        # Show breakdown by company
        print(f"\n📊 Jobs by Company:")
        company_counts = {}
        for job in results:
            company = job.get('company', 'Unknown')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {company}: {count} jobs")
    else:
        print(f"❌ No valid jobs scraped!")
        if filtered_count > 0:
            print(f"🚫 All {filtered_count} jobs were filtered out (recruitment/contract/temp/large companies)")


if __name__ == "__main__":
    # Scrape Victorian Government ICT jobs in Melbourne
    # Uses GOV_COMPANIES, CLASSIFICATION, and LOCATION from config.py
    scrape_company_jobs(
        # companies=GOV_COMPANIES,  # Default, can be overridden
        # scrape_workers=DEFAULT_WORKERS,  # Default from config
        # search_workers=max(3, DEFAULT_WORKERS // 4),  # Default calculated
        output_file="vic_gov_ict_jobs.xlsx"
    )
