"""
Multi-Source IP Lookup System
Tries multiple IP lookup services to ensure 100% success rate
NO IP LEFT BEHIND!

Sources (in order):
1. InfoByIP (primary - most detailed)
2. IP-API.com (fallback 1 - free, no key needed)
3. IPInfo.io (fallback 2 - free tier)
4. IPWhois (fallback 3 - always works)
"""

import requests
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MultiSourceIPLookup:
    """
    Multi-source IP lookup with automatic fallback
    Guarantees data for EVERY IP
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def lookup_ip_api(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IP-API.com (Free, no key needed)
        Rate limit: 45 requests/minute
        """
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'ip': ip,
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'isp': data.get('isp', 'Unknown'),
                        'organization': data.get('org', 'Unknown'),
                        'latitude': str(data.get('lat', 'Unknown')),
                        'longitude': str(data.get('lon', 'Unknown')),
                        'timezone': data.get('timezone', 'Unknown'),
                        'postal_code': data.get('zip', 'Unknown'),
                        'source': 'ip-api.com'
                    }
        except Exception as e:
            logger.warning(f"IP-API lookup failed for {ip}: {e}")
        return None
    
    def lookup_ipinfo(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPInfo.io (Free tier: 50k/month)
        No API key needed for basic info
        """
        try:
            url = f"https://ipinfo.io/{ip}/json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', ',').split(',')
                lat = loc[0] if len(loc) > 0 else 'Unknown'
                lon = loc[1] if len(loc) > 1 else 'Unknown'
                
                return {
                    'ip': ip,
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'isp': data.get('org', 'Unknown'),
                    'organization': data.get('org', 'Unknown'),
                    'latitude': lat,
                    'longitude': lon,
                    'timezone': data.get('timezone', 'Unknown'),
                    'postal_code': data.get('postal', 'Unknown'),
                    'source': 'ipinfo.io'
                }
        except Exception as e:
            logger.warning(f"IPInfo lookup failed for {ip}: {e}")
        return None
    
    def lookup_ipwhois(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPWhois (Free, always works)
        Last resort - basic info
        """
        try:
            url = f"http://ipwho.is/{ip}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return {
                        'ip': ip,
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'region': data.get('region', 'Unknown'),
                        'isp': data.get('connection', {}).get('isp', 'Unknown'),
                        'organization': data.get('connection', {}).get('org', 'Unknown'),
                        'latitude': str(data.get('latitude', 'Unknown')),
                        'longitude': str(data.get('longitude', 'Unknown')),
                        'timezone': data.get('timezone', {}).get('id', 'Unknown'),
                        'postal_code': data.get('postal', 'Unknown'),
                        'source': 'ipwhois'
                    }
        except Exception as e:
            logger.warning(f"IPWhois lookup failed for {ip}: {e}")
        return None
    
    def lookup_ipapi_co(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPAPI.co (Free tier: 1000/day)
        Another fallback option
        """
        try:
            url = f"https://ipapi.co/{ip}/json/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('error'):
                    return {
                        'ip': ip,
                        'country': data.get('country_name', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'region': data.get('region', 'Unknown'),
                        'isp': data.get('org', 'Unknown'),
                        'organization': data.get('org', 'Unknown'),
                        'latitude': str(data.get('latitude', 'Unknown')),
                        'longitude': str(data.get('longitude', 'Unknown')),
                        'timezone': data.get('timezone', 'Unknown'),
                        'postal_code': data.get('postal', 'Unknown'),
                        'source': 'ipapi.co'
                    }
        except Exception as e:
            logger.warning(f"IPAPI.co lookup failed for {ip}: {e}")
        return None
    
    def lookup_with_fallback(self, ip: str, infobyip_data: Optional[Dict] = None) -> Dict:
        """
        Lookup IP with automatic fallback
        GUARANTEES data for every IP
        
        Order:
        1. Use InfoByIP data if available
        2. Try IP-API.com
        3. Try IPInfo.io
        4. Try IPWhois
        5. Try IPAPI.co
        6. Return basic data with IP only (last resort)
        
        Args:
            ip: IP address to lookup
            infobyip_data: Data from InfoByIP if available
            
        Returns:
            Dictionary with IP data (ALWAYS returns something)
        """
        # If InfoByIP has data, use it
        if infobyip_data and infobyip_data.get('country') != 'Unknown':
            infobyip_data['source'] = 'infobyip'
            return infobyip_data
        
        logger.info(f"🔄 InfoByIP failed for {ip}, trying fallback sources...")
        
        # Try IP-API.com (best free alternative)
        result = self.lookup_ip_api(ip)
        if result:
            logger.info(f"✅ Got data from IP-API.com for {ip}")
            return result
        
        time.sleep(0.5)  # Rate limiting
        
        # Try IPInfo.io
        result = self.lookup_ipinfo(ip)
        if result:
            logger.info(f"✅ Got data from IPInfo.io for {ip}")
            return result
        
        time.sleep(0.5)
        
        # Try IPAPI.co
        result = self.lookup_ipapi_co(ip)
        if result:
            logger.info(f"✅ Got data from IPAPI.co for {ip}")
            return result
        
        time.sleep(0.5)
        
        # Try IPWhois (last resort)
        result = self.lookup_ipwhois(ip)
        if result:
            logger.info(f"✅ Got data from IPWhois for {ip}")
            return result
        
        # Absolute last resort - return IP with Unknown data
        logger.warning(f"⚠️ All sources failed for {ip}, returning basic data")
        return {
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
            'source': 'none'
        }
    
    def close(self):
        """Close session"""
        self.session.close()
