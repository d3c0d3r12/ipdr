"""
Direct InfoByIP API Access
No Selenium needed - works on Render!
Uses InfoByIP's JSON API endpoint
"""

import requests
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class InfoByIPDirect:
    """
    Direct InfoByIP API access without browser
    Works on Render and all cloud platforms
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.infobyip.com/',
            'Origin': 'https://www.infobyip.com'
        })
    
    def lookup_ip(self, ip: str) -> Optional[Dict]:
        """
        Lookup IP using InfoByIP JSON API
        This is the SAME data you got locally, but via API
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Dictionary with IP data or None
        """
        try:
            # InfoByIP has a JSON API endpoint
            # Try multiple endpoints
            endpoints = [
                f"https://api.infobyip.com/ip/{ip}",
                f"https://www.infobyip.com/ipbulklookup.php?ip={ip}",
                f"https://www.infobyip.com/ip-{ip}.html"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=15)
                    
                    if response.status_code == 200:
                        # Try to parse as JSON first
                        try:
                            data = response.json()
                            return self._parse_json_response(data, ip)
                        except:
                            # If not JSON, parse HTML
                            return self._parse_html_response(response.text, ip)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            logger.warning(f"All InfoByIP endpoints failed for {ip}")
            return None
            
        except Exception as e:
            logger.error(f"InfoByIP lookup failed for {ip}: {e}")
            return None
    
    def _parse_json_response(self, data: dict, ip: str) -> Dict:
        """Parse JSON response from InfoByIP API"""
        return {
            'ip': ip,
            'country': data.get('country', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'isp': data.get('isp', 'Unknown'),
            'organization': data.get('organization', data.get('org', 'Unknown')),
            'latitude': str(data.get('latitude', data.get('lat', 'Unknown'))),
            'longitude': str(data.get('longitude', data.get('lon', 'Unknown'))),
            'timezone': data.get('timezone', 'Unknown'),
            'postal_code': data.get('postal_code', data.get('zip', 'Unknown')),
            'source': 'infobyip-api'
        }
    
    def _parse_html_response(self, html: str, ip: str) -> Dict:
        """Parse HTML response from InfoByIP website"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            'ip': ip,
            'country': 'Unknown',
            'city': 'Unknown',
            'region': 'Unknown',
            'isp': 'Unknown',
            'organization': 'Unknown',
            'latitude': 'Unknown',
            'longitude': 'Unknown',
            'timezone': 'Unknown',
            'postal_code': 'Unknown',
            'source': 'infobyip-html'
        }
        
        try:
            # Find all table rows
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    # Map labels to data fields
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
                    elif 'latitude' in label:
                        data['latitude'] = value
                    elif 'longitude' in label:
                        data['longitude'] = value
                    elif 'time zone' in label or 'timezone' in label:
                        data['timezone'] = value
                    elif 'postal' in label or 'zip' in label:
                        data['postal_code'] = value
        
        except Exception as e:
            logger.warning(f"Parse error for {ip}: {e}")
        
        return data
    
    def close(self):
        """Close session"""
        self.session.close()
