"""Google Business enrichment for company phone numbers."""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def search_google_business_phone(driver, company_name, location=''):
    """
    Search Google for company phone number via Google Business listing.
    
    Args:
        driver: Selenium WebDriver instance
        company_name: Name of the company
        location: Optional location to refine search (e.g., 'Melbourne')
    
    Returns:
        str: Phone number if found, empty string otherwise
    """
    try:
        # Construct search query
        query = f"{company_name}"
        if location:
            # Extract city from location string (e.g., "Melbourne VIC" -> "Melbourne")
            city = location.split()[0] if location else ''
            query += f" {city}"
        query += " phone number"
        
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(0.5)  # Reduced from 1 second
        
        # Find search box and enter query
        try:
            search_box = WebDriverWait(driver, 3).until(  # Reduced from 5 seconds
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(1.5)  # Reduced from 2 seconds
        except:
            return ''
        
        # Try to find phone number in Google Business card (knowledge panel)
        phone_selectors = [
            # Google Business phone number in knowledge panel
            'span[data-dtype="d3ph"]',
            'a[data-dtype="d3ph"]',
            # Alternative selectors for phone numbers
            'span.LrzXr',
            'div.LrzXr',
            # Phone in business info
            '[jsname="ZwRAXe"]',
            # Sometimes shown as clickable link
            'a[href^="tel:"]',
        ]
        
        for selector in phone_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and is_valid_phone_format(text):
                        return clean_phone_number(text)
                    
                    # Check href attribute for tel: links
                    href = element.get_attribute('href')
                    if href and href.startswith('tel:'):
                        phone = href.replace('tel:', '').strip()
                        if is_valid_phone_format(phone):
                            return clean_phone_number(phone)
            except:
                continue
        
        # Try to extract from general page text as fallback
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            phone = extract_phone_from_text(page_text)
            if phone:
                return phone
        except:
            pass
            
    except Exception as e:
        print(f"Error searching Google Business for {company_name}: {e}")
    
    return ''


def is_valid_phone_format(text):
    """Check if text looks like an Australian phone number."""
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', text)
    
    # Check for Australian patterns
    patterns = [
        r'^(\+61|0)[2-478]\d{8}$',  # Landline
        r'^(\+61|0)4\d{8}$',         # Mobile
        r'^1[38]00\d{6}$',           # Toll-free
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False


def clean_phone_number(phone):
    """Clean and format phone number."""
    # Remove extra whitespace
    phone = phone.strip()
    
    # Remove common labels
    phone = re.sub(r'^(phone|tel|telephone|call)[:\s]+', '', phone, flags=re.IGNORECASE)
    
    return phone


def extract_phone_from_text(text):
    """Extract Australian phone number from general text."""
    # Look for Australian phone patterns with formatting
    patterns = [
        r'\+61[\s\-]?[2-478][\s\-]?\d{4}[\s\-]?\d{4}',  # +61 format
        r'\(0[2-8]\)[\s\-]?\d{4}[\s\-]?\d{4}',          # (0X) format
        r'0[2-8][\s\-]\d{4}[\s\-]\d{4}',                # 0X format with spaces
        r'04\d{2}[\s\-]\d{3}[\s\-]\d{3}',               # Mobile
        r'1[38]00[\s\-]\d{3}[\s\-]\d{3}',               # Toll-free
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return clean_phone_number(matches[0])
    
    return ''


def enrich_with_google_phone(all_jobs_data, driver):
    """
    Enrich job data with Google Business phone numbers.
    
    Args:
        all_jobs_data: List of job dictionaries
        driver: Selenium WebDriver instance
    
    Returns:
        List of enriched job dictionaries with 'office_phone' field
    """
    print("\n" + "="*60)
    print("GOOGLE BUSINESS ENRICHMENT")
    print("="*60)
    print("Searching for office phone numbers via Google Business...")
    print(f"Processing {len(all_jobs_data)} companies...\n")
    
    # Track unique companies to avoid duplicate searches
    company_phones = {}
    enriched_count = 0
    
    for idx, job in enumerate(all_jobs_data, 1):
        company = job.get('company', '')
        location = job.get('location', '')
        
        if not company or company == 'N/A':
            job['office_phone'] = ''
            continue
        
        if company in company_phones:
            job['office_phone'] = company_phones[company]
            if company_phones[company]:
                print(f"  [{idx}/{len(all_jobs_data)}] {company}: {company_phones[company]} (cached)")
        else:
            print(f"  [{idx}/{len(all_jobs_data)}] Searching: {company}...", end='')
            phone = search_google_business_phone(driver, company, location)
            
            if phone:
                print(f" Found: {phone}")
                enriched_count += 1
            else:
                print(f" Not found")
            
            company_phones[company] = phone
            job['office_phone'] = phone
            
            time.sleep(3)
    
    print("\n" + "="*60)
    print(f"Enrichment complete!")
    print(f"Office phones found: {enriched_count}/{len(company_phones)} unique companies")
    print("="*60 + "\n")
    
    return all_jobs_data
