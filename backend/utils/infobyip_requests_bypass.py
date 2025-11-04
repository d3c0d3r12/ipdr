"""
InfoByIP Requests-Based Bypass
Works on Render.com without browser/Selenium
Uses advanced request techniques to bypass Cloudflare
"""

import requests
import time
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
import cloudscraper

logger = logging.getLogger(__name__)


class InfoByIPRequestsBypass:
    """
    Bypass Cloudflare using cloudscraper (no browser needed)
    Works on serverless environments like Render.com
    """
    
    def __init__(self):
        # Use cloudscraper - automatically handles Cloudflare challenges
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=10  # Delay to avoid rate limiting
        )
        
        # Add realistic headers
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
    
    def lookup_ip(self, ip: str, max_retries: int = 3) -> Dict:
        """
        Lookup IP using cloudscraper (bypasses Cloudflare without browser)
        
        Args:
            ip: IP address to lookup
            max_retries: Maximum number of retry attempts
        
        Returns:
            Dict with IP information
        """
        url = f"https://www.infobyip.com/ip-{ip}.html"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Looking up {ip} via cloudscraper (attempt {attempt + 1}/{max_retries})")
                
                # Make request with cloudscraper (handles Cloudflare automatically)
                response = self.scraper.get(url, timeout=30)
                
                # Check if we got blocked
                if response.status_code == 403:
                    logger.warning(f"⚠️ Got 403 for {ip}, retrying...")
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                    continue
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Got status {response.status_code} for {ip}")
                    continue
                
                # Check for Cloudflare challenge
                if "Checking your browser" in response.text or "Just a moment" in response.text:
                    logger.warning(f"⚠️ Cloudflare challenge detected for {ip}, retrying...")
                    time.sleep(5 * (attempt + 1))
                    continue
                
                # Check for Cloudflare block page
                if "Sorry, you have been blocked" in response.text:
                    logger.warning(f"⚠️ Cloudflare blocked request for {ip}, retrying...")
                    time.sleep(5 * (attempt + 1))
                    continue
                
                # Parse the response
                data = self._parse_html(response.text, ip)
                
                # Check if we got data
                if data.get('country') != 'Unknown' or data.get('city') != 'Unknown':
                    logger.info(f"✅ Successfully looked up {ip} (Country: {data.get('country')})")
                    return data
                else:
                    # Log HTML snippet for debugging
                    logger.warning(f"⚠️ No data found for {ip}")
                    logger.debug(f"HTML preview: {response.text[:500]}")
                    logger.warning(f"Retrying...")
                    time.sleep(2)
                    continue
                
            except Exception as e:
                logger.error(f"❌ Error looking up {ip}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
        
        # All retries failed
        logger.error(f"❌ All retries failed for {ip}")
        return {
            "ip": ip,
            "source": "infobyip",
            "error": "lookup_failed",
            "message": "Failed to lookup IP after multiple retries"
        }
    
    def _parse_html(self, html: str, ip: str) -> Dict:
        """
        Parse InfoByIP HTML to extract data
        
        Args:
            html: HTML content
            ip: IP address
        
        Returns:
            Dict with extracted data
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "ip": ip,
            "source": "infobyip",
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
        
        # Method 1: Find table rows
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                
                if value and value != '-':
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
        
        # Method 2: Try finding divs with specific classes (if InfoByIP uses them)
        # This is a fallback method
        if data['country'] == 'Unknown':
            # Try to find country in different ways
            for tag in soup.find_all(['div', 'span', 'p']):
                text = tag.get_text(strip=True)
                if 'Country:' in text:
                    # Extract value after "Country:"
                    parts = text.split('Country:')
                    if len(parts) > 1:
                        data['country'] = parts[1].strip().split()[0]
        
        return data


# Global instance
infobyip_bypass = InfoByIPRequestsBypass()
