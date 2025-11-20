"""URL building for Seek search."""

from .config import BASE_URL, CLASSIFICATION, LOCATION


def build_search_url(sort_by_date=False, page=None):
    """
    Build the Seek URL for ICT jobs in All Melbourne VIC.
    
    Args:
        sort_by_date: Sort by listing date (newest first) if True
        page: Optional page number for direct pagination (default: None)
    
    Returns:
        Complete URL with optional page parameter
    """
    # Use the correct URL format from your config
    url = f"{BASE_URL}/{CLASSIFICATION}-jobs/in-{LOCATION}"
    
    params = []
    
    # Add page parameter BEFORE sortmode for Seek's URL structure
    if page is not None and page > 1:
        params.append(f"page={page}")
    
    if sort_by_date:
        params.append("sortmode=ListedDate")
    
    if params:
        url += "?" + "&".join(params)
    
    return url