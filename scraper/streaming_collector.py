"""Streaming link collection that yields links as they're discovered."""

from .page_parser import get_job_links_on_page, click_next_page
from .url_builder import build_search_url
from .config import MAX_PAGES
import time


def stream_job_links(driver, end_job, start_page=1, sort_by_date=False, end_page=None):
    """
    Stream job links from search result pages as they're collected.
    Yields links in batches to allow parallel scraping to start immediately.
    
    Supports page-based navigation: directly navigate to start_page instead of clicking
    through all previous pages.
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links (used in job-based mode)
        start_page: Page number to start from (default: 1). Use for page-based collection.
        sort_by_date: Sort by listing date when navigating (default: False)
        end_page: Page number to stop at (inclusive). If None, uses end_job as link count threshold.
    
    Yields:
        Batches of job URLs (one batch per page)
    """
    all_collected = []
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
        if end_page is None and len(all_collected) >= end_job:
            print(f"  Collected enough jobs to cover range (up to job {end_job}).")
            break
        
        print(f"  Scraping page {page_num}... (collected {len(all_collected)} links so far)")
        links = get_job_links_on_page(driver)
        
        if not links:
            print(f"  No links found on page {page_num}")
            if page_num == start_page:
                print("\nWARNING: No job links found on starting page. Check debug_screenshot.png")
                driver.save_screenshot("debug_first_page.png")
                break
            elif end_page is not None and page_num < end_page:
                print(f"  WARNING: No links on page {page_num}, but target is page {end_page}. Attempting direct navigation...")
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
        
        # Remove any duplicates within this batch
        unique_links = []
        for link in links:
            if link not in all_collected:
                unique_links.append(link)
                all_collected.append(link)
        
        # Yield this batch immediately for processing
        if unique_links:
            yield unique_links
        
        next_page_clicked = click_next_page(driver)
        if not next_page_clicked:
            if end_page is not None and page_num < end_page:
                print(f"  WARNING: Failed to click next page, but target is page {end_page}. Attempting direct navigation...")
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


def collect_job_links_streaming(driver, end_job, start_page=1, sort_by_date=False, end_page=None):
    """
    Collect all job links using the streaming approach.
    Returns complete list after all pages are processed.
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links (used in job-based mode)
        start_page: Page number to start from (default: 1)
        sort_by_date: Sort by listing date when navigating (default: False)
        end_page: Page number to stop at (inclusive). If None, uses end_job as link count threshold.
    
    Returns:
        List of all job URLs collected
    """
    all_links = []
    for batch in stream_job_links(driver, end_job, start_page, sort_by_date, end_page):
        all_links.extend(batch)
    return all_links
