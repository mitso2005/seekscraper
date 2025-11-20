"""Job link collection from search results."""

from .page_parser import get_job_links_on_page, click_next_page
from .url_builder import build_search_url
from .config import MAX_PAGES
import time


def collect_job_links(driver, end_job, start_page=1, sort_by_date=False, end_page=None):
    """
    Collect job links from search result pages.
    
    Supports two strategies:
    - Job-based (legacy): Collect until reaching end_job position (sequential clicking)
    - Page-based (new): Navigate directly to start_page and collect until end_page
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links (used in job-based mode)
        start_page: Page number to start from (default: 1). Use for page-based collection.
        sort_by_date: Sort by listing date when navigating (default: False)
        end_page: Page number to stop at (inclusive). If None, uses end_job as link count threshold.
    
    Returns:
        List of job URLs
    """
    all_job_links = []
    page_num = start_page
    
    print("\nCollecting job links from search results...")
    if start_page > 1:
        print(f"  Starting from page {start_page} (page-based search strategy)")
    if end_page is not None:
        print(f"  Will collect through page {end_page}")
    
    # If start_page > 1, navigate directly to that page
    if start_page > 1:
        start_url = build_search_url(sort_by_date=sort_by_date, page=start_page)
        print(f"  Navigating to: {start_url}")
        driver.get(start_url)
        time.sleep(1)
    
    while True:
        # Check if we've reached the end page (if specified for page-based search)
        if end_page is not None and page_num > end_page:
            print(f"  Reached end page {end_page}.")
            break
        
        # Check if we've collected enough jobs (legacy job-based mode)
        if end_page is None and len(all_job_links) >= end_job:
            print(f"  Collected enough jobs to cover range (up to job {end_job}).")
            break
        
        print(f"  Scraping page {page_num}... (collected {len(all_job_links)} links so far)")
        links = get_job_links_on_page(driver)
        
        if not links:
            print(f"  No links found on page {page_num}")
            if page_num == start_page:  # Changed from checking page_num == 1
                print("\n⚠️  No job links found on starting page. Check debug_screenshot.png")
                driver.save_screenshot("debug_first_page.png")
                break
            # For page-based search, if we haven't reached end_page yet, try direct navigation
            elif end_page is not None and page_num < end_page:
                print(f"  ⚠️  No links on page {page_num}, but target is page {end_page}. Attempting direct navigation...")
                next_page_num = page_num + 1
                try:
                    fallback_url = build_search_url(sort_by_date=False, page=next_page_num)
                    print(f"  Attempting direct navigation to page {next_page_num}...")
                    driver.get(fallback_url)
                    time.sleep(1)
                    page_num = next_page_num
                    continue
                except Exception as e:
                    print(f"  Direct navigation failed: {e}")
            break
        
        all_job_links.extend(links)
        
        # Remove duplicates while preserving order
        all_job_links = list(dict.fromkeys(all_job_links))
        
        # Try to go to next page
        next_page_clicked = click_next_page(driver)
        if not next_page_clicked:
            # For page-based search, check if we've reached our target page yet
            if end_page is not None and page_num < end_page:
                print(f"  ⚠️  Failed to click next page, but target is page {end_page}. Attempting direct navigation...")
                # Try direct URL navigation as fallback
                next_page_num = page_num + 1
                if next_page_num <= end_page:
                    try:
                        fallback_url = build_search_url(sort_by_date=False, page=next_page_num)
                        print(f"  Attempting direct navigation to page {next_page_num}...")
                        driver.get(fallback_url)
                        time.sleep(1)
                        page_num = next_page_num
                        continue
                    except Exception as e:
                        print(f"  Direct navigation failed: {e}")
            
            print("  No more pages available.")
            break
        
        page_num += 1
        
        # Absolute safety limit
        if page_num > start_page + MAX_PAGES:
            print(f"  Reached absolute page limit ({MAX_PAGES} pages from start).")
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
