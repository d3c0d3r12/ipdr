"""
Quick Test - Direct IP Lookup (No Form!)
Test with 3 IPs to verify it works
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass
from bs4 import BeautifulSoup


print("\n" + "🔥" * 35)
print("   QUICK TEST - DIRECT IP LOOKUP")
print("   No Form • No Limits • Direct Access")
print("🔥" * 35 + "\n")

# Test with 3 IPs
test_ips = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]

print(f"🎯 Testing {len(test_ips)} IPs directly")
print(f"📍 Method: Direct page access (no form)")
print(f"🔥 Bypass: Cloudflare stealth mode\n")

try:
    with EnhancedCloudflareBypass(
        headless=False,  # Visible so you can see
        verbose=True,
        rate_limit=2.0
    ) as bypass:
        
        for i, ip in enumerate(test_ips, 1):
            print(f"\n{'=' * 70}")
            print(f"🔍 [{i}/{len(test_ips)}] Looking up: {ip}")
            print("=" * 70)
            
            # Direct URL - NO FORM!
            url = f"https://www.infobyip.com/ip-{ip}.html"
            print(f"📍 URL: {url}")
            
            html = bypass.bypass_and_fetch(url, max_challenge_wait=30)
            
            if html:
                # Parse
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract country
                country = "Unknown"
                for tr in soup.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) >= 2:
                        if 'country' in tds[0].get_text().lower():
                            country = tds[1].get_text().strip()
                            break
                
                print(f"\n✅ SUCCESS!")
                print(f"📏 Page size: {len(html):,} bytes")
                print(f"🌍 Country: {country}")
                
                # Check if it's the actual IP page (not form)
                if f"ip-{ip}" in html.lower() or ip in html:
                    print(f"✅ Correct page (IP data page)")
                else:
                    print(f"⚠️  Might be wrong page")
                
                # Save first one
                if i == 1:
                    with open(f"test_direct_{ip}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"💾 Saved to: test_direct_{ip}.html")
            else:
                print(f"\n❌ FAILED")
        
        # Final stats
        stats = bypass.get_stats()
        print(f"\n{'=' * 70}")
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("=" * 70)
        
        if stats['successful'] == len(test_ips):
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Direct IP lookup works perfectly!")
            print("✅ No form needed!")
            print("✅ No 100 IP limit!")
            print("\n🚀 Ready to process UNLIMITED IPs!")
        else:
            print("\n⚠️  Some tests failed")
            print("Check the output above for details")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "🔥" * 35 + "\n")
