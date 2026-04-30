"""
Quick Test Script for Cloudflare Bypass
Run this to verify the bypass is working
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.cloudflare_bypass import CloudflareBypass


def test_basic_bypass():
    """Test basic Cloudflare bypass"""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: Basic Bypass (Cloudflare Test Site)")
    print("=" * 70)
    
    url = "https://nowsecure.nl"  # Known Cloudflare-protected site
    
    with CloudflareBypass(headless=False, timeout=30) as bypass:
        html = bypass.get_page(url)
        
        if html and len(html) > 1000:
            print("✅ TEST PASSED: Successfully bypassed Cloudflare")
            print(f"📏 Page size: {len(html):,} bytes")
            return True
        else:
            print("❌ TEST FAILED: Could not bypass Cloudflare")
            return False


def test_simple_site():
    """Test on a simple site (no Cloudflare)"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Simple Site (No Cloudflare)")
    print("=" * 70)
    
    url = "https://example.com"
    
    with CloudflareBypass(headless=True, timeout=10) as bypass:
        html = bypass.get_page(url)
        
        if html and "Example Domain" in html:
            print("✅ TEST PASSED: Successfully fetched simple site")
            print(f"📏 Page size: {len(html):,} bytes")
            return True
        else:
            print("❌ TEST FAILED: Could not fetch simple site")
            return False


def test_screenshot():
    """Test screenshot functionality"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Screenshot Functionality")
    print("=" * 70)
    
    url = "https://example.com"
    screenshot_file = "test_screenshot.png"
    
    with CloudflareBypass(headless=False, timeout=10) as bypass:
        html = bypass.get_page(url)
        
        if html:
            bypass.screenshot(screenshot_file)
            
            if os.path.exists(screenshot_file):
                print(f"✅ TEST PASSED: Screenshot saved to {screenshot_file}")
                print(f"📸 File size: {os.path.getsize(screenshot_file):,} bytes")
                return True
            else:
                print("❌ TEST FAILED: Screenshot not created")
                return False
        else:
            print("❌ TEST FAILED: Could not fetch page")
            return False


def test_cookies():
    """Test cookie management"""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: Cookie Management")
    print("=" * 70)
    
    url = "https://example.com"
    
    with CloudflareBypass(headless=True, timeout=10) as bypass:
        html = bypass.get_page(url)
        
        if html:
            cookies = bypass.get_cookies()
            
            if cookies:
                print(f"✅ TEST PASSED: Retrieved {len(cookies)} cookies")
                for name, value in list(cookies.items())[:3]:
                    print(f"   🍪 {name}: {value[:50]}...")
                return True
            else:
                print("⚠️  TEST WARNING: No cookies found (may be normal)")
                return True
        else:
            print("❌ TEST FAILED: Could not fetch page")
            return False


def test_retry_logic():
    """Test retry logic with invalid URL"""
    print("\n" + "=" * 70)
    print("🧪 TEST 5: Retry Logic (Expected to Fail)")
    print("=" * 70)
    
    url = "https://this-site-does-not-exist-12345.com"
    
    with CloudflareBypass(headless=True, timeout=5) as bypass:
        html = bypass.get_page(url, retry_count=2)
        
        if html is None:
            print("✅ TEST PASSED: Retry logic handled failure correctly")
            return True
        else:
            print("❌ TEST FAILED: Should have failed but didn't")
            return False


def main():
    """Run all tests"""
    print("\n" + "🔥" * 35)
    print("   CLOUDFLARE BYPASS TEST SUITE")
    print("🔥" * 35)
    
    tests = [
        ("Basic Cloudflare Bypass", test_basic_bypass),
        ("Simple Site Fetch", test_simple_site),
        ("Screenshot Functionality", test_screenshot),
        ("Cookie Management", test_cookies),
        ("Retry Logic", test_retry_logic),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
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
        print("\n🎉 ALL TESTS PASSED! Cloudflare bypass is working perfectly!")
    elif passed >= total * 0.6:
        print("\n⚠️  MOST TESTS PASSED. Some issues detected but bypass is functional.")
    else:
        print("\n❌ MULTIPLE FAILURES. Please check your setup.")
    
    print("\n" + "🔥" * 35 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
