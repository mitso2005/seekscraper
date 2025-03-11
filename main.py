from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import re

# Locate ChromeDriver
os.environ['PATH'] += r"C:/seleniumDrivers"

# Initialize WebDriver
driver = webdriver.Chrome()

# Open the Seek job listings page
driver.get("https://www.seek.com.au/software-engineer-jobs")

# Wait for job postings to load
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobTitle"]')))

# Select job postings
job_postings = driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobTitle"]')

# Get the first job posting title
first_job_title = job_postings[0].text
print(f"First job title: {first_job_title}")

# Alternatively, if you want to get the href attribute as well:
first_job_href = job_postings[0].get_attribute('href')
print(f"First job link: {first_job_href}")

# Navigate to the job posting URL
driver.get(first_job_href)

# Wait for the job description to load (you might need to adjust the selector based on the actual page structure)
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')))

# Extract the job description text
# Note: The actual selector might differ depending on the website structure
job_description = driver.find_element(By.CSS_SELECTOR, '[data-automation="jobAdDetails"]').text

# Store the job description as a string
job_description_text = job_description.lower()  # Convert to lowercase for case-insensitive search

# Prompt user for keywords to search
user_input = input("Enter keyword(s) to search for (separate multiple keywords with commas): ")
keywords = [keyword.strip().lower() for keyword in user_input.split(',')]

print(f"\nSearching for keywords: {', '.join(keywords)}")

# Check for each keyword in the description
found_keywords = []
not_found_keywords = []

for keyword in keywords:
    # Use word boundaries to match whole words
    pattern = r'\b' + re.escape(keyword) + r'\b'
    if re.search(pattern, job_description.lower()):
        found_keywords.append(keyword)
    else:
        not_found_keywords.append(keyword)

# Print summary
if found_keywords:
    print(f"\nKeywords found: {', '.join(found_keywords)}")
else:
    print("\nNo keywords were found in the job description.")
    
if not_found_keywords:
    print(f"Keywords not found: {', '.join(not_found_keywords)}")

# Close the browser
driver.quit()