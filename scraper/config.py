"""Configuration and constants for the Seek scraper."""

# Search configuration
CLASSIFICATION = "information-communication-technology"
LOCATION = "All-Melbourne-VIC"
BASE_URL = "https://www.seek.com.au"

# Scraping settings
DEFAULT_WORKERS = 5
MAX_WORKERS = 10
CHECKPOINT_INTERVAL = 100
MAX_PAGES = 100

# Timeout settings (in seconds)
PAGE_LOAD_TIMEOUT = 2
ELEMENT_WAIT_TIMEOUT = 2
BRIEF_PAUSE = 0.3
PAGE_TRANSITION = 1
PAGINATION_SCROLL = 1

# Chrome options
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Google enrichment settings
ENABLE_GOOGLE_ENRICHMENT = True  # Set to False to skip Google Business phone lookup
GOOGLE_SEARCH_DELAY = 3  # Not used in parallel mode (each browser has own delays)

# Data columns
COLUMNS = [
    'job_title', 'company', 'location', 'classification', 
    'work_type', 'salary', 'time_posted', 'application_volume', 
    'email', 'phone', 'office_phone', 'website', 'url'
]

# Invalid website domains to filter
INVALID_DOMAINS = [
    'ogp.me', 'schema.org', 'w3.org', 'xmlns.com', 'example.com',
    'facebook.com/sharer', 'twitter.com/intent', 'linkedin.com/sharing'
]

# Recruitment companies to filter out (case-insensitive matching)
RECRUITMENT_COMPANIES = [
    'Hays Technology',
    'Hays',
    'Robert Half Technology',
    'Robert Half',
    'Michael Page Technology',
    'Michael Page',
    'Paxus',
    'Talent',
    'Peoplebank',
    'Finite IT',
    'Greythorn',
    'Halcyon Knights',
    'Lanson Partners',
    'Ignite',
    'Morgan McKinley Technology',
    'Morgan McKinley',
    'Clicks IT Recruitment',
    'Clicks IT',
    'Ambition Technology',
    'Ambition',
    'Davidson Technology',
    'Davidson',
    'Charterhouse IT',
    'Charterhouse',
    'Sirius Technology',
    'Sirius',
    'Bluefin Resources',
    'Bluefin',
    'Hudson Australia',
    'Hudson',
    'Expert360',
    'Launch Recruitment',
    'CircuIT Recruitment',
    'CircuIT',
    'Randstad Digital',
    'Randstad'
]
