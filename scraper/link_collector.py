"""Job link collection from search results."""

from .page_parser import get_job_links_on_page, click_next_page
from .config import MAX_PAGES


def collect_job_links(driver, end_job):
    """
    Collect job links from search result pages.
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links
    
    Returns:
        List of job URLs
    """
    all_job_links = []
    page_num = 1
    
    print("\nCollecting job links from search results...")
    
    while True:
        # Check if we've collected enough jobs
        if len(all_job_links) >= end_job:
            print(f"  Collected enough jobs to cover range (up to job {end_job}).")
            break
        
        print(f"  Scraping page {page_num}... (collected {len(all_job_links)} links so far)")
        links = get_job_links_on_page(driver)
        
        if not links:
            print(f"  No links found on page {page_num}")
            if page_num == 1:
                print("\n⚠️  No job links found on first page. Check debug_screenshot.png")
                driver.save_screenshot("debug_first_page.png")
            break
        
        all_job_links.extend(links)
        
        # Remove duplicates while preserving order
        all_job_links = list(dict.fromkeys(all_job_links))
        
        # Try to go to next page
        if not click_next_page(driver):
            print("  No more pages available.")
            break
        
        page_num += 1
        
        # Absolute safety limit
        if page_num > MAX_PAGES:
            print(f"  Reached absolute page limit ({MAX_PAGES} pages).")
            break
    
    return all_job_links


def filter_job_range(job_links, start_job, end_job):
    """
    Filter job links to the requested range.
    
    Args:
        job_links: List of all job URLs
        start_job: Start job number (1-indexed)
        end_job: End job number (inclusive)
    
    Returns:
        Filtered list of job URLs
    """
    if end_job < len(job_links):
        return job_links[start_job-1:end_job]
    elif start_job > 1:
        return job_links[start_job-1:]
    return job_links
