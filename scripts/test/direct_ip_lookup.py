"""
Direct IP Lookup - No Limits!
Bypass the bulk form and directly access individual IP pages
Each IP has its own page: https://www.infobyip.com/ip-{IP}.html
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass, BypassStrategy
from bs4 import BeautifulSoup
import json
import csv


def parse_ip_data(html: str, ip: str) -> dict:
    """
    Parse InfoByIP HTML and extract all data
    
    Args:
        html: HTML content
        ip: IP address
        
    Returns:
        Dictionary with IP data
    """
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
        'postal_code': 'Unknown'
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
        print(f"⚠️  Parse error for {ip}: {e}")
    
    return data


def lookup_ips_unlimited(
    ip_addresses: list,
    output_csv: str = "ip_lookup_results.csv",
    output_json: str = "ip_lookup_results.json"
):
    """
    Lookup unlimited IPs directly - NO LIMITS!
    
    Args:
        ip_addresses: List of IP addresses
        output_csv: Output CSV file
        output_json: Output JSON file
    """
    
    print("\n" + "🔥" * 35)
    print("   UNLIMITED IP LOOKUP")
    print("   Direct Access - No Form Limits!")
    print("🔥" * 35)
    
    print(f"\n📊 Total IPs to lookup: {len(ip_addresses)}")
    print(f"⏱️  Estimated time: {len(ip_addresses) * 5 / 60:.1f} minutes")
    print(f"🎯 Target: InfoByIP.com (direct pages)")
    print(f"🔥 Method: Cloudflare bypass\n")
    
    results = []
    
    try:
        with EnhancedCloudflareBypass(
            headless=True,  # Headless for speed
            strategy=BypassStrategy.STEALTH,
            max_retries=3,
            rate_limit=2.0,  # 2 seconds between requests
            cookie_file="unlimited_lookup_cookies.json",
            verbose=True
        ) as bypass:
            
            # Build URLs - Direct IP pages (NO LIMITS!)
            urls = [f"https://www.infobyip.com/ip-{ip}.html" for ip in ip_addresses]
            
            print("🚀 Starting unlimited lookup...\n")
            
            # Progress callback
            def progress_callback(current, total, url, success):
                ip = url.split('ip-')[1].split('.html')[0]
                status = "✅" if success else "❌"
                percent = (current / total) * 100
                print(f"{status} [{current}/{total}] ({percent:.1f}%) {ip}")
            
            # Batch fetch - NO LIMITS!
            html_results = bypass.batch_fetch(urls, progress_callback)
            
            # Parse all results
            print(f"\n📝 Parsing {len(html_results)} results...\n")
            
            for ip, html in zip(ip_addresses, html_results):
                if html:
                    data = parse_ip_data(html, ip)
                    results.append(data)
                    print(f"✅ {ip}: {data['country']} - {data['city']} - {data['isp']}")
                else:
                    results.append({
                        'ip': ip,
                        'error': 'Failed to fetch'
                    })
                    print(f"❌ {ip}: Failed")
            
            # Save to CSV
            print(f"\n💾 Saving to CSV: {output_csv}")
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            
            # Save to JSON
            print(f"💾 Saving to JSON: {output_json}")
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            # Statistics
            stats = bypass.get_stats()
            success_count = sum(1 for r in results if 'error' not in r)
            
            print(f"\n{'=' * 70}")
            print("📊 FINAL RESULTS")
            print("=" * 70)
            print(f"Total IPs: {len(ip_addresses)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {len(ip_addresses) - success_count}")
            print(f"Success Rate: {stats['success_rate']}")
            print(f"Cookies Saved: {stats['cookies_saved']}")
            print(f"\n📁 Output Files:")
            print(f"   - {output_csv}")
            print(f"   - {output_json}")
            print("=" * 70)
            
            return results
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return results


def read_ips_from_file(filename: str) -> list:
    """Read IPs from text file (one per line)"""
    try:
        with open(filename, 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
        print(f"📄 Loaded {len(ips)} IPs from {filename}")
        return ips
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []


def main():
    """Main function"""
    
    print("\n" + "🔥" * 35)
    print("   UNLIMITED IP LOOKUP TOOL")
    print("   No Limits • Direct Access • Cloudflare Bypass")
    print("🔥" * 35 + "\n")
    
    # Option 1: Read from file
    print("📋 Options:")
    print("1. Load IPs from file (ips.txt)")
    print("2. Enter IPs manually")
    print("3. Use test IPs")
    
    choice = input("\nChoose option (1/2/3): ").strip()
    
    ip_addresses = []
    
    if choice == "1":
        print("\n💡 Examples:")
        print("   - ips.txt (if in current folder)")
        print("   - work-4gC8Av\\ips.txt")
        print("   - work-qbwqAB\\ips.txt")
        print("   - C:\\path\\to\\your\\ips.txt")
        filename = input("\nEnter file path (default: ips.txt): ").strip() or "ips.txt"
        ip_addresses = read_ips_from_file(filename)
    
    elif choice == "2":
        print("\nEnter IPs (one per line, empty line to finish):")
        while True:
            ip = input().strip()
            if not ip:
                break
            ip_addresses.append(ip)
    
    else:
        # Test IPs
        ip_addresses = [
            "8.8.8.8",
            "1.1.1.1",
            "9.9.9.9",
            "208.67.222.222",
            "208.67.220.220"
        ]
        print(f"Using {len(ip_addresses)} test IPs")
    
    if not ip_addresses:
        print("❌ No IPs provided!")
        return
    
    print(f"\n✅ Ready to lookup {len(ip_addresses)} IPs")
    print(f"⚠️  This will take approximately {len(ip_addresses) * 5 / 60:.1f} minutes")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    
    if confirm == 'y':
        results = lookup_ips_unlimited(ip_addresses)
        
        if results:
            print("\n🎉 Lookup complete!")
            print(f"✅ Successfully processed {len(results)} IPs")
        else:
            print("\n❌ Lookup failed")
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
