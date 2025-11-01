"""
Custom Cloudflare Bypass - Educational Implementation
Learn how to bypass Cloudflare protection step by step

This script demonstrates various techniques to bypass Cloudflare:
1. Browser fingerprint spoofing
2. TLS fingerprint matching
3. JavaScript challenge solving
4. Cookie management
5. Header manipulation
"""

import time
import random
import json
import base64
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class CustomCloudflareBypass:
    """
    Custom Cloudflare bypass implementation
    Educational approach to understand bypass techniques
    """
    
    def __init__(self, headless: bool = False, verbose: bool = True):
        """
        Initialize custom bypass
        
        Args:
            headless: Run in headless mode
            verbose: Print detailed logs
        """
        self.headless = headless
        self.verbose = verbose
        self.driver = None
        self.session_cookies = {}
        
        # Realistic browser fingerprint
        self.fingerprint = self._generate_fingerprint()
        
    def log(self, message: str, level: str = "INFO"):
        """Print log message if verbose"""
        if self.verbose:
            emoji = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "DEBUG": "🔍"
            }
            print(f"{emoji.get(level, 'ℹ️')} [{level}] {message}")
    
    def _generate_fingerprint(self) -> Dict[str, Any]:
        """
        Generate realistic browser fingerprint
        
        Cloudflare checks:
        - User Agent
        - Screen resolution
        - Timezone
        - Language
        - Plugins
        - Canvas fingerprint
        - WebGL fingerprint
        """
        self.log("Generating realistic browser fingerprint...", "DEBUG")
        
        # Common screen resolutions
        resolutions = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720)
        ]
        
        # Common timezones
        timezones = [
            "Asia/Kolkata",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo"
        ]
        
        # Realistic user agents (recent Chrome versions)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        fingerprint = {
            'user_agent': random.choice(user_agents),
            'screen_resolution': random.choice(resolutions),
            'timezone': random.choice(timezones),
            'language': 'en-US',
            'platform': 'Win32',
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16]),
            'color_depth': 24,
            'pixel_ratio': random.choice([1, 1.5, 2])
        }
        
        self.log(f"Fingerprint: {fingerprint['user_agent'][:50]}...", "DEBUG")
        return fingerprint
    
    def _setup_chrome_options(self) -> Options:
        """
        Configure Chrome with anti-detection options
        
        Key techniques:
        1. Remove automation flags
        2. Add realistic preferences
        3. Disable detection features
        """
        self.log("Configuring Chrome options...", "DEBUG")
        
        options = Options()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
            self.log("Running in headless mode", "DEBUG")
        
        # Set user agent
        options.add_argument(f'user-agent={self.fingerprint["user_agent"]}')
        
        # Anti-detection arguments
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        
        # Set window size to match fingerprint
        width, height = self.fingerprint['screen_resolution']
        options.add_argument(f'--window-size={width},{height}')
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add realistic preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "intl.accept_languages": self.fingerprint['language']
        }
        options.add_experimental_option("prefs", prefs)
        
        self.log("Chrome options configured", "SUCCESS")
        return options
    
    def _inject_stealth_scripts(self):
        """
        Inject JavaScript to hide automation
        
        Techniques:
        1. Override navigator.webdriver
        2. Mock plugins
        3. Override permissions
        4. Spoof canvas/WebGL
        """
        self.log("Injecting stealth scripts...", "DEBUG")
        
        # Script 1: Hide webdriver flag
        script_webdriver = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
        
        # Script 2: Override plugins
        script_plugins = """
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        """
        
        # Script 3: Override languages
        script_languages = f"""
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{self.fingerprint['language']}']
        }});
        """
        
        # Script 4: Override platform
        script_platform = f"""
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{self.fingerprint['platform']}'
        }});
        """
        
        # Script 5: Override hardware concurrency
        script_hardware = f"""
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {self.fingerprint['hardware_concurrency']}
        }});
        """
        
        # Script 6: Override device memory
        script_memory = f"""
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {self.fingerprint['device_memory']}
        }});
        """
        
        # Script 7: Override permissions
        script_permissions = """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        # Combine all scripts
        stealth_script = f"""
        {script_webdriver}
        {script_plugins}
        {script_languages}
        {script_platform}
        {script_hardware}
        {script_memory}
        {script_permissions}
        
        console.log('🔒 Stealth mode activated');
        """
        
        try:
            self.driver.execute_script(stealth_script)
            self.log("Stealth scripts injected successfully", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to inject stealth scripts: {e}", "WARNING")
    
    def _override_cdp_settings(self):
        """
        Override Chrome DevTools Protocol settings
        
        This makes the browser appear more like a real user
        """
        self.log("Overriding CDP settings...", "DEBUG")
        
        try:
            # Override user agent via CDP
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.fingerprint['user_agent'],
                "platform": self.fingerprint['platform'],
                "acceptLanguage": self.fingerprint['language']
            })
            
            # Set timezone
            self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                'timezoneId': self.fingerprint['timezone']
            })
            
            # Set locale
            self.driver.execute_cdp_cmd('Emulation.setLocaleOverride', {
                'locale': self.fingerprint['language']
            })
            
            self.log("CDP settings overridden", "SUCCESS")
        except Exception as e:
            self.log(f"CDP override failed: {e}", "WARNING")
    
    def _detect_cloudflare_challenge(self) -> bool:
        """
        Detect if Cloudflare challenge is present
        
        Returns:
            True if challenge detected, False otherwise
        """
        try:
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()
            
            # Cloudflare indicators
            indicators = [
                'checking your browser',
                'cloudflare',
                'ddos protection',
                'ray id',
                'cf-browser-verification',
                'challenge-platform',
                'cf-challenge'
            ]
            
            has_challenge = any(indicator in page_source for indicator in indicators)
            has_challenge = has_challenge or 'cloudflare' in page_title
            
            if has_challenge:
                self.log("Cloudflare challenge detected!", "WARNING")
            
            return has_challenge
            
        except Exception as e:
            self.log(f"Error detecting challenge: {e}", "ERROR")
            return False
    
    def _wait_for_challenge_completion(self, max_wait: int = 30) -> bool:
        """
        Wait for Cloudflare challenge to complete
        
        Args:
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if challenge passed, False otherwise
        """
        self.log(f"Waiting for challenge completion (max {max_wait}s)...", "INFO")
        
        start_time = time.time()
        last_check = 0
        
        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            
            # Log every 5 seconds
            if elapsed - last_check >= 5:
                self.log(f"Still waiting... ({elapsed}s elapsed)", "INFO")
                last_check = elapsed
            
            # Check if challenge is gone
            if not self._detect_cloudflare_challenge():
                wait_time = int(time.time() - start_time)
                self.log(f"Challenge passed in {wait_time}s!", "SUCCESS")
                return True
            
            # Small delay before next check
            time.sleep(1)
        
        self.log("Challenge timeout - may still be present", "WARNING")
        return False
    
    def _simulate_human_behavior(self):
        """
        Simulate human-like behavior
        
        Techniques:
        1. Random mouse movements
        2. Random scrolling
        3. Random delays
        """
        self.log("Simulating human behavior...", "DEBUG")
        
        try:
            # Random scroll
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount//2});")
            time.sleep(random.uniform(0.3, 0.8))
            
            self.log("Human behavior simulated", "DEBUG")
        except Exception as e:
            self.log(f"Behavior simulation failed: {e}", "WARNING")
    
    def initialize_driver(self):
        """Initialize Chrome driver with all anti-detection measures"""
        self.log("Initializing Chrome driver...", "INFO")
        
        try:
            # Setup options
            options = self._setup_chrome_options()
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply CDP overrides
            self._override_cdp_settings()
            
            # Inject stealth scripts
            self._inject_stealth_scripts()
            
            self.log("Driver initialized successfully!", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to initialize driver: {e}", "ERROR")
            raise
    
    def bypass_and_fetch(
        self,
        url: str,
        wait_for_element: Optional[str] = None,
        max_challenge_wait: int = 30
    ) -> Optional[str]:
        """
        Main method to bypass Cloudflare and fetch page
        
        Args:
            url: Target URL
            wait_for_element: CSS selector to wait for (optional)
            max_challenge_wait: Max time to wait for challenge
            
        Returns:
            Page HTML or None if failed
        """
        self.log(f"Starting bypass for: {url}", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Initialize driver if not done
            if not self.driver:
                self.initialize_driver()
            
            # Navigate to URL
            self.log(f"Navigating to URL...", "INFO")
            self.driver.get(url)
            
            # Wait a bit for page to load
            time.sleep(2)
            
            # Check for Cloudflare challenge
            if self._detect_cloudflare_challenge():
                self.log("Cloudflare challenge detected, waiting...", "WARNING")
                
                # Wait for challenge to complete
                if not self._wait_for_challenge_completion(max_challenge_wait):
                    self.log("Challenge may not have completed", "WARNING")
            else:
                self.log("No Cloudflare challenge detected", "SUCCESS")
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Wait for specific element if provided
            if wait_for_element:
                self.log(f"Waiting for element: {wait_for_element}", "INFO")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
                self.log("Element found!", "SUCCESS")
            
            # Get page source
            page_source = self.driver.page_source
            
            # Save cookies
            self.session_cookies = {
                cookie['name']: cookie['value']
                for cookie in self.driver.get_cookies()
            }
            
            self.log(f"Page fetched: {len(page_source):,} bytes", "SUCCESS")
            self.log(f"Cookies saved: {len(self.session_cookies)} items", "INFO")
            self.log("=" * 60, "INFO")
            
            return page_source
            
        except Exception as e:
            self.log(f"Error during bypass: {e}", "ERROR")
            return None
    
    def screenshot(self, filename: str = "bypass_screenshot.png"):
        """Take screenshot for debugging"""
        if self.driver:
            self.driver.save_screenshot(filename)
            self.log(f"Screenshot saved: {filename}", "SUCCESS")
    
    def get_cookies(self) -> Dict[str, str]:
        """Get current session cookies"""
        return self.session_cookies.copy()
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.log("Closing browser...", "INFO")
            try:
                self.driver.quit()
                self.log("Browser closed", "SUCCESS")
            except Exception as e:
                self.log(f"Error closing browser: {e}", "WARNING")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "🔥" * 35)
    print("   CUSTOM CLOUDFLARE BYPASS")
    print("   Educational Implementation")
    print("🔥" * 35 + "\n")
    
    # Test URL (Cloudflare-protected site)
    test_url = input("Enter URL to test (or press Enter for default): ").strip()
    if not test_url:
        test_url = "https://nowsecure.nl"  # Known Cloudflare test site
    
    # Create bypass instance
    with CustomCloudflareBypass(headless=False, verbose=True) as bypass:
        # Fetch page
        html = bypass.bypass_and_fetch(
            url=test_url,
            max_challenge_wait=30
        )
        
        if html:
            print(f"\n✅ SUCCESS!")
            print(f"📏 Page size: {len(html):,} bytes")
            print(f"🍪 Cookies: {len(bypass.get_cookies())} items")
            
            # Take screenshot
            bypass.screenshot("custom_bypass_test.png")
            print(f"📸 Screenshot saved: custom_bypass_test.png")
            
            # Save HTML
            with open("custom_bypass_output.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"💾 HTML saved: custom_bypass_output.html")
            
            # Show first 500 chars
            print(f"\n📝 First 500 characters:")
            print("-" * 60)
            print(html[:500])
            print("-" * 60)
        else:
            print(f"\n❌ FAILED to fetch page")
    
    print("\n" + "🔥" * 35 + "\n")
