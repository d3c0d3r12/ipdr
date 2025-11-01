"""
Cloudflare Bypass Utility
Advanced web scraping with anti-detection techniques
"""

import time
import random
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Try to import undetected_chromedriver
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    logging.warning("undetected_chromedriver not available. Using standard Selenium.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudflareBypass:
    """
    Advanced Cloudflare bypass using multiple techniques
    """
    
    # User agent rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 30,
        use_undetected: bool = True
    ):
        """
        Initialize Cloudflare bypass
        
        Args:
            headless: Run browser in headless mode
            proxy: Proxy server (format: "host:port" or "user:pass@host:port")
            timeout: Maximum wait time in seconds
            use_undetected: Use undetected_chromedriver if available
        """
        self.headless = headless
        self.proxy = proxy
        self.timeout = timeout
        self.use_undetected = use_undetected and UNDETECTED_AVAILABLE
        self.driver = None
        
    def _get_chrome_options(self) -> Options:
        """Configure Chrome options for anti-detection"""
        options = Options()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # Random user agent
        user_agent = random.choice(self.USER_AGENTS)
        options.add_argument(f'user-agent={user_agent}')
        
        # Proxy configuration
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Disable webdriver flag
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        return options
    
    def _init_driver(self):
        """Initialize WebDriver with anti-detection"""
        try:
            if self.use_undetected:
                logger.info("Using undetected_chromedriver for maximum stealth")
                self.driver = uc.Chrome(
                    options=self._get_chrome_options(),
                    version_main=None,  # Auto-detect Chrome version
                    use_subprocess=True
                )
            else:
                logger.info("Using standard Selenium WebDriver")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(
                    service=service,
                    options=self._get_chrome_options()
                )
            
            # Execute CDP commands to hide webdriver
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(self.USER_AGENTS)
            })
            
            # Override navigator.webdriver
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _wait_for_cloudflare(self, max_wait: int = 30) -> bool:
        """
        Wait for Cloudflare challenge to complete
        
        Args:
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if challenge passed, False otherwise
        """
        logger.info("Waiting for Cloudflare challenge...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check if Cloudflare challenge is present
                page_source = self.driver.page_source.lower()
                
                # Cloudflare indicators
                cf_indicators = [
                    'checking your browser',
                    'cloudflare',
                    'ddos protection',
                    'ray id',
                    'cf-browser-verification'
                ]
                
                has_cf_challenge = any(indicator in page_source for indicator in cf_indicators)
                
                if not has_cf_challenge:
                    logger.info("✅ Cloudflare challenge passed!")
                    return True
                
                # Wait a bit before checking again
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking Cloudflare status: {e}")
                time.sleep(1)
        
        logger.warning("⚠️ Cloudflare challenge timeout")
        return False
    
    def get_page(
        self,
        url: str,
        wait_for_element: Optional[str] = None,
        retry_count: int = 3
    ) -> Optional[str]:
        """
        Fetch page content bypassing Cloudflare
        
        Args:
            url: Target URL
            wait_for_element: CSS selector to wait for (optional)
            retry_count: Number of retry attempts
            
        Returns:
            Page HTML content or None if failed
        """
        for attempt in range(retry_count):
            try:
                logger.info(f"Attempt {attempt + 1}/{retry_count}: Fetching {url}")
                
                # Initialize driver if not already done
                if not self.driver:
                    self._init_driver()
                
                # Navigate to URL
                self.driver.get(url)
                
                # Wait for Cloudflare challenge
                if not self._wait_for_cloudflare():
                    logger.warning("Cloudflare challenge not passed, but continuing...")
                
                # Wait for specific element if provided
                if wait_for_element:
                    logger.info(f"Waiting for element: {wait_for_element}")
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                else:
                    # Default wait for page load
                    time.sleep(3)
                
                # Get page source
                page_source = self.driver.page_source
                logger.info(f"✅ Successfully fetched page ({len(page_source)} bytes)")
                
                return page_source
                
            except TimeoutException:
                logger.error(f"Timeout waiting for page to load (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
            except WebDriverException as e:
                logger.error(f"WebDriver error: {e}")
                self.close()  # Close and reinitialize
                if attempt < retry_count - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
        
        logger.error(f"❌ Failed to fetch page after {retry_count} attempts")
        return None
    
    def get_cookies(self) -> Dict[str, str]:
        """Get current session cookies"""
        if not self.driver:
            return {}
        
        cookies = {}
        for cookie in self.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        
        return cookies
    
    def set_cookies(self, cookies: Dict[str, str]):
        """Set cookies for the session"""
        if not self.driver:
            self._init_driver()
        
        for name, value in cookies.items():
            self.driver.add_cookie({'name': name, 'value': value})
    
    def screenshot(self, filename: str = "screenshot.png"):
        """Take a screenshot for debugging"""
        if self.driver:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Test the bypass
    test_url = "https://example.com"  # Replace with your target URL
    
    print("🔥 Cloudflare Bypass Test")
    print("=" * 50)
    
    # Method 1: Using context manager (recommended)
    with CloudflareBypass(headless=False, use_undetected=True) as bypass:
        html = bypass.get_page(test_url)
        
        if html:
            print(f"✅ Success! Page length: {len(html)} bytes")
            print(f"📸 Taking screenshot...")
            bypass.screenshot("cloudflare_bypass_test.png")
            
            # Get cookies
            cookies = bypass.get_cookies()
            print(f"🍪 Cookies: {len(cookies)} items")
        else:
            print("❌ Failed to fetch page")
    
    print("\n" + "=" * 50)
    print("Test complete!")
