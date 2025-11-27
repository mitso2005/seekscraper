"""Scrape jobs from specific companies."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.company_search import search_multiple_companies_parallel
from scraper.streaming_parallel_scraper import scrape_job_parallel, phone_cache
from scraper.config import (
    COLUMNS, GOV_COMPANIES, CLASSIFICATION, LOCATION,
    DEFAULT_WORKERS, ENABLE_GOOGLE_ENRICHMENT
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import re


def company_names_match(scraped_company, expected_company, threshold=0.6):
    """
    Check if scraped company name matches expected company name.
    Uses fuzzy matching to handle variations.
    
    Args:
        scraped_company: Company name from scraped job
        expected_company: Company name we're searching for
        threshold: Minimum similarity ratio (0-1)
    
    Returns:
        True if names match closely enough
    """
    if not scraped_company or scraped_company == 'N/A':
        return False
    
    # Normalize both names (lowercase, remove special chars)
    def normalize(text):
        # Remove parentheses and contents
        text = re.sub(r'\([^)]*\)', '', text)
        # Keep only alphanumeric and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Collapse whitespace
        text = ' '.join(text.split())
        return text.lower().strip()
    
    scraped_norm = normalize(scraped_company)
    expected_norm = normalize(expected_company)
    
    # Exact match after normalization
    if scraped_norm == expected_norm:
        return True
    
    # Check if one contains the other (for cases like "Department of X" vs "X")
    if expected_norm in scraped_norm or scraped_norm in expected_norm:
        # But make sure it's a substantial match (not just "the" or "of")
        shorter = min(len(expected_norm), len(scraped_norm))
        if shorter >= 10:  # Require at least 10 chars overlap
            return True
    
    # Simple similarity: count matching words
    scraped_words = set(scraped_norm.split())
    expected_words = set(expected_norm.split())
    
    # Remove common words that don't help identify the company
    common_words = {'the', 'of', 'and', 'for', 'in', 'victoria', 'victorian', 'department', 'office'}
    scraped_words -= common_words
    expected_words -= common_words
    
    if not expected_words:  # If no meaningful words left, can't match
        return False
    
    # Calculate word overlap ratio
    intersection = scraped_words & expected_words
    union = scraped_words | expected_words
    
    if not union:
        return False
    
    similarity = len(intersection) / len(union)
    
    return similarity >= threshold


def scrape_company_jobs(companies=None, scrape_workers=None, search_workers=None, max_jobs_per_company=5, output_file=None):
    """
    Scrape jobs from specific companies.
    
    Args:
        companies: List of company names to search (default: GOV_COMPANIES from config)
        scrape_workers: Number of parallel workers for scraping jobs (default: from config)
        search_workers: Number of parallel workers for searching companies (default: from config)
        max_jobs_per_company: Maximum jobs to scrape per company (default: 5, use None for unlimited)
        output_file: Output Excel filename (default: data/vic_gov_ict_jobs.xlsx)
    """
    # Set default output file
    if output_file is None:
        os.makedirs("data", exist_ok=True)
        output_file = os.path.join("data", "vic_gov_ict_jobs.xlsx")
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
    print(f"Google Business enrichment: {google_status}")
    print(f"Filtering: recruitment companies, contract/temp, large companies (1000+ employees)")
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
    skipped_jobs = 0
    
    for company, jobs in company_jobs.items():
        # Limit jobs per company if specified
        if max_jobs_per_company and len(jobs) > max_jobs_per_company:
            jobs_to_scrape = jobs[:max_jobs_per_company]
            skipped_jobs += len(jobs) - max_jobs_per_company
        else:
            jobs_to_scrape = jobs
        
        for job_url in jobs_to_scrape:
            all_jobs.append(job_url)
            job_to_company[job_url] = company
    
    if skipped_jobs > 0:
        print(f"\nLimiting to top {max_jobs_per_company} jobs per company (skipped {skipped_jobs} jobs)")
    
    if not all_jobs:
        print("\nNo jobs found!")
        return
    
    print(f"\n{'=' * 60}")
    print(f"SCRAPING {len(all_jobs)} JOBS")
    print(f"{'=' * 60}")
    print(f"Scrape Workers: {scrape_workers}")
    if max_jobs_per_company:
        print(f"Max per company: {max_jobs_per_company}")
    print(f"Output: {output_file}\n")
    
    # Step 2: Scrape jobs in parallel (with filtering)
    results = []
    completed = 0
    filtered_count = 0
    company_mismatch_count = 0
    company_job_counts = {}  # Track valid jobs per company
    
    with ThreadPoolExecutor(max_workers=scrape_workers) as executor:
        futures = {
            executor.submit(scrape_job_parallel, url, i+1, len(all_jobs), headless=True): url
            for i, url in enumerate(all_jobs)
        }
        
        for future in as_completed(futures):
            job_url = futures[future]
            expected_company = job_to_company[job_url]
            
            try:
                job_data = future.result()
                if job_data:
                    # Verify the company name matches what we searched for
                    scraped_company = job_data.get('company', '')
                    if company_names_match(scraped_company, expected_company):
                        results.append(job_data)
                        # Track count per company
                        company_job_counts[expected_company] = company_job_counts.get(expected_company, 0) + 1
                    else:
                        company_mismatch_count += 1
                        filtered_count += 1
                else:
                    filtered_count += 1
                
                completed += 1
                
                # Progress update
                if completed % 10 == 0 or completed == len(all_jobs):
                    print(f"  Progress: {completed}/{len(all_jobs)} ({completed/len(all_jobs)*100:.1f}%) | Valid: {len(results)} | Filtered: {filtered_count}")
                    
            except Exception as e:
                print(f"  ✗ Failed to scrape job: {e}")
    
    print(f"\n{'=' * 60}")
    print("SAVING RESULTS")
    print(f"{'=' * 60}\n")
    
    if results:
        df = pd.DataFrame(results, columns=COLUMNS)
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"Saved {len(results)} jobs to {output_file}")
        print(f"Filtered out: {filtered_count} jobs")
        print(f"   - Recruitment/contract/temp/large: {filtered_count - company_mismatch_count}")
        print(f"   - Company name mismatches: {company_mismatch_count}")
        
        stats = phone_cache.get_stats()
        print(f"Phone cache: {stats['with_phone']}/{stats['total_companies']} companies have phone numbers")
        
        print(f"\nJobs by Company:")
        company_counts = {}
        for job in results:
            company = job.get('company', 'Unknown')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {company}: {count} jobs")
    else:
        print(f"No valid jobs scraped!")
        if filtered_count > 0:
            print(f"All {filtered_count} jobs were filtered out (recruitment/contract/temp/large companies)")


if __name__ == "__main__":
    scrape_company_jobs(
        max_jobs_per_company=5
    )
