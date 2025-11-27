"""Resume manager for handling Google quota exceeded and auto-resume."""

import os
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from .config import COLUMNS


class ResumeManager:
    """Manages scraping progress and auto-resume functionality."""
    
    def __init__(self, filename):
        self.filename = filename
        self.progress_file = filename.replace('.xlsx', '_progress.json')
        self.completed_urls = set()
        self.load_progress()
    
    def load_progress(self):
        """Load previously completed jobs from progress file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.completed_urls = set(data.get('completed_urls', []))
                print(f"Loaded progress: {len(self.completed_urls)} jobs already completed")
            except Exception as e:
                print(f"WARNING: Could not load progress file: {e}")
        
        if os.path.exists(self.filename):
            try:
                df = pd.read_excel(self.filename)
                if 'url' in df.columns:
                    excel_urls = set(df['url'].dropna().tolist())
                    self.completed_urls.update(excel_urls)
                    print(f"Loaded from checkpoint: {len(excel_urls)} jobs in Excel file")
            except Exception as e:
                print(f"WARNING: Could not load checkpoint file: {e}")
    
    def save_progress(self, all_jobs_data):
        """Save current progress to JSON file."""
        try:
            completed = [job['url'] for job in all_jobs_data if job and job.get('url')]
            self.completed_urls.update(completed)
            
            progress_data = {
                'completed_urls': list(self.completed_urls),
                'last_updated': datetime.now().isoformat(),
                'total_completed': len(self.completed_urls)
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
        except Exception as e:
            print(f"WARNING: Could not save progress: {e}")
    
    def is_completed(self, url):
        """Check if a job URL has already been scraped."""
        return url in self.completed_urls
    
    def filter_pending_urls(self, all_urls):
        """Filter out already completed URLs."""
        pending = [url for url in all_urls if url not in self.completed_urls]
        if len(pending) < len(all_urls):
            print(f"📋 Filtered out {len(all_urls) - len(pending)} already completed jobs")
            print(f"📋 Remaining to scrape: {len(pending)} jobs")
        return pending
    
    def merge_with_existing(self, new_jobs_data):
        """Merge new job data with existing checkpoint data."""
        existing_data = []
        
        if os.path.exists(self.filename):
            try:
                df_existing = pd.read_excel(self.filename)
                existing_data = df_existing.to_dict('records')
                print(f"Loaded {len(existing_data)} existing jobs from checkpoint")
            except Exception as e:
                print(f"WARNING: Could not load existing data: {e}")
        
        existing_urls = {job.get('url') for job in existing_data if job.get('url')}
        new_unique = [job for job in new_jobs_data if job.get('url') not in existing_urls]
        
        combined = existing_data + new_unique
        print(f"Merged: {len(existing_data)} existing + {len(new_unique)} new = {len(combined)} total jobs")
        
        return combined
    
    def cleanup_progress_file(self):
        """Remove progress file after successful completion."""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                print(f"🗑️  Cleaned up progress file")
        except:
            pass


def detect_quota_exceeded():
    """Check if we should pause due to Google quota issues."""
    # This would be called to detect quota issues
    # For now, we'll rely on exception handling
    pass


def wait_for_quota_reset(wait_minutes=30):
    """Wait for Google quota to reset."""
    print(f"\nPausing for {wait_minutes} minutes to reset Google quota...")
    print(f"Resume time: {datetime.now() + timedelta(minutes=wait_minutes)}")
    
    for remaining in range(wait_minutes * 60, 0, -60):
        mins = remaining // 60
        print(f"   {mins} minutes remaining...", end='\r')
        time.sleep(60)
    
    print("\nQuota reset period complete. Resuming scraping...")
