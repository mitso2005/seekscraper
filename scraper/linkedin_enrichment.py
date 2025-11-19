"""LinkedIn enrichment for finding hiring contacts."""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def search_linkedin_hiring_contacts(driver, company_name, job_title='', max_contacts=3):
    """
    Search LinkedIn for likely hiring managers/recruiters for a role.
    
    Args:
        driver: Selenium WebDriver instance
        company_name: Name of the company
        job_title: Optional job title to refine search
        max_contacts: Maximum number of contacts to return (default 3)
    
    Returns:
        list: List of dictionaries with contact info [{'name': 'John Smith', 'title': 'Talent Acquisition Manager'}, ...]
    """
    contacts = []
    
    # Debug flag - set to True to see what's happening
    DEBUG = True  # Temporarily enabled to diagnose issue
    
    try:
        # Determine search keywords based on job title
        department = extract_department_from_title(job_title)
        
        # Construct LinkedIn search query
        # Example: "Google recruiter technology" or "Google talent acquisition"
        query = f"{company_name} site:linkedin.com/in/ "
        
        # Add role-specific terms
        search_terms = []
        if department:
            search_terms.append(f"{department} manager")
            search_terms.append(f"{department} lead")
        
        # Always add general recruiting terms
        search_terms.extend([
            "recruiter",
            "talent acquisition",
            "hiring manager",
            "people & culture"
        ])
        
        # Try each search term
        for term_idx, term in enumerate(search_terms[:4]):  # Try up to 4 terms
            # First try with Melbourne, then without if no results
            queries_to_try = [
                f"{company_name} {term} Melbourne site:linkedin.com/in/",
                f"{company_name} {term} site:linkedin.com/in/"  # Fallback without location
            ]
            
            for query_with_term in queries_to_try:
                if DEBUG:
                    print(f"    LinkedIn search: {query_with_term}")
                
                # Navigate to Google
                driver.get("https://www.google.com")
                time.sleep(0.5)
                
                try:
                    search_box = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.NAME, "q"))
                    )
                    search_box.clear()
                    search_box.send_keys(query_with_term)
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(1.5)
                except:
                    continue
                
                # Extract LinkedIn profile links and names from search results
                found_contacts = extract_contacts_from_google_results(driver, company_name)
                
                if DEBUG:
                    print(f"      Found {len(found_contacts)} contacts from this search")
                
                # Add new contacts (avoid duplicates)
                for contact in found_contacts:
                    if contact and contact.get('name') and contact not in contacts:
                        contacts.append(contact)
                        if len(contacts) >= max_contacts:
                            return contacts[:max_contacts]
                
                # If we found contacts, don't try the fallback query
                if found_contacts:
                    break
                
                # Small delay between searches
                time.sleep(0.5)
        
    except Exception as e:
        print(f"    LinkedIn search error for {company_name}: {e}")
    
    return contacts[:max_contacts]


def extract_department_from_title(job_title):
    """Extract department/field from job title."""
    if not job_title or job_title == 'N/A':
        return ''
    
    title_lower = job_title.lower()
    
    # Common department mappings
    departments = {
        'technology': ['developer', 'engineer', 'programmer', 'software', 'devops', 'tech', 'it', 'data', 'cloud'],
        'sales': ['sales', 'account', 'business development', 'bd'],
        'marketing': ['marketing', 'digital', 'content', 'social media'],
        'finance': ['finance', 'accounting', 'accountant', 'financial'],
        'hr': ['hr', 'human resources', 'people'],
        'operations': ['operations', 'project manager', 'program manager'],
        'design': ['designer', 'ux', 'ui', 'creative'],
    }
    
    for dept, keywords in departments.items():
        if any(keyword in title_lower for keyword in keywords):
            return dept
    
    return ''


def extract_contacts_from_google_results(driver, company_name):
    """Extract contact names and titles from Google search results."""
    contacts = []
    
    DEBUG = True  # Match parent function
    
    try:
        # Find all search result divs
        result_selectors = [
            'div.g',  # Standard Google result
            'div[data-hveid]',  # Alternative selector
        ]
        
        results = []
        for selector in result_selectors:
            try:
                results = driver.find_elements(By.CSS_SELECTOR, selector)
                if results:
                    if DEBUG:
                        print(f"      Found {len(results)} Google results with selector: {selector}")
                    break
            except:
                continue
        
        if DEBUG and not results:
            print(f"      WARNING: No Google results found!")
        
        for result in results[:10]:  # Check top 10 results
            try:
                text = result.text
                
                # Look for LinkedIn profile patterns
                # Example: "John Smith - Talent Acquisition Manager - Google | LinkedIn"
                # Example: "Jane Doe - Senior Recruiter at Google - LinkedIn"
                # Note: parse_linkedin_result will validate location (prefer Melbourne, allow unknown)
                
                if 'linkedin' in text.lower():
                    # Extract name and title
                    contact = parse_linkedin_result(text, company_name)
                    if contact:
                        if DEBUG:
                            print(f"        ✓ Extracted contact: {contact['name']} - {contact['title']}")
                        contacts.append(contact)
                    elif DEBUG:
                        print(f"        ✗ Failed to parse LinkedIn result")
                        
            except:
                continue
                
    except Exception as e:
        pass
    
    return contacts


def parse_linkedin_result(text, company_name):
    """Parse a LinkedIn search result to extract name and title."""
    try:
        lines = text.split('\n')
        
        # Check if this profile mentions other Australian cities (exclude those)
        text_lower = text.lower()
        
        # Only exclude if explicitly mentions OTHER states/cities
        other_locations = ['sydney', 'brisbane', 'perth', 'adelaide', 'canberra']
        # Skip only if these are mentioned AND Melbourne is NOT mentioned
        has_melbourne = 'melbourne' in text_lower or 'victoria' in text_lower or ' vic' in text_lower
        has_other_city = any(city in text_lower for city in other_locations)
        
        # Only reject if has other city and definitely NOT Melbourne
        if has_other_city and not has_melbourne:
            return None
        
        for i, line in enumerate(lines):
            # Look for name patterns (usually first line with person's name)
            # Common patterns:
            # "John Smith - Talent Acquisition Manager - Google"
            # "Jane Doe | Recruiter at Google | LinkedIn"
            
            if '-' in line or '|' in line or '·' in line:
                # Split by common separators
                parts = re.split(r'[-|·•]', line)
                parts = [p.strip() for p in parts if p.strip()]
                
                # First part is usually the name
                if parts and len(parts) >= 1:
                    potential_name = parts[0]
                    potential_title = parts[1] if len(parts) > 1 else ''
                    
                    # Validate it looks like a name
                    if is_valid_name(potential_name):
                        # More lenient - accept any title or no title
                        # Prefer titles with relevant keywords but don't require them
                        title_lower = potential_title.lower()
                        has_relevant_keyword = any(keyword in title_lower for keyword in 
                            ['recruit', 'talent', 'hr', 'people', 'manager', 'lead', 'head', 'director', 'specialist'])
                        
                        # Return if has relevant keyword OR if first 3 lines (likely important)
                        if has_relevant_keyword or i < 3:
                            return {
                                'name': potential_name,
                                'title': potential_title
                            }
        
        # More aggressive fallback: look for any two capitalized words together
        for line in lines[:5]:  # Check first 5 lines only
            words = line.split()
            for i in range(len(words) - 1):
                potential_name = f"{words[i]} {words[i+1]}"
                if is_valid_name(potential_name):
                    return {
                        'name': potential_name,
                        'title': ''
                    }
                        
    except:
        pass
    
    return None


def is_valid_name(text):
    """Check if text looks like a person's name."""
    if not text or len(text) < 4 or len(text) > 60:
        return False
    
    # Should have 2-5 words
    words = text.split()
    if len(words) < 2 or len(words) > 5:
        return False
    
    # At least the first word should start with capital letter
    if not words[0][0].isupper():
        return False
    
    # Shouldn't contain common non-name words
    excluded_words = ['linkedin', 'profile', 'view', 'australia', 'company', 'about', 'search', 'people', 'jobs']
    text_lower = text.lower()
    if any(excluded in text_lower for excluded in excluded_words):
        return False
    
    return True


def format_contacts_for_excel(contacts):
    """Format contacts list into separate columns for Excel."""
    result = {}
    
    for i in range(3):  # Always return 3 contact slots
        if i < len(contacts):
            result[f'contact_{i+1}_name'] = contacts[i].get('name', '')
            result[f'contact_{i+1}_title'] = contacts[i].get('title', '')
        else:
            result[f'contact_{i+1}_name'] = ''
            result[f'contact_{i+1}_title'] = ''
    
    return result
