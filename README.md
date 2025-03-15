# Welcome to Dimitri's Seek Webscraper (Work in Progress)

This is a super simple python program that uses selenium to scrape through seek job postings and calulate the frequency of any specified key words. Its intended use is for finding the most in demand programing languages for software engineering roles however it can be used to find how often any key word appears for any type of job.

<ins>**Only scraping 22 jobs at a time at the moment. Will fix soon!!**</ins>

The prgoram is simple:

You input the type of job you wish to scrape in the comand line (eg. input: software engineer, will scrape: https://www.seek.com.au/software-engineer-jobs) and follow it up with the key words you'd like to scrape for (eg. Python, Javascript, C). The program will then tally up the number of times these key words appear for that type of job (capped at one appearance per posting) and outputs the results (eg. Python: 10, Javascript: 3, C: 8).

**How I Worked Through This Program**
Here are the versions I'll be making of this program to eventually get a fully functioning scraper.
1. Scrape the first posting of software-engineer-jobs for its description and store it as a string in my program.
2. Be able to detect whether a speacfied key word appears in that string.
3. Be able to detect multiple key words.
4. Be able to specify the number of job postings you want to scrape and tally up key word detections amoung them.
5. Format this output.
Later: Store this output in a csv file.


**Checkout My Socials!!**
- [Instagram](https://www.instagram.com/dimitri_petrakis)
- [LinkedIn](https://www.linkedin.com/in/dimitrios-petrakis-719443269/)
- [Tiktok](https://www.tiktok.com/@dimitri_petrakis)
- [Checkout My Live Portfolio Here](https://dimitripetrakis.com/)
