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
driver.get("https://www.seek.com.au/python-jobs")

# Wait for job postings to load
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobTitle"]')))

# Select job postings
job_postings = driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobTitle"]')
jobs_avaliable = len(job_postings)

# Prompt user for the number of job postings they want to search
jobs_searching = input(f"Enter how many job postings you'd like to scrape (max = {jobs_avaliable}): ")

# Prompt user for keywords to search
keyword_input = input("Enter keyword(s) to search for (separate multiple keywords with commas): ")
# Create a dictionary with each keyword initialized to 0
keywords = {keyword.strip().lower(): 0 for keyword in keyword_input.split(',')}

print(f"\nSearching for keywords: {', '.join(keywords)}")

for i in range(0, int(jobs_searching) - 1):
    # Refresh the job postings list inside the loop
    job_postings = driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobTitle"]')
    
    if i >= len(job_postings):  # Ensure we're not going out of range
        break
    
    job_current = job_postings[i].get_attribute('href')
    driver.get(job_current)

    # Wait for the job description to load
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')))

    # Extract and store the job description as a string
    job_description = driver.find_element(By.CSS_SELECTOR, '[data-automation="jobAdDetails"]').text
    job_description_text = job_description.lower()  # Convert to lowercase for case-insensitive search

    # Check each keyword
    for keyword in keywords:
        # If the keyword appears in the job description, increment the count by 1
        if re.search(r'\b' + re.escape(keyword) + r'\b', job_description_text):
            keywords[keyword] += 1

# Print summary
print("\nKeyword counts:")
for keyword, count in keywords.items():
    print(f"{keyword}: {count}")

# Close the browser
driver.quit()