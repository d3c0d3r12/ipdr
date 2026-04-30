"""
Multi-Source IP Lookup System
Tries multiple IP lookup services to ensure 100% success rate
NO IP LEFT BEHIND!

Sources (in order):
1. InfoByIP (primary - most detailed)
2. GeoLite2 local databases (offline, always works)
3. IP-API.com (fallback 1 - free, no key needed)
4. IPInfo.io (fallback 2 - free tier)
5. IPWhois (fallback 3 - always works)
"""

import logging
import os
import time
from typing import Dict, Optional, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── Tor Exit Node Checker ─────────────────────────────────────────────────────
_TOR_LIST_URL = "https://check.torproject.org/torbulkexitlist"
_tor_exit_nodes: Set[str] = set()
_tor_fetched_at: float = 0.0
_TOR_TTL = 6 * 3600  # refresh every 6 hours

def _load_tor_exit_nodes() -> Set[str]:
    global _tor_exit_nodes, _tor_fetched_at
    if time.time() - _tor_fetched_at < _TOR_TTL and _tor_exit_nodes:
        return _tor_exit_nodes
    try:
        resp = requests.get(_TOR_LIST_URL, timeout=8)
        if resp.status_code == 200:
            nodes = {line.strip() for line in resp.text.splitlines() if line.strip() and not line.startswith('#')}
            _tor_exit_nodes = nodes
            _tor_fetched_at = time.time()
            logger.info("Loaded %d Tor exit nodes", len(nodes))
    except Exception as e:
        logger.debug("Could not fetch Tor exit node list: %s", e)
    return _tor_exit_nodes

def _is_tor(ip: str) -> bool:
    return ip in _load_tor_exit_nodes()


# ── Datacenter / VPN ASN keyword detection ───────────────────────────────────
_DATACENTER_KEYWORDS = {
    'amazon', 'aws', 'google', 'microsoft', 'azure', 'digitalocean',
    'linode', 'akamai', 'cloudflare', 'vultr', 'hetzner', 'ovh',
    'leaseweb', 'choopa', 'quadranet', 'tzulo', 'm247', 'datacamp',
    'mullvad', 'expressvpn', 'nordvpn', 'surfshark', 'purevpn',
    'private internet access', 'ipvanish', 'hidemyass', 'protonvpn',
    'hosting', 'datacenter', 'data center', 'colocation', 'vps',
    'serverius', 'fastly', 'incapsula', 'zscaler', 'piaproxy',
}

def _classify_type(asn_org: str, is_proxy: bool, is_hosting: bool, is_mobile: bool) -> str:
    """Return a human-readable connection type label."""
    org_lower = asn_org.lower()
    if any(kw in org_lower for kw in _DATACENTER_KEYWORDS):
        return 'VPN / Datacenter'
    if is_proxy:
        return 'VPN / Proxy'
    if is_hosting:
        return 'Datacenter / Hosting'
    if is_mobile:
        return 'Mobile'
    return 'Residential / ISP'

# GeoIP database paths from env or default to backend/geoip/
_GEOIP_CITY_DB = os.getenv(
    "GEOIP_CITY_DB",
    os.path.join(os.path.dirname(__file__), "..", "geoip", "GeoLite2-City.mmdb"),
)
_GEOIP_ASN_DB = os.getenv(
    "GEOIP_ASN_DB",
    os.path.join(os.path.dirname(__file__), "..", "geoip", "GeoLite2-ASN.mmdb"),
)

try:
    import geoip2.database
    import geoip2.errors
    _city_reader = geoip2.database.Reader(_GEOIP_CITY_DB)
    _asn_reader = geoip2.database.Reader(_GEOIP_ASN_DB)
    _GEOIP_AVAILABLE = True
    logger.info("GeoLite2 databases loaded successfully")
except Exception as _e:
    _city_reader = None
    _asn_reader = None
    _GEOIP_AVAILABLE = False
    logger.warning("GeoLite2 databases not available: %s", _e)


class MultiSourceIPLookup:
    """
    Multi-source IP lookup with automatic fallback
    Guarantees data for EVERY IP
    """
    
    def __init__(self):
        self.timeout_seconds = self._parse_float_env("IP_LOOKUP_TIMEOUT_SEC", 3.5, minimum=0.5)
        retries_raw = os.getenv("IP_LOOKUP_RETRIES", "1").strip() or "1"
        try:
            retries = max(0, min(int(retries_raw), 3))
        except Exception:
            retries = 1

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        retry_strategy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({'GET'}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    @staticmethod
    def _parse_float_env(name: str, default: float, minimum: float = 0.1) -> float:
        raw = os.getenv(name, '').strip()
        if not raw:
            return default
        try:
            value = float(raw)
            return value if value >= minimum else minimum
        except Exception:
            return default

    def _fetch_json(self, url: str) -> Optional[Dict]:
        try:
            response = self.session.get(url, timeout=(1.5, self.timeout_seconds))
        except Exception:
            return None

        if response.status_code != 200:
            return None

        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
    
    def lookup_geoip(self, ip: str) -> Optional[Dict]:
        """Lookup using local GeoLite2 databases — offline, no rate limits."""
        if not _GEOIP_AVAILABLE:
            return None
        try:
            city = _city_reader.city(ip)
            asn = _asn_reader.asn(ip)
            asn_org = asn.autonomous_system_organization or 'Unknown'
            conn_type = _classify_type(asn_org, is_proxy=False, is_hosting=False, is_mobile=False)
            return {
                'ip': ip,
                'country': city.country.name or 'Unknown',
                'city': city.city.name or 'Unknown',
                'region': city.subdivisions.most_specific.name or 'Unknown',
                'isp': asn_org,
                'organization': asn_org,
                'latitude': str(city.location.latitude) if city.location.latitude is not None else 'Unknown',
                'longitude': str(city.location.longitude) if city.location.longitude is not None else 'Unknown',
                'timezone': city.location.time_zone or 'Unknown',
                'postal_code': city.postal.code or 'Unknown',
                'connection_type': conn_type,
                'is_tor': False,
                'is_vpn': 'VPN' in conn_type,
                'source': 'geoip2-local',
            }
        except geoip2.errors.AddressNotFoundError:
            logger.debug('GeoIP: address not found for %s', ip)
        except Exception as e:
            logger.debug('GeoIP lookup failed for %s: %s', ip, e)
        return None

    def lookup_ip_api(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IP-API.com (Free, no key needed)
        Rate limit: 45 requests/minute
        proxy/hosting/mobile fields are available on the free tier
        """
        try:
            url = (
                f"http://ip-api.com/json/{ip}"
                f"?fields=status,message,country,countryCode,region,regionName,"
                f"city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting,mobile"
            )
            data = self._fetch_json(url)
            if data and data.get('status') == 'success':
                is_proxy   = bool(data.get('proxy', False))
                is_hosting = bool(data.get('hosting', False))
                is_mobile  = bool(data.get('mobile', False))
                org        = data.get('org', data.get('isp', 'Unknown'))
                conn_type  = _classify_type(org, is_proxy, is_hosting, is_mobile)
                return {
                    'ip': ip,
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'organization': org,
                    'latitude': str(data.get('lat', 'Unknown')),
                    'longitude': str(data.get('lon', 'Unknown')),
                    'timezone': data.get('timezone', 'Unknown'),
                    'postal_code': data.get('zip', 'Unknown'),
                    'connection_type': conn_type,
                    'is_tor': False,
                    'is_vpn': is_proxy or is_hosting or 'VPN' in conn_type,
                    'source': 'ip-api.com',
                }
        except Exception:
            logger.debug('IP-API lookup failed for %s', ip)
        return None
    
    def lookup_ipinfo(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPInfo.io (Free tier: 50k/month)
        No API key needed for basic info
        """
        try:
            url = f"https://ipinfo.io/{ip}/json"
            data = self._fetch_json(url)
            if data:
                loc = str(data.get('loc', ',')).split(',')
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
        except Exception:
            logger.debug('IPInfo lookup failed for %s', ip)
        return None
    
    def lookup_ipwhois(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPWhois (Free, always works)
        Last resort - basic info
        """
        try:
            url = f"https://ipwho.is/{ip}"
            data = self._fetch_json(url)
            if data and data.get('success', False):
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
        except Exception:
            logger.debug('IPWhois lookup failed for %s', ip)
        return None
    
    def lookup_ipapi_co(self, ip: str) -> Optional[Dict]:
        """
        Lookup using IPAPI.co (Free tier: 1000/day)
        Another fallback option
        """
        try:
            url = f"https://ipapi.co/{ip}/json/"
            data = self._fetch_json(url)
            if data and not data.get('error'):
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
        except Exception:
            logger.debug('IPAPI.co lookup failed for %s', ip)
        return None
    
    def lookup_ip_api_batch(self, ips: list) -> dict:
        """Batch lookup via ip-api.com — up to 100 IPs per HTTP call (free tier)."""
        if not ips:
            return {}
        try:
            fields = (
                "status,message,country,countryCode,region,regionName,"
                "city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting,mobile"
            )
            url = f"http://ip-api.com/batch?fields={fields}"
            payload = [{"query": ip} for ip in ips[:100]]
            resp = self.session.post(url, json=payload, timeout=(2, self.timeout_seconds))
            if resp.status_code != 200:
                return {}
            data = resp.json()
            if not isinstance(data, list):
                return {}
            results: dict = {}
            for item in data:
                if not isinstance(item, dict) or item.get('status') != 'success':
                    continue
                ip_addr = str(item.get('query', '')).strip()
                if not ip_addr:
                    continue
                is_proxy   = bool(item.get('proxy'))
                is_hosting = bool(item.get('hosting'))
                is_mobile  = bool(item.get('mobile'))
                org        = item.get('org') or item.get('isp') or 'Unknown'
                conn_type  = _classify_type(org, is_proxy, is_hosting, is_mobile)
                result = {
                    'ip':              ip_addr,
                    'country':         item.get('country', 'Unknown'),
                    'city':            item.get('city', 'Unknown'),
                    'region':          item.get('regionName', 'Unknown'),
                    'isp':             item.get('isp', 'Unknown'),
                    'organization':    org,
                    'latitude':        str(item.get('lat', 'Unknown')),
                    'longitude':       str(item.get('lon', 'Unknown')),
                    'timezone':        item.get('timezone', 'Unknown'),
                    'postal_code':     item.get('zip', 'Unknown'),
                    'connection_type': conn_type,
                    'is_tor':          False,
                    'is_vpn':          is_proxy or is_hosting or 'VPN' in conn_type,
                    'source':          'ip-api.com',
                }
                results[ip_addr] = self._stamp_threat(ip_addr, result)
            return results
        except Exception as e:
            logger.debug('ip-api.com batch failed: %s', e)
            return {}

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
        if infobyip_data:
            has_meaningful_fields = any(
                str(infobyip_data.get(k, '')).strip() not in ('', 'Unknown')
                for k in ('country', 'city', 'region', 'isp', 'organization')
            )
            if has_meaningful_fields:
                infobyip_data['source'] = 'infobyip'
                result = infobyip_data
                return self._stamp_threat(ip, result)

        for source in (
            self.lookup_geoip,
            self.lookup_ipinfo,
            self.lookup_ipapi_co,
            self.lookup_ipwhois,
            self.lookup_ip_api,
        ):
            result = source(ip)
            if result:
                return self._stamp_threat(ip, result)

        # Absolute last resort - return IP with Unknown data
        logger.warning(f"⚠️ All sources failed for {ip}, returning basic data")
        base = {
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
            'source': 'none',
        }
        return self._stamp_threat(ip, base)

    def _stamp_threat(self, ip: str, data: Dict) -> Dict:
        """Add Tor / VPN / connection_type fields to any result dict."""
        tor = _is_tor(ip)
        if tor:
            data['is_tor'] = True
            data['is_vpn'] = False
            data['connection_type'] = 'Tor Exit Node'
        else:
            data.setdefault('is_tor', False)
            data.setdefault('is_vpn', False)
            data.setdefault('connection_type',
                _classify_type(
                    data.get('organization') or data.get('isp') or '',
                    is_proxy=False, is_hosting=False, is_mobile=False,
                ))
        return data
    
    def close(self):
        """Close session"""
        self.session.close()
