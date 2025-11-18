"""Data export and statistics."""

import pandas as pd
from datetime import datetime
from .config import COLUMNS


def create_filename(interrupted=False, error=False):
    """Generate a timestamped filename for the Excel output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if interrupted:
        return f"seek_ict_jobs_melbourne_interrupted_{timestamp}.xlsx"
    elif error:
        return f"seek_ict_jobs_melbourne_error_{timestamp}.xlsx"
    else:
        return f"seek_ict_jobs_melbourne_{timestamp}.xlsx"


def save_to_excel(all_jobs_data, filename):
    """
    Save job data to Excel file.
    
    Args:
        all_jobs_data: List of job data dictionaries
        filename: Output filename
    
    Returns:
        pandas DataFrame of the saved data
    """
    if not all_jobs_data:
        return None
    
    print(f"\n  💾 Saving {len(all_jobs_data)} jobs to Excel...")
    
    # Create DataFrame with specified column order (more efficient)
    df = pd.DataFrame(all_jobs_data, columns=COLUMNS)
    df.to_excel(filename, index=False, engine='openpyxl')
    
    print(f"  ✅ Excel file saved successfully")
    
    return df


def print_statistics(df, filename, total_processed=None, filtered_count=0):
    """
    Print scraping statistics.
    
    Args:
        df: DataFrame of scraped jobs
        filename: Output filename
        total_processed: Total number of jobs processed (including filtered)
        filtered_count: Number of jobs filtered out (recruitment companies + non-full-time)
    """
    if df is None or df.empty:
        if filtered_count > 0:
            print("\n" + "=" * 60)
            print("⚠️  All jobs were filtered out")
            print(f"Total jobs processed: {total_processed}")
            print(f"Jobs filtered (recruitment + contract/temp + large companies): {filtered_count}")
            print("=" * 60)
        else:
            print("\nNo jobs were scraped. Please check the search criteria or website structure.")
        return
    
    print("\n  📊 Calculating statistics...")
    
    successful_scrapes = df[df['job_title'].notna() & (df['job_title'] != '') & (df['job_title'] != 'N/A')].shape[0]
    failed_scrapes = len(df) - successful_scrapes
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS! Data exported to: {filename}")
    
    if total_processed and filtered_count > 0:
        print(f"Total jobs processed: {total_processed}")
        print(f"Jobs filtered (recruitment + contract/temp + large companies): {filtered_count}")
        print(f"Jobs saved to Excel (small-mid companies, permanent roles): {len(df)}")
    else:
        print(f"Total jobs scraped: {len(df)}")
    
    print(f"Successfully extracted: {successful_scrapes}")
    print(f"Failed to extract: {failed_scrapes}")
    print(f"Jobs with email: {df['email'].astype(bool).sum()}")
    print(f"Jobs with phone: {df['phone'].astype(bool).sum()}")
    print(f"Jobs with website: {df['website'].astype(bool).sum()}")
    print("=" * 60)


def save_partial_data(all_jobs_data, interrupted=False):
    """Save partial data when scraping is interrupted or errors occur."""
    if not all_jobs_data:
        print("No valid data to save.")
        return
    
    try:
        valid_data = [j for j in all_jobs_data if j is not None]
        if valid_data:
            filename = create_filename(interrupted=interrupted, error=not interrupted)
            df = save_to_excel(valid_data, filename)
            print(f"💾 Partial data saved to: {filename} ({len(valid_data)} jobs)")
        else:
            print("No valid data to save.")
    except Exception as save_error:
        print(f"Could not save partial data: {save_error}")
