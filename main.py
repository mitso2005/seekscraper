from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Thread-safe lock for data collection
data_lock = Lock()

def setup_driver(headless=False):
    """Initialize and return a Selenium WebDriver instance."""
    try:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Performance optimizations
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Disable images and CSS for faster loading (comment out if you need to see the page)
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # Disable images
                'stylesheet': 2  # Disable CSS
            },
            'profile.managed_default_content_settings': {
                'images': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver-manager to handle ChromeDriver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute CDP commands to hide webdriver property
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set page load strategy and implicit wait for faster performance
        driver.implicitly_wait(2)  # Reduced from default 10s
        
        return driver
    except Exception as e:
        print(f"Error initializing the WebDriver: {e}")
        exit()

def build_search_url(sort_by_date=False):
    """Build the Seek URL for ICT jobs in All Melbourne VIC."""
    # Seek URL structure for classification and location filters
    # Classification: Information & Communication Technology (ID: 6281)
    # Location: All Melbourne VIC (ID: 3000)
    base_url = "https://www.seek.com.au/information-communication-technology-jobs/in-All-Melbourne-VIC"
    
    # Add sort parameter for newest first
    if sort_by_date:
        base_url += "?sortmode=ListedDate"
    
    return base_url

def get_total_jobs(driver):
    """Extract and return the total number of job postings available."""
    try:
        # Wait for page to fully load
        time.sleep(1)  # Reduced from 3s
        
        # Try multiple selectors for job count
        selectors = [
            '[data-automation="totalJobsCount"]',
            'span[data-automation="totalJobsCount"]',
            '.yvsb870',  # Common Seek class for job count
            'strong[data-automation="totalJobsCount"]'
        ]
        
        for selector in selectors:
            try:
                total_jobs_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                total_text = total_jobs_element.text.replace(',', '').strip()
                if total_text.isdigit():
                    return int(total_text)
            except:
                continue
        
        # If all selectors fail, try to find any element with job count pattern
        page_source = driver.page_source
        import re
        match = re.search(r'(\d{1,3}(?:,?\d{3})*)\s*(?:jobs?|results?)', page_source, re.IGNORECASE)
        if match:
            count_text = match.group(1).replace(',', '')
            print(f"Found job count via regex: {count_text}")
            return int(count_text)
        
        # Save screenshot for debugging
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
        time.sleep(0.5)  # Wait for dynamic content (reduced from 2s)
        
        # Try multiple selectors
        selectors = [
            'a[data-automation="jobTitle"]',
            '[data-automation="jobTitle"]',
            'a[data-card-tracking-control="true"]',
            'article a[href*="/job/"]'
        ]
        
        for selector in selectors:
            try:
                job_cards = WebDriverWait(driver, 2).until(
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
        time.sleep(1)
        
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
                time.sleep(1)  # Wait for page to load (reduced from 3s)
                
                # Verify we're on a new page by checking URL chan
                return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"  Error clicking next page: {e}")
        return False

def extract_contact_info(text):
    """Extract email, phone, and website from text."""
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Australian phone patterns - more restrictive
    # Must have spaces, dashes, or parentheses to avoid random number sequences
    phone_pattern = r'(?:\+61[\s-]?[2-478][\s-]?\d{4}[\s-]?\d{4}|\(0[2-8]\)[\s-]?\d{4}[\s-]?\d{4}|0[2-8][\s-]\d{4}[\s-]\d{4}|04\d{2}[\s-]\d{3}[\s-]\d{3}|1[38]00[\s-]\d{3}[\s-]\d{3})'
    
    # Website pattern - must start with http/https or www, and filter out common false positives
    website_pattern = r'(?:https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s<>"]*)?|www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s<>"]*)?)'
    
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    websites = re.findall(website_pattern, text)
    
    # Filter out invalid emails (common false positives)
    emails = [e for e in emails if not e.endswith('.png') and not e.endswith('.jpg')]
    
    # Filter phones - remove if no spaces/dashes/parentheses (likely not a real phone number)
    phones = [p for p in phones if any(char in p for char in [' ', '-', '(', ')'])]
    
    # Filter websites - remove common false positives
    invalid_domains = ['ogp.me', 'schema.org', 'w3.org', 'xmlns.com', 'example.com', 
                       'facebook.com/sharer', 'twitter.com/intent', 'linkedin.com/sharing']
    websites = [w for w in websites if not any(inv in w.lower() for inv in invalid_domains)]
    websites = [w for w in websites if '@' not in w and not w.endswith('.jpg') and not w.endswith('.png')]
    
    # Only return if we have valid results
    return {
        'email': emails[0] if emails else '',
        'phone': phones[0] if phones else '',
        'website': websites[0] if websites else ''
    }

def scrape_job_details(driver, job_url, retry_count=0, max_retries=3):
    """Scrape job details from a given job URL."""
    job_data = {
        'job_title': '',
        'company': '',
        'location': '',
        'classification': '',
        'work_type': '',
        'salary': '',
        'time_posted': '',
        'application_volume': '',
        'email': '',
        'phone': '',
        'website': '',
        'url': job_url
    }
    
    try:
        driver.get(job_url)
        time.sleep(0.3)  # Brief pause to let page load (reduced from 1s)
        
        # Extract job title
        try:
            title_element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-automation="job-detail-title"]'))
            )
            job_data['job_title'] = title_element.text.strip()
        except:
            try:
                title_element = driver.find_element(By.TAG_NAME, 'h1')
                job_data['job_title'] = title_element.text.strip()
            except:
                job_data['job_title'] = 'N/A'
        
        # Extract company name
        try:
            company_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="advertiser-name"]')
            job_data['company'] = company_element.text.strip()
        except:
            try:
                company_element = driver.find_element(By.CSS_SELECTOR, 'span[data-automation="job-detail-advertiser"]')
                job_data['company'] = company_element.text.strip()
            except:
                job_data['company'] = 'N/A'
        
        # Extract location
        try:
            location_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="job-detail-location"]')
            job_data['location'] = location_element.text.strip()
        except:
            try:
                location_element = driver.find_element(By.CSS_SELECTOR, 'span[data-automation="job-detail-location"]')
                job_data['location'] = location_element.text.strip()
            except:
                job_data['location'] = ''
        
        # Extract classification
        try:
            classification_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="job-detail-classifications"]')
            job_data['classification'] = classification_element.text.strip()
        except:
            try:
                classification_element = driver.find_element(By.CSS_SELECTOR, 'a[data-automation="job-detail-classifications"]')
                job_data['classification'] = classification_element.text.strip()
            except:
                job_data['classification'] = ''
        
        # Extract work type
        try:
            work_type_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="job-detail-work-type"]')
            job_data['work_type'] = work_type_element.text.strip()
        except:
            try:
                work_type_element = driver.find_element(By.CSS_SELECTOR, 'span[data-automation="job-detail-work-type"]')
                job_data['work_type'] = work_type_element.text.strip()
            except:
                job_data['work_type'] = ''
        
        # Extract salary (both listed salary and predicted range)
        try:
            # Try to find listed salary first
            salary_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="job-detail-salary"]')
            job_data['salary'] = salary_element.text.strip()
        except:
            try:
                # Look for salary info in common span elements
                salary_spans = driver.find_elements(By.CSS_SELECTOR, 'span[data-automation="job-detail-salary"]')
                if salary_spans:
                    job_data['salary'] = salary_spans[0].text.strip()
            except:
                pass
        
        # If no listed salary, look for predicted salary range
        if not job_data['salary']:
            try:
                # Look for predicted salary text patterns
                salary_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$') or contains(text(), 'salary')]")
                for element in salary_elements:
                    text = element.text.strip()
                    # Look for salary range patterns (e.g., "$80,000 - $100,000", "$80k - $100k")
                    if '$' in text and ('-' in text or 'to' in text.lower()):
                        # Avoid the profile insight message
                        if 'profile' not in text.lower() and 'add' not in text.lower():
                            job_data['salary'] = text
                            break
            except:
                pass
        
        # Extract time posted (looking for "Posted X ago" pattern)
        try:
            time_elements = driver.find_elements(By.CSS_SELECTOR, '._1i38d6g0.dk7b5050.h9jxny0.h9jxny1.h9jxny1u.h9jxny6._1lwlriv4')
            for element in time_elements:
                text = element.text.strip()
                # Look for "Posted" keyword specifically
                if text and text.lower().startswith('posted'):
                    job_data['time_posted'] = text
                    break
        except:
            try:
                # Fallback: look for common time posted patterns
                time_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="job-detail-date"]')
                job_data['time_posted'] = time_element.text.strip()
            except:
                job_data['time_posted'] = ''
        
        # Extract application volume (looking for "volume" keyword)
        try:
            volume_elements = driver.find_elements(By.CSS_SELECTOR, '._1i38d6g0.dk7b5050.h9jxny0.h9jxny1.h9jxny1u.h9jxny6._1lwlriv4')
            for element in volume_elements:
                text = element.text.strip()
                # Look for "volume" keyword (e.g., "Medium application volume", "High application volume")
                if text and 'volume' in text.lower():
                    job_data['application_volume'] = text
                    break
        except:
            job_data['application_volume'] = ''
        
        # Extract job description and contact info - ONLY from job description, not entire page
        try:
            description_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')
            description_text = description_element.text
            
            # Extract contact information ONLY from description
            contact_info = extract_contact_info(description_text)
            job_data['email'] = contact_info['email']
            job_data['phone'] = contact_info['phone']
            job_data['website'] = contact_info['website']
        except:
            pass
        
        # Don't extract from page source - it causes false positives from meta tags
            
    except Exception as e:
        error_msg = str(e)
        if 'invalid session id' in error_msg.lower() or 'session' in error_msg.lower():
            # Browser session died - raise to trigger recovery
            raise
        else:
            print(f"Error scraping {job_url}: {e}")
    
    return job_data

def scrape_job_parallel(job_url, job_num, total_jobs, headless=True):
    """Scrape a single job in a separate browser instance (for parallel execution)."""
    driver = None
    try:
        driver = setup_driver(headless=headless)
        job_data = scrape_job_details(driver, job_url)
        driver.quit()
        print(f"  ✓ [Job #{job_num}] Completed")
        return job_data
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"  ✗ [Job #{job_num}] Failed: {e}")
        return {'job_title': '', 'company': '', 'location': '', 'classification': '', 'work_type': '', 'salary': '', 'time_posted': '', 'application_volume': '', 'email': '', 'phone': '', 'website': '', 'url': job_url}

def main():
    print("=" * 60)
    print("SEEK Web Scraper - ICT Jobs in All Melbourne VIC")
    print("=" * 60)
    print("\nNOTE: This scraper is for educational purposes only.")
    
    # Ask if user wants to sort by newest first
    while True:
        sort_input = input("\nSort by newest jobs first? (y/n): ").strip().lower()
        if sort_input in ['y', 'n']:
            sort_by_date = (sort_input == 'y')
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    
    # Ask how many parallel browsers to use
    while True:
        parallel_input = input("\nHow many parallel browsers? (1-10, recommended: 5): ").strip()
        if parallel_input.isdigit() and 1 <= int(parallel_input) <= 10:
            num_workers = int(parallel_input)
            break
        else:
            print("Invalid input. Enter a number between 1 and 10.")
    
    print(f"\n⚡ Using {num_workers} parallel browser(s) for faster scraping!")
    print("\nInitializing...\n")
    
    # Run in visible mode for debugging (set to True for headless)
    driver = setup_driver(headless=True)
    all_jobs_data = []
    
    try:
        # Navigate to the search page
        search_url = build_search_url(sort_by_date=sort_by_date)
        print(f"Navigating to: {search_url}\n")
        driver.get(search_url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(2)  # Reduced from 5s
        
        # Get total jobs available
        total_jobs = get_total_jobs(driver)
        print(f"\n📊 Total ICT jobs available: {total_jobs}")
        
        if total_jobs == 0:
            print("\n⚠️  Could not detect jobs on the page.")
            print("The browser window is open - please check if:")
            print("  1. The page loaded correctly")
            print("  2. There's a CAPTCHA or bot detection")
            print("  3. The URL is correct")
            print("\nPress Enter to continue with link extraction anyway, or Ctrl+C to quit...")
            input()
            total_jobs = 9999  # Fallback if can't detect
        
        # Ask user which jobs to scrape
        start_job = 1
        end_job = total_jobs
        
        while True:
            range_input = input(f"\nWhich jobs to scrape? (e.g., '1-100', '50-250', or 'all' for all {total_jobs}): ").strip().lower()
            
            if range_input == 'all':
                start_job = 1
                end_job = total_jobs
                print(f"Will scrape ALL jobs (1 to {total_jobs})")
                break
            elif '-' in range_input:
                try:
                    parts = range_input.split('-')
                    start_job = int(parts[0].strip())
                    end_job = int(parts[1].strip())
                    
                    if start_job < 1 or end_job > total_jobs or start_job > end_job:
                        print(f"Invalid range. Must be between 1 and {total_jobs}, with start <= end.")
                        continue
                    
                    print(f"Will scrape jobs {start_job} to {end_job} ({end_job - start_job + 1} jobs)")
                    break
                except ValueError:
                    print("Invalid format. Use format like '1-100' or 'all'.")
            else:
                print("Invalid input. Enter a range like '1-100' or 'all'.")
        
        # Collect job links from all pages
        all_job_links = []
        page_num = 1
        
        print("\nCollecting job links from search results...")
        
        # Determine stopping condition
        while True:
            # Check if we've collected enough jobs to cover the range
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
            
            # Remove duplicates
            all_job_links = list(dict.fromkeys(all_job_links))
            
            # Try to go to next page
            if not click_next_page(driver):
                print("  No more pages available.")
                break
            
            page_num += 1
            
            # Absolute safety limit
            if page_num > 100:
                print("  Reached absolute page limit (100 pages).")
                break
        
        print(f"\nTotal job links collected: {len(all_job_links)}")
        
        if len(all_job_links) == 0:
            print("\n❌ No jobs found. Exiting.")
            driver.quit()
            return
        
        # Filter to only the requested range (accounting for 0-based indexing)
        if end_job < len(all_job_links):
            all_job_links = all_job_links[start_job-1:end_job]
        elif start_job > 1:
            all_job_links = all_job_links[start_job-1:]
        
        print(f"Selected range: {len(all_job_links)} jobs (from job {start_job} to job {min(end_job, start_job + len(all_job_links) - 1)})")
        
        # Close the initial driver used for collecting links
        driver.quit()
        
        print(f"\n⚡ Scraping {len(all_job_links)} jobs using {num_workers} parallel browser(s)...")
        print("(Much faster with parallel processing!)\n")
        
        # Create filename at the start
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seek_ict_jobs_melbourne_{timestamp}.xlsx"
        
        # Parallel scraping with ThreadPoolExecutor
        all_jobs_data = [None] * len(all_job_links)  # Pre-allocate list to maintain order
        completed = 0
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all jobs
            future_to_index = {
                executor.submit(scrape_job_parallel, job_url, start_job + idx, len(all_job_links), headless=True): idx 
                for idx, job_url in enumerate(all_job_links)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    job_data = future.result()
                    all_jobs_data[idx] = job_data
                    completed += 1
                    
                    # Progress update
                    if completed % 10 == 0 or completed == len(all_job_links):
                        print(f"  Progress: {completed}/{len(all_job_links)} jobs completed ({(completed/len(all_job_links)*100):.1f}%)")
                    
                    # Save checkpoint every 100 jobs
                    if completed % 100 == 0:
                        with data_lock:
                            df_checkpoint = pd.DataFrame([j for j in all_jobs_data if j is not None])
                            df_checkpoint = df_checkpoint[['job_title', 'company', 'location', 'classification', 'work_type', 'salary', 'time_posted', 'application_volume', 'email', 'phone', 'website', 'url']]
                            df_checkpoint.to_excel(filename, index=False, engine='openpyxl')
                            print(f"  💾 Checkpoint saved: {completed} jobs")
                        
                except Exception as e:
                    print(f"  ✗ Job {idx+1} failed: {e}")
                    all_jobs_data[idx] = {'job_title': '', 'company': '', 'location': '', 'classification': '', 'work_type': '', 'salary': '', 'time_posted': '', 'application_volume': '', 'email': '', 'phone': '', 'website': '', 'url': all_job_links[idx]}
        
        # Remove any None values (shouldn't happen but just in case)
        all_jobs_data = [j for j in all_jobs_data if j is not None]
        
        # Retry failed jobs is no longer needed with parallel approach - failures are already handled
        
        # Final save to Excel
        if all_jobs_data:
            df = pd.DataFrame(all_jobs_data)
            # Reorder columns
            df = df[['job_title', 'company', 'location', 'classification', 'work_type', 'salary', 'time_posted', 'application_volume', 'email', 'phone', 'website', 'url']]
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            # Calculate statistics
            successful_scrapes = df[df['job_title'].notna() & (df['job_title'] != '') & (df['job_title'] != 'N/A')].shape[0]
            failed_scrapes = len(all_jobs_data) - successful_scrapes
            
            print("\n" + "=" * 60)
            print(f"✅ SUCCESS! Data exported to: {filename}")
            print(f"Total jobs scraped: {len(all_jobs_data)}")
            print(f"Successfully extracted: {successful_scrapes}")
            print(f"Failed to extract: {failed_scrapes}")
            print(f"Jobs with email: {df['email'].astype(bool).sum()}")
            print(f"Jobs with phone: {df['phone'].astype(bool).sum()}")
            print(f"Jobs with website: {df['website'].astype(bool).sum()}")
            print("=" * 60)
        else:
            print("\nNo jobs were scraped. Please check the search criteria or website structure.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user.")
        # Save whatever data we have so far
        if all_jobs_data:
            try:
                # Filter out None values before creating DataFrame
                valid_data = [j for j in all_jobs_data if j is not None]
                if valid_data:
                    df = pd.DataFrame(valid_data)
                    df = df[['job_title', 'company', 'location', 'classification', 'work_type', 'salary', 'time_posted', 'application_volume', 'email', 'phone', 'website', 'url']]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"seek_ict_jobs_melbourne_interrupted_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                    print(f"💾 Partial data saved to: {filename} ({len(valid_data)} jobs)")
                else:
                    print("No valid data to save.")
            except Exception as save_error:
                print(f"Could not save partial data: {save_error}")
        # Note: In parallel mode, browsers are managed by threads and will close automatically
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        # Save whatever data we have so far
        if all_jobs_data:
            try:
                # Filter out None values before creating DataFrame
                valid_data = [j for j in all_jobs_data if j is not None]
                if valid_data:
                    df = pd.DataFrame(valid_data)
                    df = df[['job_title', 'company', 'location', 'classification', 'work_type', 'salary', 'time_posted', 'application_volume', 'email', 'phone', 'website', 'url']]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"seek_ict_jobs_melbourne_error_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                    print(f"💾 Partial data saved to: {filename} ({len(valid_data)} jobs)")
                else:
                    print("No valid data to save.")
            except Exception as save_error:
                print(f"Could not save partial data: {save_error}")
        # Note: In parallel mode, browsers are managed by threads and will close automatically
        raise

if __name__ == "__main__":
    main()
