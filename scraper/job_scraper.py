"""Job details scraping logic."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .config import BRIEF_PAUSE, ELEMENT_WAIT_TIMEOUT, COLUMNS, RECRUITMENT_COMPANIES
from .extractors import extract_contact_info


def create_empty_job_data(job_url):
    """Create an empty job data dictionary with the given URL."""
    return {
        'job_title': '',
        'company': '',
        'location': '',
        'classification': '',
        'work_type': '',
        'salary': '',
        'time_posted': '',
        'email': '',
        'phone': '',
        'website': '',
        'url': job_url
    }


def extract_text_by_selector(driver, selectors, default=''):
    """Try multiple selectors and return the first successful text extraction."""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            continue
    return default


def extract_job_title(driver):
    """Extract job title from the page."""
    selectors = [
        'h1[data-automation="job-detail-title"]',
        'h1'
    ]
    return extract_text_by_selector(driver, selectors, 'N/A')


def extract_company(driver):
    """Extract company name from the page."""
    selectors = [
        '[data-automation="advertiser-name"]',
        'span[data-automation="job-detail-advertiser"]'
    ]
    return extract_text_by_selector(driver, selectors, 'N/A')


def extract_location(driver):
    """Extract location from the page."""
    selectors = [
        '[data-automation="job-detail-location"]',
        'span[data-automation="job-detail-location"]'
    ]
    return extract_text_by_selector(driver, selectors)


def extract_classification(driver):
    """Extract job classification from the page."""
    selectors = [
        '[data-automation="job-detail-classifications"]',
        'a[data-automation="job-detail-classifications"]'
    ]
    return extract_text_by_selector(driver, selectors)


def extract_work_type(driver):
    """Extract work type from the page."""
    selectors = [
        '[data-automation="job-detail-work-type"]',
        'span[data-automation="job-detail-work-type"]'
    ]
    return extract_text_by_selector(driver, selectors)


def extract_salary(driver):
    """Extract salary information from the page."""
    # Try listed salary first
    selectors = [
        '[data-automation="job-detail-salary"]',
        'span[data-automation="job-detail-salary"]'
    ]
    salary = extract_text_by_selector(driver, selectors)
    
    if salary:
        return salary
    
    # Look for predicted salary range
    try:
        salary_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), 'salary')]")
        for element in salary_elements:
            text = element.text.strip()
            if '$' in text and ('-' in text or 'to' in text.lower()):
                if 'profile' not in text.lower() and 'add' not in text.lower():
                    return text
    except:
        pass
    
    return ''


def extract_time_posted(driver):
    """Extract time posted from the page."""
    try:
        time_elements = driver.find_elements(By.CSS_SELECTOR, '._1i38d6g0.dk7b5050.h9jxny0.h9jxny1.h9jxny1u.h9jxny6._1lwlriv4')
        for element in time_elements:
            text = element.text.strip()
            if text and text.lower().startswith('posted'):
                return text
    except:
        pass
    
    # Fallback
    selectors = ['[data-automation="job-detail-date"]']
    return extract_text_by_selector(driver, selectors)

def extract_contact_details(driver):
    """Extract contact information from job description."""
    try:
        description_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')
        description_text = description_element.text
        return extract_contact_info(description_text)
    except:
        return {'email': '', 'phone': '', 'website': ''}


def is_recruitment_company(company_name):
    """
    Check if the company is a recruitment agency.
    Returns True if company matches any recruitment company (case-insensitive).
    """
    if not company_name or company_name == 'N/A':
        return False
    
    company_lower = company_name.lower().strip()
    
    for recruiter in RECRUITMENT_COMPANIES:
        if recruiter.lower() in company_lower:
            return True
    
    return False


def scrape_job_details(driver, job_url):
    """Scrape all job details from a given job URL."""
    job_data = create_empty_job_data(job_url)
    
    try:
        driver.get(job_url)
        time.sleep(BRIEF_PAUSE)
        
        # Wait for title to ensure page is loaded
        try:
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-automation="job-detail-title"]'))
            )
        except:
            pass
        
        # Extract all fields
        job_data['job_title'] = extract_job_title(driver)
        job_data['company'] = extract_company(driver)
        
        # Check if this is a recruitment company - return None to skip this job
        if is_recruitment_company(job_data['company']):
            return None
        
        job_data['location'] = extract_location(driver)
        job_data['classification'] = extract_classification(driver)
        job_data['work_type'] = extract_work_type(driver)
        job_data['salary'] = extract_salary(driver)
        job_data['time_posted'] = extract_time_posted(driver)
        
        # Extract contact information
        contact_info = extract_contact_details(driver)
        job_data['email'] = contact_info['email']
        job_data['phone'] = contact_info['phone']
        job_data['website'] = contact_info['website']
        
    except Exception as e:
        error_msg = str(e)
        if 'invalid session id' in error_msg.lower() or 'session' in error_msg.lower():
            raise
        else:
            print(f"Error scraping {job_url}: {e}")
    
    return job_data
