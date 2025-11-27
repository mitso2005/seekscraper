"""Search for jobs from specific companies."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from .driver_setup import setup_driver
import time
import re


def build_company_search_url(company_name, location="Melbourne", classification="information-communication-technology"):
    """
    Build SEEK URL for company-specific job search.
    Uses SEEK's path-based format: /{Company-Name}-jobs-in-{classification}/in-{Location}
    
    Args:
        company_name: Company name to search for
        location: Location filter (default: Melbourne)
        classification: Job category slug (default: information-communication-technology)
    
    Returns:
        URL string
    """
    # Convert company name to URL-safe slug
    # 1. Replace & with 'and'
    company_slug = company_name.replace('&', 'and')
    # 2. Remove parentheses and their contents (e.g., "(AMES Aust)" -> "")
    company_slug = re.sub(r'\([^)]*\)', '', company_slug)
    # 3. Remove special characters except spaces and hyphens
    company_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', company_slug)
    # 4. Replace multiple spaces with single space
    company_slug = re.sub(r'\s+', ' ', company_slug)
    # 5. Strip leading/trailing spaces
    company_slug = company_slug.strip()
    # 6. Replace spaces with hyphens
    company_slug = company_slug.replace(' ', '-')
    # 7. Remove multiple consecutive hyphens
    company_slug = re.sub(r'-+', '-', company_slug)
    # 8. Remove leading/trailing hyphens
    company_slug = company_slug.strip('-')
    
    # Convert location to SEEK format (e.g., "Melbourne" -> "Melbourne-VIC")
    location_slug = f"{location}-VIC" if location and "VIC" not in location else location
    
    # Build URL in SEEK's path format
    # Format: /{Company-Name}-jobs-in-{classification}/in-{Location}
    if classification:
        url = f"https://www.seek.com.au/{company_slug}-jobs-in-{classification}/in-{location_slug}"
    else:
        # If no classification, just company and location
        url = f"https://www.seek.com.au/{company_slug}-jobs/in-{location_slug}"
    
    return url


def get_company_job_links(driver, company_name, location="Melbourne", classification="information-communication-technology"):
    """
    Get all job links for a specific company.
    
    Args:
        driver: Selenium WebDriver
        company_name: Company to search for
        location: Location filter
        classification: Job category slug
    
    Returns:
        List of job URLs
    """
    url = build_company_search_url(company_name, location, classification)
    driver.get(url)
    time.sleep(2)
    
    job_links = []
    
    try:
        # Check if there are any jobs (SEEK shows "0 jobs" message if none found)
        # Try to find the job count or no results message first
        try:
            no_results = driver.find_elements(By.CSS_SELECTOR, "[data-automation='noSearchResults']")
            if no_results:
                print(f"  Found 0 jobs for {company_name}")
                return []
        except:
            pass
        
        # Wait for results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-search-sol-meta]"))
        )
        
        # Get all job links on page
        job_cards = driver.find_elements(By.CSS_SELECTOR, "article[data-card-type='JobCard'] a[data-automation='jobTitle']")
        
        for card in job_cards:
            href = card.get_attribute('href')
            if href and '/job/' in href:
                # Clean URL
                job_url = href.split('?')[0]
                if job_url not in job_links:
                    job_links.append(job_url)
        
        print(f"  Found {len(job_links)} jobs for {company_name}")
        
    except Exception as e:
        print(f"  ⚠️  Error searching {company_name}: {e}")
    
    return job_links


def search_company_with_driver(company_name, location="Melbourne", classification="information-communication-technology", headless=True):
    """
    Search a single company with its own driver instance (for parallel execution).
    
    Args:
        company_name: Company to search for
        location: Location filter
        classification: Job category slug
        headless: Run browser in headless mode
    
    Returns:
        Tuple of (company_name, job_links)
    """
    driver = None
    try:
        driver = setup_driver(headless=headless)
        job_links = get_company_job_links(driver, company_name, location, classification)
        driver.quit()
        return (company_name, job_links)
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"  ✗ Failed to search {company_name}: {e}")
        return (company_name, [])


def search_multiple_companies(driver, company_list, location="Melbourne", classification="information-communication-technology"):
    """
    Search jobs for multiple companies (sequential, single driver).
    
    Args:
        driver: Selenium WebDriver
        company_list: List of company names
        location: Location filter
        classification: Job category slug
    
    Returns:
        Dict mapping company names to job URLs
    """
    results = {}
    
    print(f"\n🔍 Searching {len(company_list)} companies in {location}...\n")
    
    for i, company in enumerate(company_list, 1):
        print(f"[{i}/{len(company_list)}] Searching: {company}")
        job_links = get_company_job_links(driver, company, location, classification)
        results[company] = job_links
        time.sleep(1)  # Rate limiting
    
    total_jobs = sum(len(jobs) for jobs in results.values())
    print(f"\n✅ Total jobs found: {total_jobs}")
    
    return results


def search_multiple_companies_parallel(company_list, location="Melbourne", classification="information-communication-technology", num_workers=5, headless=True):
    """
    Search jobs for multiple companies in parallel (each with own headless browser).
    
    Args:
        company_list: List of company names
        location: Location filter
        classification: Job category slug
        num_workers: Number of parallel browser instances
        headless: Run browsers in headless mode
    
    Returns:
        Dict mapping company names to job URLs
    """
    results = {}
    
    print(f"\n🔍 Searching {len(company_list)} companies in {location} (parallel)...")
    print(f"⚡ Using {num_workers} parallel workers\n")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(search_company_with_driver, company, location, classification, headless): company
            for company in company_list
        }
        
        completed = 0
        for future in as_completed(futures):
            company_name = futures[future]
            try:
                company, job_links = future.result()
                results[company] = job_links
                
                completed += 1
                if completed % 10 == 0 or completed == len(company_list):
                    print(f"  Progress: {completed}/{len(company_list)} companies searched")
                    
            except Exception as e:
                print(f"  ✗ Error with {company_name}: {e}")
                results[company_name] = []
    
    total_jobs = sum(len(jobs) for jobs in results.values())
    print(f"\n✅ Total jobs found: {total_jobs}")
    
    return results
