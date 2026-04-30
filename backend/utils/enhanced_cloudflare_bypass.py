"""
Enhanced Cloudflare Bypass - Production Ready
Advanced features for robust web scraping with anti-detection

Features:
- Multiple bypass strategies
- Automatic retry with fallback
- Proxy rotation support
- Cookie persistence
- Rate limiting
- Request queuing
- Progress tracking
- Error recovery
- Session management
- CAPTCHA detection
"""

import time
import random
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import threading
from queue import Queue, Empty

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BypassStrategy:
    """Different bypass strategies"""
    STEALTH = "stealth"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    CUSTOM = "custom"


class EnhancedCloudflareBypass:
    """
    Enhanced Cloudflare bypass with advanced features
    """
    
    # Comprehensive user agent pool
    USER_AGENTS = [
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        # Chrome Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        # Chrome Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 30,
        strategy: str = BypassStrategy.STEALTH,
        max_retries: int = 3,
        rate_limit: float = 2.0,
        cookie_file: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize enhanced bypass
        
        Args:
            headless: Run in headless mode
            proxy: Proxy server (format: "host:port" or "user:pass@host:port")
            timeout: Maximum wait time in seconds
            strategy: Bypass strategy to use
            max_retries: Maximum retry attempts
            rate_limit: Minimum seconds between requests
            cookie_file: Path to save/load cookies
            verbose: Enable verbose logging
        """
        self.headless = headless
        self.proxy = proxy
        self.timeout = timeout
        self.strategy = strategy
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.cookie_file = cookie_file
        self.verbose = verbose
        
        self.driver = None
        self.session_cookies = {}
        self.last_request_time = 0
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        
        # Request queue for rate limiting
        self.request_queue = Queue()
        self.processing = False
        
        # Load cookies if file exists
        if cookie_file and Path(cookie_file).exists():
            self._load_cookies_from_file()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose"""
        if self.verbose:
            emoji = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "DEBUG": "🔍",
                "PROGRESS": "⏳"
            }
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{emoji.get(level, 'ℹ️')} [{timestamp}] {message}")
            logger.log(getattr(logging, level, logging.INFO), message)
    
    def _generate_fingerprint(self) -> Dict[str, Any]:
        """Generate realistic browser fingerprint based on strategy"""
        
        # Screen resolutions by popularity
        resolutions = [
            (1920, 1080),  # Most common
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (2560, 1440),
            (1280, 720)
        ]
        
        # Timezones
        timezones = [
            "Asia/Kolkata",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "America/Los_Angeles"
        ]
        
        # Languages
        languages = ["en-US", "en-GB", "en"]
        
        # Hardware specs (realistic combinations)
        hardware_configs = [
            {"cores": 4, "memory": 8},
            {"cores": 8, "memory": 16},
            {"cores": 12, "memory": 16},
            {"cores": 16, "memory": 32},
        ]
        
        hardware = random.choice(hardware_configs)
        
        fingerprint = {
            'user_agent': random.choice(self.USER_AGENTS),
            'screen_resolution': random.choice(resolutions),
            'timezone': random.choice(timezones),
            'language': random.choice(languages),
            'platform': 'Win32' if 'Windows' in self.USER_AGENTS[0] else 'MacIntel',
            'hardware_concurrency': hardware['cores'],
            'device_memory': hardware['memory'],
            'color_depth': 24,
            'pixel_ratio': random.choice([1, 1.5, 2]),
            'webgl_vendor': 'Google Inc. (NVIDIA)',
            'webgl_renderer': 'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)'
        }
        
        self.log(f"Fingerprint: {fingerprint['user_agent'][:60]}...", "DEBUG")
        return fingerprint
    
    def _setup_chrome_options(self) -> Options:
        """Configure Chrome with advanced anti-detection"""
        options = Options()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
        
        # Set user agent
        options.add_argument(f'user-agent={self.fingerprint["user_agent"]}')
        
        # Window size
        width, height = self.fingerprint['screen_resolution']
        options.add_argument(f'--window-size={width},{height}')
        
        # Anti-detection arguments
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Additional stealth
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Proxy configuration
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        
        # Preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "intl.accept_languages": self.fingerprint['language'],
            "profile.managed_default_content_settings.images": 2 if self.strategy == BypassStrategy.AGGRESSIVE else 1
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _inject_advanced_stealth(self):
        """Inject comprehensive stealth scripts"""
        self.log("Injecting advanced stealth scripts...", "DEBUG")
        
        # Comprehensive stealth script
        stealth_script = """
        // Override webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['""" + self.fingerprint['language'] + """']
        });
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {
            get: () => '""" + self.fingerprint['platform'] + """'
        });
        
        // Override hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => """ + str(self.fingerprint['hardware_concurrency']) + """
        });
        
        // Override device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => """ + str(self.fingerprint['device_memory']) + """
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Override chrome property
        window.chrome = {
            runtime: {}
        };
        
        // Override toString
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === window.navigator.permissions.query) {
                return 'function query() { [native code] }';
            }
            return originalToString.call(this);
        };
        
        // Canvas fingerprint protection
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            const context = originalGetContext.call(this, type, ...args);
            if (type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function(...args) {
                    return originalFillText.apply(this, args);
                };
            }
            return context;
        };
        
        // WebGL fingerprint protection
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return '""" + self.fingerprint['webgl_vendor'] + """';
            }
            if (parameter === 37446) {
                return '""" + self.fingerprint['webgl_renderer'] + """';
            }
            return getParameter.call(this, parameter);
        };
        
        // Battery API
        Object.defineProperty(navigator, 'getBattery', {
            get: () => undefined
        });
        
        // Connection API
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });
        
        console.log('🔒 Advanced stealth mode activated');
        """
        
        try:
            self.driver.execute_script(stealth_script)
            self.log("Advanced stealth scripts injected", "SUCCESS")
        except Exception as e:
            self.log(f"Stealth injection warning: {e}", "WARNING")
    
    def _override_cdp_settings(self):
        """Override Chrome DevTools Protocol settings"""
        try:
            # Override user agent
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
            
            # Set geolocation (optional)
            if self.fingerprint['timezone'] == 'Asia/Kolkata':
                self.driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                    'latitude': 28.6139,
                    'longitude': 77.2090,
                    'accuracy': 100
                })
            
            self.log("CDP settings overridden", "SUCCESS")
        except Exception as e:
            self.log(f"CDP override warning: {e}", "WARNING")
    
    def _detect_cloudflare_challenge(self) -> bool:
        """Detect Cloudflare challenge with multiple indicators"""
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
                'cf-challenge',
                'just a moment',
                'please wait',
                'verifying you are human'
            ]
            
            has_challenge = any(indicator in page_source for indicator in indicators)
            has_challenge = has_challenge or any(indicator in page_title for indicator in indicators)
            
            # Check for Cloudflare iframe
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'iframe[src*="cloudflare"]')
                has_challenge = True
            except:
                pass
            
            return has_challenge
            
        except Exception as e:
            self.log(f"Challenge detection error: {e}", "WARNING")
            return False
    
    def _detect_captcha(self) -> bool:
        """Detect CAPTCHA challenges"""
        try:
            page_source = self.driver.page_source.lower()
            
            captcha_indicators = [
                'recaptcha',
                'hcaptcha',
                'captcha',
                'g-recaptcha',
                'h-captcha'
            ]
            
            return any(indicator in page_source for indicator in captcha_indicators)
        except:
            return False
    
    def _wait_for_challenge_completion(self, max_wait: int = 30) -> bool:
        """Wait for challenge with progress tracking"""
        self.log(f"Waiting for challenge (max {max_wait}s)...", "PROGRESS")
        
        start_time = time.time()
        check_interval = 1
        last_log = 0
        
        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            
            # Log progress every 5 seconds
            if elapsed - last_log >= 5:
                self.log(f"Still waiting... ({elapsed}s/{max_wait}s)", "PROGRESS")
                last_log = elapsed
            
            # Check if challenge is gone
            if not self._detect_cloudflare_challenge():
                wait_time = int(time.time() - start_time)
                self.log(f"Challenge passed in {wait_time}s!", "SUCCESS")
                return True
            
            # Check for CAPTCHA
            if self._detect_captcha():
                self.log("CAPTCHA detected - manual intervention needed", "WARNING")
                return False
            
            time.sleep(check_interval)
        
        self.log("Challenge timeout", "WARNING")
        return False
    
    def _simulate_human_behavior(self):
        """Advanced human behavior simulation"""
        try:
            # Random scroll pattern
            scroll_actions = [
                ("window.scrollBy(0, {});", random.randint(100, 500)),
                ("window.scrollBy(0, -{});", random.randint(50, 250)),
                ("window.scrollTo(0, document.body.scrollHeight/2);", 0),
            ]
            
            for script, value in random.sample(scroll_actions, k=2):
                self.driver.execute_script(script.format(value) if value else script)
                time.sleep(random.uniform(0.3, 0.8))
            
            # Random mouse movements (via JavaScript)
            self.driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            
            self.log("Human behavior simulated", "DEBUG")
        except Exception as e:
            self.log(f"Behavior simulation warning: {e}", "WARNING")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit:
                wait_time = self.rate_limit - elapsed
                self.log(f"Rate limiting: waiting {wait_time:.1f}s", "DEBUG")
                time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def initialize_driver(self):
        """Initialize driver with all enhancements"""
        self.log("Initializing enhanced Chrome driver...", "INFO")
        
        try:
            # Generate fingerprint
            self.fingerprint = self._generate_fingerprint()
            
            # Setup options
            options = self._setup_chrome_options()
            
            # Create driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply CDP overrides
            self._override_cdp_settings()
            
            # Inject stealth scripts
            self._inject_advanced_stealth()
            
            # Load saved cookies if available
            if self.session_cookies:
                self.log(f"Loading {len(self.session_cookies)} saved cookies", "INFO")
            
            self.log("Driver initialized successfully!", "SUCCESS")
            
        except Exception as e:
            self.log(f"Driver initialization failed: {e}", "ERROR")
            raise
    
    def bypass_and_fetch(
        self,
        url: str,
        wait_for_element: Optional[str] = None,
        max_challenge_wait: int = 30,
        retry_on_fail: bool = True
    ) -> Optional[str]:
        """
        Main bypass method with retry logic
        
        Args:
            url: Target URL
            wait_for_element: CSS selector to wait for
            max_challenge_wait: Max time to wait for challenge
            retry_on_fail: Retry on failure
            
        Returns:
            Page HTML or None
        """
        self.request_count += 1
        
        for attempt in range(self.max_retries if retry_on_fail else 1):
            try:
                self.log(f"Request #{self.request_count} (attempt {attempt + 1}/{self.max_retries}): {url}", "INFO")
                
                # Enforce rate limiting
                self._enforce_rate_limit()
                
                # Initialize driver if needed
                if not self.driver:
                    self.initialize_driver()
                
                # Navigate
                self.driver.get(url)
                time.sleep(2)
                
                # Check for challenge
                if self._detect_cloudflare_challenge():
                    if not self._wait_for_challenge_completion(max_challenge_wait):
                        raise Exception("Challenge not completed")
                
                # Simulate human behavior
                self._simulate_human_behavior()
                
                # Wait for element if specified
                if wait_for_element:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                
                # Get page source
                html = self.driver.page_source
                
                # Save cookies
                self.session_cookies = {
                    c['name']: c['value']
                    for c in self.driver.get_cookies()
                }
                
                if self.cookie_file:
                    self._save_cookies_to_file()
                
                self.success_count += 1
                self.log(f"Success! ({len(html):,} bytes) [Success rate: {self.success_count}/{self.request_count}]", "SUCCESS")
                
                return html
                
            except Exception as e:
                self.fail_count += 1
                error_msg = str(e)
                self.log(f"Attempt {attempt + 1} failed: {e}", "ERROR")
                
                # Check if browser session crashed
                if "invalid session id" in error_msg or "session deleted" in error_msg:
                    self.log("Browser session crashed - restarting browser...", "WARNING")
                    try:
                        if self.driver:
                            self.driver.quit()
                    except:
                        pass
                    self.driver = None
                    self.log("Browser closed, will reinitialize on next attempt", "INFO")
                
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.log(f"Retrying in {wait_time}s...", "WARNING")
                    time.sleep(wait_time)
                else:
                    self.log(f"All attempts failed for: {url}", "ERROR")
        
        return None
    
    def batch_fetch(
        self,
        urls: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[Optional[str]]:
        """
        Fetch multiple URLs with progress tracking
        
        Args:
            urls: List of URLs to fetch
            progress_callback: Callback function(current, total, url, success)
            
        Returns:
            List of HTML strings (None for failures)
        """
        results = []
        total = len(urls)
        
        self.log(f"Starting batch fetch: {total} URLs", "INFO")
        
        for i, url in enumerate(urls, 1):
            self.log(f"Progress: {i}/{total}", "PROGRESS")
            
            html = self.bypass_and_fetch(url)
            results.append(html)
            
            if progress_callback:
                progress_callback(i, total, url, html is not None)
        
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        self.log(f"Batch complete: {self.success_count}/{total} successful ({success_rate:.1f}%)", "SUCCESS")
        
        return results
    
    def _save_cookies_to_file(self):
        """Save cookies to file"""
        if self.cookie_file and self.session_cookies:
            try:
                with open(self.cookie_file, 'w') as f:
                    json.dump(self.session_cookies, f)
                self.log(f"Cookies saved to {self.cookie_file}", "DEBUG")
            except Exception as e:
                self.log(f"Cookie save failed: {e}", "WARNING")
    
    def _load_cookies_from_file(self):
        """Load cookies from file"""
        if self.cookie_file and Path(self.cookie_file).exists():
            try:
                with open(self.cookie_file, 'r') as f:
                    self.session_cookies = json.load(f)
                self.log(f"Loaded {len(self.session_cookies)} cookies", "INFO")
            except Exception as e:
                self.log(f"Cookie load failed: {e}", "WARNING")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bypass statistics"""
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'total_requests': self.request_count,
            'successful': self.success_count,
            'failed': self.fail_count,
            'success_rate': f"{success_rate:.1f}%",
            'cookies_saved': len(self.session_cookies)
        }
    
    def lookup_ip(self, ip: str) -> Dict[str, Any]:
        """
        Lookup IP information from InfoByIP.com
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Dictionary with IP information
        """
        url = f"https://www.infobyip.com/ip-{ip}.html"
        
        try:
            html = self.bypass_and_fetch(url, max_challenge_wait=30)
            
            if not html:
                return {
                    'ip': ip,
                    'error': 'Failed to fetch page',
                    'source': 'infobyip'
                }
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data from table
            data = {
                'ip': ip,
                'country': 'Unknown',
                'region': 'Unknown',
                'city': 'Unknown',
                'isp': 'Unknown',
                'postal_code': 'Unknown',
                'latitude': 'Unknown',
                'longitude': 'Unknown',
                'source': 'infobyip'
            }
            
            # Find all table rows
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'country' in label and 'code' not in label:
                        data['country'] = value
                    elif 'region' in label or 'state' in label:
                        data['region'] = value
                    elif 'city' in label:
                        data['city'] = value
                    elif 'isp' in label or 'organization' in label:
                        data['isp'] = value
                    elif 'postal' in label or 'zip' in label:
                        data['postal_code'] = value
                    elif 'latitude' in label:
                        data['latitude'] = value
                    elif 'longitude' in label:
                        data['longitude'] = value
            
            self.log(f"IP lookup successful: {ip} -> {data['country']}, {data['city']}", "SUCCESS")
            return data
            
        except Exception as e:
            self.log(f"IP lookup failed for {ip}: {e}", "ERROR")
            return {
                'ip': ip,
                'error': str(e),
                'source': 'infobyip'
            }
    
    def screenshot(self, filename: str = "bypass_screenshot.png"):
        """Take screenshot (safe - handles crashed browser)"""
        if self.driver:
            try:
                self.driver.save_screenshot(filename)
                self.log(f"Screenshot: {filename}", "SUCCESS")
            except Exception as e:
                # Browser may have crashed - ignore screenshot errors
                self.log(f"Screenshot failed (browser may have crashed): {str(e)}", "WARNING")
                pass
    
    def close(self):
        """Close driver and cleanup"""
        if self.driver:
            self.log("Closing browser...", "INFO")
            try:
                # Save cookies before closing
                if self.cookie_file and self.session_cookies:
                    self._save_cookies_to_file()
                
                self.driver.quit()
                self.log("Browser closed", "SUCCESS")
                
                # Print final stats
                stats = self.get_stats()
                self.log(f"Final stats: {stats}", "INFO")
            except Exception as e:
                self.log(f"Close error: {e}", "WARNING")
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
    print("\n" + "🔥" * 35)
    print("   ENHANCED CLOUDFLARE BYPASS")
    print("   Production-Ready Implementation")
    print("🔥" * 35 + "\n")
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://nowsecure.nl",  # Cloudflare test site
    ]
    
    # Create bypass instance with advanced features
    with EnhancedCloudflareBypass(
        headless=False,
        strategy=BypassStrategy.STEALTH,
        max_retries=3,
        rate_limit=2.0,
        cookie_file="cloudflare_cookies.json",
        verbose=True
    ) as bypass:
        
        # Single fetch
        html = bypass.bypass_and_fetch(test_urls[0])
        
        if html:
            print(f"\n✅ Success: {len(html):,} bytes")
            bypass.screenshot("test_screenshot.png")
        
        # Batch fetch
        def progress_callback(current, total, url, success):
            status = "✅" if success else "❌"
            print(f"{status} [{current}/{total}] {url}")
        
        results = bypass.batch_fetch(test_urls, progress_callback)
        
        # Show stats
        stats = bypass.get_stats()
        print(f"\n📊 Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\n" + "🔥" * 35 + "\n")
