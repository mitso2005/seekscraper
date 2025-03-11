from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# Locate ChromeDriver
os.environ['PATH'] += r"C:/seleniumDrivers"

# Initialize WebDriver
driver = webdriver.Chrome()

# Open the Seek job listings page
driver.get("https://www.seek.com.au/software-engineer-jobs")

# Wait for job postings to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobTitle"]')))

# Select job postings
job_postings = driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobTitle"]')

# Get the first job posting title
first_job_title = job_postings[0].text
print(f"First job title: {first_job_title}")

# Alternatively, if you want to get the href attribute as well:
first_job_href = job_postings[0].get_attribute('href')
print(f"First job link: {first_job_href}")

# Close the browser
driver.quit()