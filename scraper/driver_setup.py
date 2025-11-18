"""WebDriver setup and configuration."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .config import USER_AGENT, PAGE_LOAD_TIMEOUT


def create_chrome_options(headless=False):
    """Create and configure Chrome options for optimal performance."""
    options = webdriver.ChromeOptions()
    
    # Basic options
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={USER_AGENT}")
    
    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Performance optimizations
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    # Disable images and CSS for faster loading
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
            'stylesheet': 2
        },
        'profile.managed_default_content_settings': {
            'images': 2
        }
    }
    options.add_experimental_option('prefs', prefs)
    
    return options


def setup_driver(headless=False):
    """Initialize and return a configured Selenium WebDriver instance."""
    try:
        options = create_chrome_options(headless)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute CDP commands to hide webdriver property
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": USER_AGENT
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set implicit wait for faster performance
        driver.implicitly_wait(PAGE_LOAD_TIMEOUT)
        
        return driver
    except Exception as e:
        print(f"Error initializing the WebDriver: {e}")
        raise
