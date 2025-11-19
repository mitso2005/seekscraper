"""Streaming link collection that yields links as they're discovered."""

from .page_parser import get_job_links_on_page, click_next_page
from .config import MAX_PAGES


def stream_job_links(driver, end_job):
    """
    Stream job links from search result pages as they're collected.
    Yields links in batches to allow parallel scraping to start immediately.
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links
    
    Yields:
        Batches of job URLs (one batch per page)
    """
    all_collected = []
    page_num = 1
    
    print("\nCollecting job links from search results...")
    
    while True:
        # Check if we've collected enough jobs
        if len(all_collected) >= end_job:
            print(f"  Collected enough jobs to cover range (up to job {end_job}).")
            break
        
        print(f"  Scraping page {page_num}... (collected {len(all_collected)} links so far)")
        links = get_job_links_on_page(driver)
        
        if not links:
            print(f"  No links found on page {page_num}")
            if page_num == 1:
                print("\n⚠️  No job links found on first page. Check debug_screenshot.png")
                driver.save_screenshot("debug_first_page.png")
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
        
        # Try to go to next page
        if not click_next_page(driver):
            print("  No more pages available.")
            break
        
        page_num += 1
        
        # Absolute safety limit
        if page_num > MAX_PAGES:
            print(f"  Reached absolute page limit ({MAX_PAGES} pages).")
            break


def collect_job_links_streaming(driver, end_job):
    """
    Collect all job links using the streaming approach.
    Returns complete list after all pages are processed.
    
    Args:
        driver: Selenium WebDriver instance
        end_job: Stop after collecting this many job links
    
    Returns:
        List of all job URLs collected
    """
    all_links = []
    for batch in stream_job_links(driver, end_job):
        all_links.extend(batch)
    return all_links
