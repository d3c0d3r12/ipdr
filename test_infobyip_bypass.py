"""
Test Enhanced Cloudflare Bypass on InfoByIP
Target: https://www.infobyip.com/ipbulklookup.php
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass, BypassStrategy
from bs4 import BeautifulSoup
import time


def test_infobyip_main_page():
    """Test 1: Access main InfoByIP page"""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: InfoByIP Main Page")
    print("=" * 70)
    
    url = "https://www.infobyip.com/"
    
    try:
        with EnhancedCloudflareBypass(
            headless=False,
            verbose=True,
            max_retries=3,
            rate_limit=2.0
        ) as bypass:
            html = bypass.bypass_and_fetch(url, max_challenge_wait=30)
            
            if html:
                print(f"\n✅ TEST 1 PASSED")
                print(f"📏 Page size: {len(html):,} bytes")
                
                # Check for Cloudflare
                if "cloudflare" in html.lower() and "checking your browser" in html.lower():
                    print("⚠️  Still showing Cloudflare challenge")
                    return False
                else:
                    print("✅ No Cloudflare challenge detected")
                    return True
            else:
                print("❌ TEST 1 FAILED")
                return False
                
    except Exception as e:
        print(f"❌ TEST 1 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infobyip_bulk_lookup():
    """Test 2: Access bulk lookup page"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: InfoByIP Bulk Lookup Page")
    print("=" * 70)
    
    url = "https://www.infobyip.com/ipbulklookup.php"
    
    try:
        with EnhancedCloudflareBypass(
            headless=False,
            verbose=True,
            max_retries=3,
            rate_limit=2.0,
            cookie_file="infobyip_test_cookies.json"
        ) as bypass:
            html = bypass.bypass_and_fetch(url, max_challenge_wait=30)
            
            if html:
                print(f"\n✅ TEST 2 PASSED")
                print(f"📏 Page size: {len(html):,} bytes")
                
                # Parse and check content
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check for form
                form = soup.find('form')
                if form:
                    print("✅ Form found on page")
                else:
                    print("⚠️  No form found")
                
                # Check for Cloudflare
                if "cloudflare" in html.lower() and "checking your browser" in html.lower():
                    print("⚠️  Still showing Cloudflare challenge")
                    return False
                else:
                    print("✅ No Cloudflare challenge detected")
                
                # Save HTML for inspection
                with open("infobyip_bulk_lookup.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("💾 HTML saved to: infobyip_bulk_lookup.html")
                
                # Take screenshot
                bypass.screenshot("infobyip_bulk_lookup.png")
                print("📸 Screenshot saved to: infobyip_bulk_lookup.png")
                
                # Show stats
                stats = bypass.get_stats()
                print(f"\n📊 Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                
                return True
            else:
                print("❌ TEST 2 FAILED")
                return False
                
    except Exception as e:
        print(f"❌ TEST 2 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infobyip_single_ip():
    """Test 3: Lookup single IP"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: InfoByIP Single IP Lookup")
    print("=" * 70)
    
    test_ips = [
        "8.8.8.8",      # Google DNS
        "1.1.1.1",      # Cloudflare DNS
        "9.9.9.9",      # Quad9 DNS
    ]
    
    try:
        with EnhancedCloudflareBypass(
            headless=False,
            verbose=True,
            max_retries=3,
            rate_limit=3.0,  # Slower for testing
            cookie_file="infobyip_test_cookies.json"
        ) as bypass:
            
            results = []
            
            for i, ip in enumerate(test_ips, 1):
                print(f"\n🔍 [{i}/{len(test_ips)}] Looking up: {ip}")
                
                url = f"https://www.infobyip.com/ip-{ip}.html"
                html = bypass.bypass_and_fetch(url, max_challenge_wait=30)
                
                if html:
                    # Parse data
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try to extract country
                    country = "Unknown"
                    try:
                        # Look for country in various places
                        for td in soup.find_all('td'):
                            if 'Country' in td.get_text():
                                country_td = td.find_next_sibling('td')
                                if country_td:
                                    country = country_td.get_text().strip()
                                    break
                    except:
                        pass
                    
                    print(f"✅ Success: {ip} → {country}")
                    results.append({
                        'ip': ip,
                        'country': country,
                        'success': True
                    })
                    
                    # Save first result for inspection
                    if i == 1:
                        with open(f"infobyip_{ip}.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print(f"💾 HTML saved to: infobyip_{ip}.html")
                else:
                    print(f"❌ Failed: {ip}")
                    results.append({
                        'ip': ip,
                        'success': False
                    })
            
            # Summary
            print(f"\n{'=' * 70}")
            print("📊 TEST 3 SUMMARY")
            print("=" * 70)
            
            success_count = sum(1 for r in results if r['success'])
            print(f"\nResults: {success_count}/{len(test_ips)} successful")
            
            for result in results:
                status = "✅" if result['success'] else "❌"
                country = result.get('country', 'N/A')
                print(f"{status} {result['ip']}: {country}")
            
            # Show final stats
            stats = bypass.get_stats()
            print(f"\n📊 Bypass Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            return success_count == len(test_ips)
            
    except Exception as e:
        print(f"❌ TEST 3 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infobyip_batch():
    """Test 4: Batch lookup using bypass"""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: InfoByIP Batch Lookup")
    print("=" * 70)
    
    test_ips = [
        "8.8.8.8",
        "1.1.1.1",
        "9.9.9.9",
        "208.67.222.222",
        "208.67.220.220"
    ]
    
    try:
        with EnhancedCloudflareBypass(
            headless=True,  # Headless for batch
            verbose=True,
            max_retries=3,
            rate_limit=2.0,
            cookie_file="infobyip_test_cookies.json"
        ) as bypass:
            
            # Build URLs
            urls = [f"https://www.infobyip.com/ip-{ip}.html" for ip in test_ips]
            
            # Progress callback
            def progress_callback(current, total, url, success):
                ip = url.split('ip-')[1].split('.html')[0]
                status = "✅" if success else "❌"
                print(f"{status} [{current}/{total}] {ip}")
            
            # Batch fetch
            print(f"\n🚀 Fetching {len(urls)} IPs in batch mode...")
            results = bypass.batch_fetch(urls, progress_callback)
            
            # Process results
            print(f"\n{'=' * 70}")
            print("📊 BATCH RESULTS")
            print("=" * 70)
            
            success_count = sum(1 for r in results if r is not None)
            
            for ip, html in zip(test_ips, results):
                if html:
                    # Quick parse
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else "Unknown"
                    print(f"✅ {ip}: {len(html):,} bytes - {title[:50]}...")
                else:
                    print(f"❌ {ip}: Failed")
            
            # Final stats
            stats = bypass.get_stats()
            print(f"\n📊 Final Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            return success_count >= len(test_ips) * 0.8  # 80% success rate
            
    except Exception as e:
        print(f"❌ TEST 4 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🔥" * 35)
    print("   INFOBYIP CLOUDFLARE BYPASS TEST")
    print("   Target: https://www.infobyip.com/")
    print("🔥" * 35)
    
    tests = [
        ("InfoByIP Main Page", test_infobyip_main_page),
        ("InfoByIP Bulk Lookup Page", test_infobyip_bulk_lookup),
        ("InfoByIP Single IP Lookup", test_infobyip_single_ip),
        ("InfoByIP Batch Lookup", test_infobyip_batch),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n⏳ Starting: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            results.append((test_name, False))
        
        # Wait between tests
        print("\n⏸️  Waiting 3 seconds before next test...")
        time.sleep(3)
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("-" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enhanced bypass works perfectly on InfoByIP!")
    elif passed >= total * 0.75:
        print("\n⚠️  MOST TESTS PASSED")
        print("✅ Bypass is functional but may need tuning")
    else:
        print("\n❌ MULTIPLE FAILURES")
        print("⚠️  Check configuration and try again")
    
    print("\n📁 Output Files:")
    print("   - infobyip_bulk_lookup.html")
    print("   - infobyip_bulk_lookup.png")
    print("   - infobyip_8.8.8.8.html")
    print("   - infobyip_test_cookies.json")
    
    print("\n" + "🔥" * 35 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
