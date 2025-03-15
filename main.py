from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re

def setup_driver():
    """Initialize and return a Selenium WebDriver instance."""
    try:
        os.environ['PATH'] += r"C:/seleniumDrivers"
        # Set Chrome options for headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error initializing the WebDriver: {e}")
        exit()  # Exit if the driver can't be initialized

def get_total_jobs(driver):
    """Extract and return the total number of job postings available."""
    try:
        total_jobs_element = driver.find_element(By.CSS_SELECTOR, '[data-automation="totalJobsCount"]')
        return total_jobs_element.text
    except Exception as e:
        print(f"Error while extracting job count: {e}")
        return "0"  # Return "0" if there's an issue with extracting the count

def get_job_postings(driver):
    """Return a list of job posting elements."""
    try:
        return driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobTitle"]')
    except Exception as e:
        print(f"Error retrieving job postings: {e}")
        return []  # Return an empty list if an error occurs

def get_keywords():
    """Prompt user for keywords and return them as a dictionary."""
    keyword_input = input("Enter keyword(s) to search for (separate multiple keywords with commas): ")
    return {keyword.strip().lower(): 0 for keyword in keyword_input.split(',')}

def scrape_job_details(driver, job_url, keywords):
    """Scrape job details from a given job URL and update keyword counts."""
    try:
        driver.get(job_url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')))
        job_description = driver.find_element(By.CSS_SELECTOR, '[data-automation="jobAdDetails"]').text.lower()
        
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', job_description):
                keywords[keyword] += 1
    except Exception as e:
        print(f"Error while scraping job details from {job_url}: {e}")

def main():
    run_program = 'y'
    while run_program == 'y':
        try:
            job_title = input("Enter job title to search for: ").replace(" ", "-")
            driver = setup_driver()
            driver.get(f"https://www.seek.com.au/{job_title}-jobs")
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobTitle"]')))
            
            jobs_available = get_total_jobs(driver)
            print(f"Total jobs available: {jobs_available}")
            
            # Remove commas from jobs_available and convert to integer
            jobs_available = int(jobs_available.replace(',', ''))

            # Prompt user for input
            jobs_searching = input(f"Enter how many job postings you'd like to scrape (max = {jobs_available}): ")

            # Validate input with while loop
            while not jobs_searching.isdigit() or int(jobs_searching) <= 0:
                print("Invalid input. Please enter a valid positive integer value.")
                jobs_searching = input(f"Enter how many job postings you'd like to scrape (max = {jobs_available}): ")

            # Convert to integer after validation
            jobs_searching = int(jobs_searching)

            # Check if exceeds maximum and handle that case
            if jobs_searching > jobs_available:
                print(f"Can't scrape more than {jobs_available} jobs. Scraping {jobs_available} jobs instead.")
                jobs_searching = jobs_available
                        
            keywords = get_keywords()
            print(f"\nSearching for keywords: {', '.join(keywords)}")
            
            for i in range(jobs_searching):
                job_postings = get_job_postings(driver)
                if i >= len(job_postings):
                    print("No more job postings available.")
                    break
                
                job_url = job_postings[i].get_attribute('href')
                scrape_job_details(driver, job_url, keywords)
                
                driver.back()
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobTitle"]')))
            
            print("\nKeyword counts:")
            for keyword, count in keywords.items():
                print(f"{keyword}: {count}")
            
            driver.quit()
        
        except Exception as e:
            print(f"Error during main program execution: {e}")
            if driver:
                driver.quit()  # Ensure the driver quits in case of any error

        repeat_input = input("\nWould you like to scrape more jobs? (y/n): ").lower()
        while repeat_input not in ['y', 'n']:
            print("Invalid input. Please enter 'y' for Yes or 'n' for No.")
            repeat_input = input("\nWould you like to scrape more jobs? (y/n): ").lower()

        # After a valid input is entered, assign it to run_program
        run_program = repeat_input

if __name__ == "__main__":
    main()

print("\nI hope I was helpful,\ngoodbye!")
exit()
