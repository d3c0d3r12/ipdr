"""
Automatic Cookie Fetcher for InfoByIP
Automatically fetches and validates cookies using Selenium
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

logger = logging.getLogger(__name__)


class AutoCookieFetcher:
    """
    Automatically fetches cookies from InfoByIP by solving Cloudflare challenge
    """
    
    def __init__(self):
        self.driver = None
        self.cookie_file = Path(__file__).parent.parent / "infobyip_cookies.json"
    
    def setup_driver(self, headless: bool = True):
        """
        Setup Chrome driver with options
        
        Args:
            headless: Run in headless mode (no visible browser)
        """
        try:
            logger.info("🚀 Setting up Chrome driver...")
            
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless=new')
            
            # Essential options for Cloudflare bypass
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Install and setup driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            logger.info("✅ Chrome driver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up driver: {e}")
            return False
    
    def fetch_cookies(self, headless: bool = True, max_wait: int = 30) -> Dict:
        """
        Automatically fetch cookies from InfoByIP
        
        Args:
            headless: Run in headless mode
            max_wait: Maximum time to wait for Cloudflare (seconds)
        
        Returns:
            Dict with status and cookies
        """
        try:
            logger.info("🍪 Starting automatic cookie fetch...")
            
            # Setup driver
            if not self.setup_driver(headless):
                return {
                    "success": False,
                    "error": "Failed to setup browser",
                    "message": "Could not initialize Chrome driver"
                }
            
            # Visit InfoByIP
            logger.info("🌐 Visiting InfoByIP.com...")
            self.driver.get("https://www.infobyip.com/ip-8.8.8.8.html")
            
            # Wait for Cloudflare challenge to complete
            logger.info("⏳ Waiting for Cloudflare challenge...")
            start_time = time.time()
            cloudflare_passed = False
            
            while time.time() - start_time < max_wait:
                # Check if page has loaded (Cloudflare passed)
                try:
                    page_source = self.driver.page_source
                    
                    # Check if still on Cloudflare challenge
                    if "Checking your browser" in page_source or "Just a moment" in page_source:
                        logger.info("⏳ Still on Cloudflare challenge...")
                        time.sleep(3)
                        continue
                    
                    # Look for content that appears after Cloudflare
                    if "United States" in page_source or "Google" in page_source or "IP Address Location" in page_source:
                        logger.info("✅ Cloudflare challenge passed!")
                        cloudflare_passed = True
                        break
                    
                    # Wait and check again
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Error checking page: {e}")
                    time.sleep(2)
            
            # Check if we timed out
            if not cloudflare_passed:
                logger.error("❌ Timeout waiting for Cloudflare")
                self.cleanup()
                return {
                    "success": False,
                    "error": "timeout",
                    "message": "Cloudflare challenge took too long. Try again."
                }
            
            # Wait longer to ensure cf_clearance cookie is set
            logger.info("⏳ Waiting for cf_clearance cookie to be set...")
            time.sleep(5)
            
            # Check multiple times for cf_clearance cookie
            for attempt in range(3):
                cookies = self.driver.get_cookies()
                cookie_names = [c['name'] for c in cookies]
                
                if 'cf_clearance' in cookie_names:
                    logger.info("✅ cf_clearance cookie found!")
                    break
                else:
                    logger.warning(f"⚠️ cf_clearance not found yet (attempt {attempt + 1}/3), waiting...")
                    time.sleep(3)
            
            # Final wait to ensure all cookies are stable
            time.sleep(2)
            
            # Extract cookies
            logger.info("🍪 Extracting cookies...")
            cookies = self.driver.get_cookies()
            
            if not cookies:
                logger.error("❌ No cookies found")
                self.cleanup()
                return {
                    "success": False,
                    "error": "no_cookies",
                    "message": "No cookies were set. Try again."
                }
            
            # Convert to simple format
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']
            
            # Check for essential cookies
            has_cf_clearance = 'cf_clearance' in cookie_dict
            
            if not has_cf_clearance:
                logger.warning("⚠️ cf_clearance cookie not found - cookies may not work properly")
                logger.info(f"Available cookies: {list(cookie_dict.keys())}")
            else:
                logger.info(f"✅ cf_clearance cookie found: {cookie_dict['cf_clearance'][:20]}...")
            
            logger.info(f"✅ Extracted {len(cookie_dict)} cookies")
            
            # Save cookies
            self.save_cookies(cookies)
            
            # Cleanup
            self.cleanup()
            
            # Return success even without cf_clearance, but warn
            return {
                "success": True,
                "cookies": cookies,
                "cookie_count": len(cookies),
                "message": f"Successfully fetched {len(cookies)} cookies!" + 
                          ("" if has_cf_clearance else " (Warning: cf_clearance not found)"),
                "has_cf_clearance": has_cf_clearance,
                "warning": None if has_cf_clearance else "cf_clearance cookie not found - may need to retry"
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching cookies: {e}")
            self.cleanup()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to fetch cookies: {str(e)}"
            }
    
    def save_cookies(self, cookies):
        """
        Save cookies to file
        
        Args:
            cookies: List of cookie dictionaries from Selenium
        """
        try:
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"✅ Saved cookies to {self.cookie_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving cookies: {e}")
    
    def cleanup(self):
        """Close browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("🧹 Browser cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")


# Global instance
auto_fetcher = AutoCookieFetcher()
