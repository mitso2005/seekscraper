"""Page parsing logic for Seek website."""

import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .config import ELEMENT_WAIT_TIMEOUT, PAGINATION_SCROLL


def get_total_jobs(driver):
    """Extract and return the total number of job postings available."""
    try:
        time.sleep(1)
        
        # Try multiple selectors for job count
        selectors = [
            '[data-automation="totalJobsCount"]',
            'span[data-automation="totalJobsCount"]',
            '.yvsb870',
            'strong[data-automation="totalJobsCount"]'
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                total_text = element.text.replace(',', '').strip()
                if total_text.isdigit():
                    return int(total_text)
            except:
                continue
        
        # Fallback: regex search in page source
        page_source = driver.page_source
        match = re.search(r'(\d{1,3}(?:,?\d{3})*)\s*(?:jobs?|results?)', page_source, re.IGNORECASE)
        if match:
            count_text = match.group(1).replace(',', '')
            print(f"Found job count via regex: {count_text}")
            return int(count_text)
        
        driver.save_screenshot("debug_screenshot.png")
        print("Could not find job count. Screenshot saved to debug_screenshot.png")
        return 0
        
    except Exception as e:
        print(f"Error while extracting job count: {e}")
        driver.save_screenshot("error_screenshot.png")
        return 0


def get_job_links_on_page(driver):
    """Extract all job links from the current page."""
    job_links = []
    try:
        time.sleep(0.5)
        
        selectors = [
            'a[data-automation="jobTitle"]',
            '[data-automation="jobTitle"]',
            'a[data-card-tracking-control="true"]',
            'article a[href*="/job/"]'
        ]
        
        for selector in selectors:
            try:
                job_cards = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if job_cards:
                    for card in job_cards:
                        try:
                            link = card.get_attribute('href')
                            if link and '/job/' in link:
                                job_links.append(link)
                        except:
                            continue
                    if job_links:
                        return job_links
            except:
                continue
        
        return job_links
    except Exception as e:
        print(f"Error retrieving job links: {e}")
        return []


def click_next_page(driver):
    """Click the next page button. Returns True if successful, False otherwise."""
    try:
        # Scroll to bottom to ensure pagination is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(PAGINATION_SCROLL)
        
        # Try multiple selectors for the next button
        next_selectors = [
            'a[data-automation="page-next"]',
            '[data-automation="page-next"]',
            'a[aria-label="Next"]',
            'nav[aria-label="pagination"] a:last-child'
        ]
        
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Check if button is not disabled
                if next_button.get_attribute('aria-disabled') == 'true':
                    return False
                
                # Click using JavaScript to avoid interception issues
                driver.execute_script("arguments[0].click();", next_button)
                
                # Wait for page to transition or stabilize
                time.sleep(PAGINATION_SCROLL * 1.5)
                
                # Extra safety: wait for job links to be visible or at least page to respond
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article'))
                    )
                except:
                    # Page might not have articles, but that's okay - we tried
                    pass
                
                return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"  Error clicking next page: {e}")
        return False
