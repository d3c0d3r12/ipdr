"""
IP-API.com Integration for Automated IP Lookups
Free tier: 45 requests per minute, unlimited requests per day
No CAPTCHA, no Cloudflare, no blocking
"""

import time
import csv
import requests
from pathlib import Path
from typing import List, Dict, Optional
import json


def _log(log_path: Path, message: str) -> None:
    """Write log message to file"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8', newline='') as f:
        f.write(message + "\n")


def lookup_single_ip(ip: str, session: Optional[requests.Session] = None) -> Dict:
    """
    Lookup single IP using IP-API.com
    
    Args:
        ip: IP address to lookup
        session: Optional requests session for connection reuse
    
    Returns:
        Dictionary with IP information
    """
    if session is None:
        session = requests.Session()
    
    url = f"http://ip-api.com/json/{ip}"
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country': data.get('country', ''),
                'region': data.get('regionName', ''),
                'city': data.get('city', ''),
                'isp': data.get('isp', ''),
                'status': 'success'
            }
        else:
            return {
                'ip': ip,
                'country': '',
                'region': '',
                'city': '',
                'isp': '',
                'status': 'failed',
                'error': data.get('message', 'Unknown error')
            }
    except Exception as e:
        return {
            'ip': ip,
            'country': '',
            'region': '',
            'city': '',
            'isp': '',
            'status': 'error',
            'error': str(e)
        }


def lookup_batch(ips: List[str], log_path: Path) -> List[Dict]:
    """
    Lookup multiple IPs with rate limiting (45 requests/minute)
    
    Args:
        ips: List of IP addresses
        log_path: Path to log file
    
    Returns:
        List of dictionaries with IP information
    """
    results = []
    session = requests.Session()
    
    # Rate limit: 45 requests per minute = 1 request per 1.33 seconds
    # We'll use 1.5 seconds to be safe
    delay_between_requests = 1.5
    
    total_ips = len(ips)
    _log(log_path, f"[ip-api] Starting lookup for {total_ips} IPs...")
    _log(log_path, f"[ip-api] Rate limit: 1 request per {delay_between_requests}s (45/min)")
    
    for idx, ip in enumerate(ips, 1):
        ip = ip.strip()
        if not ip:
            continue
        
        # Log progress every 10 IPs
        if idx % 10 == 0 or idx == 1:
            _log(log_path, f"[ip-api] Progress: {idx}/{total_ips} ({(idx/total_ips*100):.1f}%)")
        
        # Lookup IP
        result = lookup_single_ip(ip, session)
        results.append(result)
        
        # Rate limiting delay (except for last IP)
        if idx < total_ips:
            time.sleep(delay_between_requests)
    
    # Count successes
    success_count = sum(1 for r in results if r['status'] == 'success')
    _log(log_path, f"[ip-api] ✅ Completed: {success_count}/{total_ips} successful lookups")
    
    return results


def process_batch_file(batch_file: Path, output_csv: Path, log_path: Path) -> bool:
    """
    Process a batch file and create CSV output
    
    Args:
        batch_file: Path to batch file containing IPs
        output_csv: Path to save CSV output
        log_path: Path to log file
    
    Returns:
        True if successful
    """
    try:
        _log(log_path, f"[ip-api] Processing {batch_file.name}...")
        
        # Read IPs from batch file
        ips = batch_file.read_text(encoding='utf-8').strip().split('\n')
        ips = [ip.strip() for ip in ips if ip.strip()]
        
        if not ips:
            _log(log_path, f"[ip-api] ❌ No IPs found in {batch_file.name}")
            return False
        
        # Lookup all IPs
        results = lookup_batch(ips, log_path)
        
        # Write to CSV
        with output_csv.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['ip', 'country', 'region', 'city', 'isp'])
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'ip': result['ip'],
                    'country': result.get('country', ''),
                    'region': result.get('region', ''),
                    'city': result.get('city', ''),
                    'isp': result.get('isp', '')
                })
        
        _log(log_path, f"[ip-api] ✅ Saved {output_csv.name}")
        return True
        
    except Exception as e:
        _log(log_path, f"[ip-api] ❌ Error processing {batch_file.name}: {e}")
        return False


def auto_lookup_batches(run_dir: Path) -> int:
    """
    Automatically lookup all batch files using IP-API.com
    
    Args:
        run_dir: Directory containing batch files
    
    Returns:
        Number of successfully processed batches
    """
    log_path = run_dir / 'process_log.txt'
    batches = sorted(run_dir.glob('batch_*.txt'))
    
    _log(log_path, "")
    _log(log_path, "[ip-api] ═══════════════════════════════════════════")
    _log(log_path, f"[ip-api] IP-API.com Automated Lookup")
    _log(log_path, f"[ip-api] Total batches: {len(batches)}")
    _log(log_path, "[ip-api] ═══════════════════════════════════════════")
    
    count = 0
    
    for idx, batch in enumerate(batches, 1):
        num = batch.stem.split('_')[-1]
        output_csv = run_dir / f"infobyip_batch_{num}.csv"
        
        # Skip if already processed
        if output_csv.exists():
            _log(log_path, f"[ip-api] [{idx}/{len(batches)}] Skipping {batch.name} (already processed)")
            count += 1
            continue
        
        _log(log_path, f"[ip-api] [{idx}/{len(batches)}] Processing {batch.name}...")
        
        # Process batch
        if process_batch_file(batch, output_csv, log_path):
            count += 1
            _log(log_path, f"[ip-api] [{idx}/{len(batches)}] ✅ Success ({count}/{len(batches)} completed)")
        else:
            _log(log_path, f"[ip-api] [{idx}/{len(batches)}] ❌ Failed")
        
        # Add delay between batches (5 seconds for safety)
        if idx < len(batches):
            _log(log_path, f"[ip-api] Waiting 5s before next batch...")
            time.sleep(5)
    
    _log(log_path, "[ip-api] ═══════════════════════════════════════════")
    _log(log_path, f"[ip-api] Completed: {count}/{len(batches)} batches")
    _log(log_path, f"[ip-api] Success rate: {(count/len(batches)*100):.1f}%")
    _log(log_path, "[ip-api] ═══════════════════════════════════════════")
    
    return count


if __name__ == "__main__":
    # Test with a single IP
    result = lookup_single_ip("8.8.8.8")
    print(json.dumps(result, indent=2))
