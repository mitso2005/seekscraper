"""Search for jobs from specific companies."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from .driver_setup import setup_driver
import time


def build_company_search_url(company_name, location="Melbourne", classification="Information & Communication Technology"):
    """
    Build SEEK URL for company-specific job search.
    
    Args:
        company_name: Company name to search for
        location: Location filter (default: Melbourne)
        classification: Job category (default: ICT)
    
    Returns:
        URL string
    """
    base_url = "https://www.seek.com.au/jobs"
    params = []
    
    # Add classification
    if classification:
        params.append(f"classification={quote_plus(classification)}")
    
    # Add location
    if location:
        params.append(f"where={quote_plus(location)}")
    
    # Add company (advertiser)
    params.append(f"advertiser={quote_plus(company_name)}")
    
    url = f"{base_url}?{'&'.join(params)}"
    return url


def get_company_job_links(driver, company_name, location="Melbourne"):
    """
    Get all job links for a specific company.
    
    Args:
        driver: Selenium WebDriver
        company_name: Company to search for
        location: Location filter
    
    Returns:
        List of job URLs
    """
    url = build_company_search_url(company_name, location)
    driver.get(url)
    time.sleep(2)
    
    job_links = []
    
    try:
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


def search_company_with_driver(company_name, location="Melbourne", headless=True):
    """
    Search a single company with its own driver instance (for parallel execution).
    
    Args:
        company_name: Company to search for
        location: Location filter
        headless: Run browser in headless mode
    
    Returns:
        Tuple of (company_name, job_links)
    """
    driver = None
    try:
        driver = setup_driver(headless=headless)
        job_links = get_company_job_links(driver, company_name, location)
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


def search_multiple_companies(driver, company_list, location="Melbourne"):
    """
    Search jobs for multiple companies (sequential, single driver).
    
    Args:
        driver: Selenium WebDriver
        company_list: List of company names
        location: Location filter
    
    Returns:
        Dict mapping company names to job URLs
    """
    results = {}
    
    print(f"\n🔍 Searching {len(company_list)} companies in {location}...\n")
    
    for i, company in enumerate(company_list, 1):
        print(f"[{i}/{len(company_list)}] Searching: {company}")
        job_links = get_company_job_links(driver, company, location)
        results[company] = job_links
        time.sleep(1)  # Rate limiting
    
    total_jobs = sum(len(jobs) for jobs in results.values())
    print(f"\n✅ Total jobs found: {total_jobs}")
    
    return results


def search_multiple_companies_parallel(company_list, location="Melbourne", num_workers=5, headless=True):
    """
    Search jobs for multiple companies in parallel (each with own headless browser).
    
    Args:
        company_list: List of company names
        location: Location filter
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
            executor.submit(search_company_with_driver, company, location, headless): company
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
