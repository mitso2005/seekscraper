# Seek Job Scraper

## Overview

**Dimitri's Seek Web Scraper** is a Python-based tool that leverages Selenium to scrape job postings from [Seek](https://www.seek.com.au). It calculates the frequency of specified keywords within job descriptions. This project is useful for identifying in-demand programming languages for software engineering roles or analyzing keyword appearances in any job category.

> **⚠️ Note:** Currently, the scraper only retrieves 22 job postings at a time. This will be fixed in future updates.

## Features

- Scrapes job postings from Seek based on a user-defined job title.
- Extracts job descriptions and counts occurrences of specified keywords.
- Allows users to specify multiple keywords.
- Outputs keyword counts for analysis.
- Future updates will include CSV export functionality.

## Installation

### Prerequisites

Ensure you have the following installed on your system:

- Python 3
- Google Chrome
- ChromeDriver (ensure it is added to your system PATH)
- Required Python packages:
  ```sh
  pip install selenium
  ```

## Usage

1. **Clone the repository:**
   ```sh
   git clone https://github.com/dimitripetrakis/seek-webscraper.git
   cd seek-webscraper
   ```
2. **Run the script:**
   ```sh
   python main.py
   ```
3. **Follow the prompts:**
   - Enter the job title (e.g., "software engineer").
   - Specify the number of job postings to scrape.
   - Enter keywords to track (comma-separated).
4. **View the output:** The script will display the count of each keyword found across job descriptions.

## Development Plan

### Version Roadmap

1. Scrape a single job posting and extract its description.
2. Detect a specified keyword within the job description.
3. Detect multiple keywords.
4. Allow users to specify the number of job postings to scrape.
5. Format the output for readability.
6. **(Future Update)** Store results in a CSV file.

## Future Enhancements

- **Fix job count limitation** (scraping only 22 jobs at a time).
- **Improve efficiency** by optimizing Selenium operations.
- **CSV export** for easier data analysis.
- **Add GUI support** for easier user interaction.

## Connect with Me

If you find this project useful, let's connect!

- [Instagram](https://www.instagram.com/dimitri_petrakis)
- [LinkedIn](https://www.linkedin.com/in/dimitrios-petrakis-719443269/)
- [TikTok](https://www.tiktok.com/@dimitri_petrakis)
- [Portfolio](https://dimitripetrakis.com/)

---

Feel free to contribute or suggest improvements!

