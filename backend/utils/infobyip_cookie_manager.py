"""
InfoByIP Cookie Manager - Automated Cookie-Based Cloudflare Bypass
Manages cookies for unlimited InfoByIP access without browser overhead
"""

import requests
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class InfoByIPCookieManager:
    """
    Manages cookies for InfoByIP access with automatic expiry detection
    and fallback mechanisms
    """
    
    def __init__(self):
        self.cookie_file = Path(__file__).parent.parent / "infobyip_cookies.json"
        self.session = requests.Session()
        
        # Add browser-like headers to avoid Cloudflare blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        self.cookies_loaded = False
        self.cookies_valid = False
        self.last_check = None
        self.expiry_time = None
        # Load cookies on initialization
        self.load_cookies()
    
    def load_cookies(self) -> bool:
        """
        Load cookies from file and validate them
        
        Returns:
            bool: True if cookies loaded and valid, False otherwise
        """
        try:
            if not self.cookie_file.exists():
                logger.warning(f"Cookie file not found: {self.cookie_file}")
                return False
            
            with open(self.cookie_file, 'r') as f:
                cookie_data = json.load(f)
            
            # Handle different cookie formats
            if isinstance(cookie_data, list):
                # Format from EditThisCookie extension
                for cookie in cookie_data:
                    self.session.cookies.set(
                        cookie.get('name'),
                        cookie.get('value'),
                        domain=cookie.get('domain', '.infobyip.com')
                    )
            elif isinstance(cookie_data, dict):
                # Simple key-value format
                for name, value in cookie_data.items():
                    self.session.cookies.set(name, value, domain='.infobyip.com')
            
            self.cookies_loaded = True
            logger.info(f"✅ Loaded {len(self.session.cookies)} cookies from file")
            
            # Validate cookies
            self.cookies_valid = self.validate_cookies()
            
            if self.cookies_valid:
                # Estimate expiry (24 hours from now)
                self.expiry_time = datetime.now() + timedelta(hours=24)
                logger.info(f"✅ Cookies validated successfully. Expiry: {self.expiry_time}")
            
            return self.cookies_valid
            
        except Exception as e:
            logger.error(f"❌ Error loading cookies: {e}")
            return False
    
    def validate_cookies(self) -> bool:
        """
        Validate cookies by making a test request to InfoByIP
        
        Returns:
            bool: True if cookies are valid, False otherwise
        """
        try:
            # Test with a known IP
            test_url = "https://www.infobyip.com/ip-8.8.8.8.html"
            response = self.session.get(test_url, timeout=10)
            
            # Check if Cloudflare is blocking
            if "Checking your browser" in response.text or "Just a moment" in response.text:
                logger.warning("⚠️ Cloudflare challenge detected - cookies invalid or expired")
                return False
            
            # Check if we got actual data (look for various indicators)
            if any(indicator in response.text for indicator in ["United States", "Google", "IP Address Location", "Country", "infobyip.com"]):
                logger.info("✅ Cookie validation successful - InfoByIP accessible")
                self.last_check = datetime.now()
                return True
            
            # If we got a 200 response and no Cloudflare challenge, consider it valid
            if response.status_code == 200:
                logger.info("✅ Cookies appear valid - got 200 response")
                self.last_check = datetime.now()
                return True
            
            logger.warning("⚠️ Unexpected response - cookies may be invalid")
            return False
            
        except Exception as e:
            logger.error(f"❌ Cookie validation failed: {e}")
            return False
    
    def save_cookies(self, cookies: List[Dict]) -> bool:
        """
        Save cookies to file
        
        Args:
            cookies: List of cookie dictionaries
        
        Returns:
            bool: True if saved successfully
        """
        try:
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"✅ Saved {len(cookies)} cookies to {self.cookie_file}")
            
            # Reload cookies
            return self.load_cookies()
            
        except Exception as e:
            logger.error(f"❌ Error saving cookies: {e}")
            return False
    
    def lookup_ip(self, ip: str) -> Dict:
        """
        Lookup IP information using cookies
        
        Args:
            ip: IP address to lookup
        
        Returns:
            Dict with IP information or error
        """
        if not self.cookies_loaded:
            return {
                "error": "cookies_not_loaded",
                "message": "Cookies not loaded. Please upload cookies first."
            }
        
        if not self.cookies_valid:
            return {
                "error": "cookies_invalid",
                "message": "Cookies are invalid or expired. Please refresh cookies."
            }
        
        try:
            url = f"https://www.infobyip.com/ip-{ip}.html"
            response = self.session.get(url, timeout=10)
            
            # Check for Cloudflare challenge
            if "Checking your browser" in response.text or "Just a moment" in response.text:
                logger.warning(f"⚠️ Cloudflare challenge for IP {ip} - cookies expired")
                self.cookies_valid = False
                return {
                    "error": "cookies_expired",
                    "message": "Cookies expired. Please refresh cookies.",
                    "ip": ip
                }
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data from InfoByIP page
            data = {
                "ip": ip,
                "source": "infobyip",  # Lowercase to match router check
                "country": "Unknown",
                "city": "Unknown",
                "region": "Unknown",
                "isp": "Unknown",
                "organization": "Unknown",
                "postal_code": "",
                "latitude": "",
                "longitude": "",
                "timezone": ""
            }
            
            # Try multiple parsing methods
            # Method 1: Find table rows
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if value and value != '-':  # Only update if we have a value
                        if 'country' in label:
                            data['country'] = value
                        elif 'city' in label:
                            data['city'] = value
                        elif 'region' in label or 'state' in label:
                            data['region'] = value
                        elif 'isp' in label:
                            data['isp'] = value
                        elif 'organization' in label:
                            data['organization'] = value
                        elif 'postal' in label or 'zip' in label:
                            data['postal_code'] = value
                        elif 'latitude' in label:
                            data['latitude'] = value
                        elif 'longitude' in label:
                            data['longitude'] = value
                        elif 'timezone' in label or 'time zone' in label:
                            data['timezone'] = value
            
            # Method 2: Try finding specific divs/spans (InfoByIP might use different structure)
            if data['country'] == 'Unknown':
                # Try alternative selectors
                country_elem = soup.find(string=lambda text: text and 'Country' in text)
                if country_elem:
                    parent = country_elem.find_parent()
                    if parent:
                        next_elem = parent.find_next_sibling()
                        if next_elem:
                            data['country'] = next_elem.get_text(strip=True)
            
            # Log what we found
            found_data = sum(1 for v in [data['country'], data['city'], data['region'], data['isp']] if v != 'Unknown')
            logger.info(f"✅ Successfully looked up IP {ip} via cookies (found {found_data}/4 fields)")
            
            # If we didn't find any data, log the HTML structure for debugging
            if found_data == 0:
                logger.warning(f"⚠️ No data extracted for {ip}. Page might have different structure.")
                logger.debug(f"HTML preview: {response.text[:500]}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error looking up IP {ip}: {e}")
            return {
                "error": "lookup_failed",
                "message": f"Lookup failed: {str(e)}",
                "ip": ip
            }
    
    def get_status(self) -> Dict:
        """
        Get current cookie status
        
        Returns:
            Dict with status information
        """
        status = {
            "cookies_loaded": self.cookies_loaded,
            "cookies_valid": self.cookies_valid,
            "cookie_count": len(self.session.cookies),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "expiry_time": self.expiry_time.isoformat() if self.expiry_time else None,
            "needs_refresh": False
        }
        
        # Check if cookies need refresh
        if self.expiry_time and datetime.now() > self.expiry_time:
            status["needs_refresh"] = True
            status["message"] = "Cookies expired. Please refresh."
        elif not self.cookies_valid:
            status["needs_refresh"] = True
            status["message"] = "Cookies invalid. Please upload new cookies."
        elif not self.cookies_loaded:
            status["needs_refresh"] = True
            status["message"] = "No cookies loaded. Please upload cookies."
        else:
            hours_remaining = (self.expiry_time - datetime.now()).total_seconds() / 3600 if self.expiry_time else 0
            status["message"] = f"Cookies valid. {hours_remaining:.1f} hours remaining."
        
        return status
    
    def refresh_validation(self) -> bool:
        """
        Re-validate cookies (useful for checking if they're still working)
        
        Returns:
            bool: True if cookies are still valid
        """
        logger.info("🔄 Refreshing cookie validation...")
        self.cookies_valid = self.validate_cookies()
        return self.cookies_valid


# Global instance
cookie_manager = InfoByIPCookieManager()
