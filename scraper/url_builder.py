"""URL building for Seek search."""

from .config import BASE_URL, CLASSIFICATION, LOCATION


def build_search_url(sort_by_date=False):
    """Build the Seek URL for ICT jobs in All Melbourne VIC."""
    url = f"{BASE_URL}/{CLASSIFICATION}-jobs/in-{LOCATION}"
    
    if sort_by_date:
        url += "?sortmode=ListedDate"
    
    return url
