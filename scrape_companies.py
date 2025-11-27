"""Scrape jobs from specific companies."""

from scraper.company_search import search_multiple_companies_parallel
from scraper.streaming_parallel_scraper import scrape_job_parallel, phone_cache
from scraper.config import COLUMNS
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Victorian Government Departments and Agencies
COMPANIES = [
    # Departments
    "Education and Training",
    "Environment, Land, Water and Planning",
    "Families, Fairness and Housing",
    "Health",
    "Jobs, Precincts and Regions",
    "Justice and Community Safety",
    "Premier and Cabinet",
    "Transport",
    "Treasury and Finance",
    # Key Agencies
    "Cenitex",
    "Commercial Passenger Vehicle Commission",
    "Essential Services Commission",
    "Environment Protection Authority",
    "Game Management Authority",
    "Independent Broad-Based Anti-Corruption Commission",
    "Infrastructure Victoria",
    "Office of Public Prosecutions and Associate Crown Prosecutors",
    "Office of the Chief Commissioner of Police (Victoria Police)",
    "Office of the Commissioner for Environmental Sustainability",
    "Office of the Commission for Children and Young People",
    "Office of the Labour Hire Licensing Authority",
    "Office of the Legal Services Commissioner",
    "Office of the Ombudsman",
    "Office of the Road Safety Camera Commissioner",
    "Office of the Victorian Disability Worker Commissioner",
    "Office of the Victorian Information Commissioner",
    "Portable Long Service Benefits Authority",
    "Victorian Auditor-General's Office",
    "Victorian Commission for Gambling and Liquor Regulation",
    "Victorian Electoral Commission",
    "Victorian Equal Opportunity and Human Rights",
    "Victorian Fisheries Authority",
    "Victorian Inspectorate",
    "Victorian Public Sector Commission",
    "Victorian Responsible Gambling Foundation",
    # Education & Training
    "Adult Community and Further Education Board",
    "Adult Multicultural Education Services (AMES Aust)",
    "Bendigo TAFE",
    "Box Hill Institute of TAFE",
    "Chisholm Institute",
    "Federation Training - TAFE Gippsland",
    "Gordon Institute of TAFE",
    "Goulburn Ovens Institute of TAFE",
    "Holmesglen Institute of TAFE",
    "Melbourne Polytechnic",
    "South West Institute of TAFE",
    "Sunraysia Institute of TAFE",
    "Victorian Curriculum and Assessment Authority (VCAA)",
    "Victorian Institute of Teaching",
    "Victorian Registration and Qualifications Authority",
    "William Angliss Institute of TAFE",
    "Wodonga Institute of TAFE",
    # Environment, Water & Planning
    "Alpine Resorts Co-ordinating Council",
    "Architects' Registration Board of Victoria",
    "Barwon Region Water Corporation",
    "Central Gippsland Region Water Corporation",
    "Central Highlands Region Water Corporation",
    "City West Water Corporation",
    "Cladding Safety Victoria",
    "Coliban Region Water Corporation",
    "Corangamite Catchment Management Authority",
    "Dhelkunya Dja Land Management Board",
    "East Gippsland Catchment Management Authority",
    "East Gippsland Region Water Corporation",
    "Energy Safe Victoria",
    "Falls Creek Alpine Resort Management Board",
    "Glenelg Hopkins Catchment Management Authority",
    "Goulburn Broken Catchment Management Authority",
    "Goulburn Valley Region Water Corporation",
    "Goulburn Valley Waste and Resource Recovery Group",
    "Goulburn-Murray Rural Water Corporation",
    "Grampians Central Waste and Resource Recovery Group",
    "GWM Water (Grampians Wimmera-Mallee Water Corporation)",
    "Lower Murray Urban and Rural Water Corporation",
    "Mallee Catchment Management Authority",
    "Melbourne Water Corporation",
    "Metropolitan Waste and Resource Recovery Group",
    "Mount Buller and Mount Stirling Alpine Resort Management Board",
    "Mount Hotham Alpine Resort Management Board",
    "North Central Catchment Management Authority",
    "North East Catchment Management Authority",
    "North East Region Water Corporation",
    "Parks Victoria",
    "Phillip Island Nature Park Board of Management",
    "Port Phillip and Westernport Catchment Management Authority",
    "Royal Botanic Gardens Board of Victoria",
    "South East Water Corporation",
    "South Gippsland Water Corporation",
    "Southern Alpine Resort Management Board",
    "Southern Rural Water Corporation",
    "Surveyors Registration Board of Victoria",
    "Sustainability Victoria",
    "Trust for Nature (Victoria)",
    "Victorian Building Authority",
    "Victorian Environmental Water Holder",
    "Victorian Planning Authority",
    "Wannon Region Water Corporation",
    "West Gippsland Catchment Management Authority",
    "Western Water Corporation",
    "Westernport Region Water Corporation",
    "Wimmera Catchment Management Authority",
    "Yarra Valley Water Corporation",
    "Zoological Parks and Gardens Board",
    # Families, Fairness & Housing
    "Queen Victoria Women's Centre Trust",
    "Shrine of Remembrance",
    "Victorian Interpreting and Translating Services (VITS) Language Loop",
    # Health
    "Ambulance Victoria",
    "Ballarat General Cemeteries Trust",
    "Geelong Cemeteries Trust",
    "Greater Metropolitan Cemeteries Trust",
    "Mental Health Tribunal",
    "Remembrance Parks Central Victoria (Formerly Bendigo Cemeteries Trust)",
    "Southern Metropolitan Cemeteries Trust",
    "VicHealth (Victorian Health Promotion Foundation)",
    "Victorian Assisted Reproductive Treatment Authority",
    "Victorian Institute of Forensic Mental Health (Forensicare)",
    "Victorian Pharmacy Authority",
    # Jobs, Precincts & Regions
    "Arts Centre Melbourne",
    "Australian Centre for the Moving Image",
    "Australian Grand Prix Corporation",
    "Dairy Food Safety Victoria",
    "Emerald Tourist Railway Board",
    "Film Victoria",
    "Geelong Performing Arts Centre Trust",
    "Greyhound Racing Victoria",
    "Harness Racing Victoria",
    "Kardinia Park Stadium Trust",
    "Melbourne and Olympic Parks Trust",
    "Melbourne Convention and Exhibition Centre Trust (MCEC)",
    "Melbourne Cricket Ground Trust",
    "Melbourne Market Authority",
    "Museums Victoria",
    "National Gallery of Victoria, Council of Trustees",
    "PrimeSafe",
    "State Library of Victoria",
    "State Sports Centres Trust",
    "Veterinary Practitioners Registration Board of Victoria",
    "VicForests",
    # Justice & Community Safety
    "Accident Compensation and Conciliation Service",
    "Court Services Victoria",
    "Country Fire Authority",
    "Emergency Services Telecommunications Authority",
    "Fire Rescue Victoria",
    "Residential Tenancies Bond Authority",
    "Sentencing Advisory Council",
    "Victoria Legal Aid",
    "Victoria State Emergency Service Authority",
    "Victorian Institute of Forensic Medicine",
    "Victorian Law Reform Commission",
    "Worksafe Victoria",
    # Transport
    "Development Victoria",
    "Port of Hastings Development Authority",
    "Transport Accident Commission",
    "V/Line Corporation",
    "Victorian Ports Corporation",
    "Victorian Regional Channels Authority",
    "VicTrack",
    # Treasury & Finance
    "Emergency Services and State Superannuation Board - ESSB",
    "Treasury Corporation of Victoria",
    "Victorian Funds Management Corporation",
    "Victorian Managed Insurance Authority",
]


def scrape_company_jobs(companies, scrape_workers=5, search_workers=3, location="Melbourne", output_file="company_jobs.xlsx"):
    """
    Scrape jobs from specific companies.
    
    Args:
        companies: List of company names
        scrape_workers: Number of parallel workers for scraping jobs (default: 5)
        search_workers: Number of parallel workers for searching companies (default: 3)
        location: Location filter (default: Melbourne)
        output_file: Output Excel filename (default: company_jobs.xlsx)
    """
    # Step 1: Search for jobs from each company (parallel headless)
    print("=" * 60)
    print("🏢 COMPANY-SPECIFIC JOB SCRAPER")
    print("=" * 60)
    
    company_jobs = search_multiple_companies_parallel(companies, location, num_workers=search_workers, headless=True)
    
    # Flatten job list and track which company posted each job
    all_jobs = []
    job_to_company = {}
    
    for company, jobs in company_jobs.items():
        for job_url in jobs:
            all_jobs.append(job_url)
            job_to_company[job_url] = company
    
    if not all_jobs:
        print("\n❌ No jobs found!")
        return
    
    print(f"\n{'=' * 60}")
    print(f"⚡ SCRAPING {len(all_jobs)} JOBS")
    print(f"{'=' * 60}")
    print(f"Scrape Workers: {scrape_workers}")
    print(f"Location: {location}")
    print(f"Output: {output_file}\n")
    
    # Step 2: Scrape jobs in parallel
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=scrape_workers) as executor:
        futures = {
            executor.submit(scrape_job_parallel, url, i+1, len(all_jobs), headless=True): url
            for i, url in enumerate(all_jobs)
        }
        
        for future in as_completed(futures):
            job_url = futures[future]
            try:
                job_data = future.result()
                if job_data:
                    results.append(job_data)
                
                completed += 1
                
                # Progress update
                if completed % 10 == 0 or completed == len(all_jobs):
                    print(f"  Progress: {completed}/{len(all_jobs)} ({completed/len(all_jobs)*100:.1f}%)")
                    
            except Exception as e:
                print(f"  ✗ Failed to scrape job: {e}")
    
    # Step 3: Save results
    print(f"\n{'=' * 60}")
    print("💾 SAVING RESULTS")
    print(f"{'=' * 60}\n")
    
    if results:
        df = pd.DataFrame(results, columns=COLUMNS)
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✅ Saved {len(results)} jobs to {output_file}")
        
        # Show cache stats
        stats = phone_cache.get_stats()
        print(f"📞 Phone cache: {stats['with_phone']}/{stats['total_companies']} companies have phone numbers")
        
        # Show breakdown by company
        print(f"\n📊 Jobs by Company:")
        company_counts = {}
        for job in results:
            company = job.get('company', 'Unknown')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {company}: {count} jobs")
    else:
        print("❌ No valid jobs scraped!")


if __name__ == "__main__":
    # You can customize these parameters:
    scrape_company_jobs(
        companies=COMPANIES,
        scrape_workers=20,      # Parallel workers for scraping job details
        search_workers=20,      # Parallel workers for searching companies
        location="Melbourne",
        output_file="company_jobs.xlsx"
    )
