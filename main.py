import os
from scraper.driver_setup import setup_driver
from scraper.streaming_parallel_scraper import scrape_jobs_streaming, cleanup_all_browsers
from scraper.data_export import create_filename, save_to_excel, print_statistics
from scraper.url_builder import build_search_url
from scraper.page_parser import get_total_jobs
from scraper.phone_cache import phone_cache
from scraper.user_input import get_sort_preference, get_parallel_workers, get_job_range


def main():
    use_default = os.getenv('USE_DEFAULT_CONFIG', 'false').lower() == 'true'

    print("=" * 60)
    print("SEEK Web Scraper - ICT Jobs in All Melbourne VIC")
    print("=" * 60)
    print("\nNOTE: This scraper is for educational purposes only.\n")

    if use_default:
        print("Running in AUTOMATIC mode with default configuration")
        sort_by_date = True
        num_workers = 20
        start_job = 1
        end_job = 999999  # Will scrape all available
        print(f"  - Sort by date: Yes")
        print(f"  - Parallel browsers: {num_workers}")
        print(f"  - Job range: All available\n")
    else:
        print("Running in INTERACTIVE mode\n")
        sort_by_date = get_sort_preference()
        num_workers = get_parallel_workers()

    driver = None
    phone_cache.load()

    try:
        print("Initializing browser...")
        driver = setup_driver(headless=True)
        search_url = build_search_url(sort_by_date=sort_by_date)
        driver.get(search_url)

        total_jobs = get_total_jobs(driver)
        print(f"Total jobs found: {total_jobs}\n")

        if not use_default:
            start_job, end_job = get_job_range(total_jobs)
        else:
            end_job = min(end_job, total_jobs)

        filename = create_filename()
        print(f"Output will be saved to: {filename}\n")

        print(f"Starting scrape: jobs {start_job}-{end_job} with {num_workers} parallel browsers\n")

        all_jobs_data, all_job_urls = scrape_jobs_streaming(
            driver=driver,
            start_job=start_job,
            end_job=end_job,
            num_workers=num_workers,
            filename=filename,
            use_page_based=False,
            start_page=1,
            end_page=None,
            sort_by_date=sort_by_date
        )

        df = save_to_excel(all_jobs_data, filename)
        print_statistics(df, filename)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
        cleanup_all_browsers()
        phone_cache.save()
        print("\nCleanup complete.")


if __name__ == "__main__":
    main()