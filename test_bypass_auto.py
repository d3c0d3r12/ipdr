"""
Automated Test Script for Custom Cloudflare Bypass
No user input required - runs automatically
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from custom_cloudflare_bypass import CustomCloudflareBypass


def test_simple_site():
    """Test 1: Simple site (no Cloudflare)"""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: Simple Site (example.com)")
    print("=" * 70)
    
    try:
        with CustomCloudflareBypass(headless=True, verbose=True) as bypass:
            html = bypass.bypass_and_fetch(
                url="https://example.com",
                max_challenge_wait=10
            )
            
            if html and len(html) > 1000:
                print("\n✅ TEST 1 PASSED")
                print(f"📏 Page size: {len(html):,} bytes")
                print(f"🍪 Cookies: {len(bypass.get_cookies())} items")
                return True
            else:
                print("\n❌ TEST 1 FAILED")
                return False
                
    except Exception as e:
        print(f"\n❌ TEST 1 ERROR: {e}")
        return False


def test_cloudflare_site():
    """Test 2: Cloudflare-protected site"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Cloudflare Protected Site (nowsecure.nl)")
    print("=" * 70)
    
    try:
        with CustomCloudflareBypass(headless=False, verbose=True) as bypass:
            html = bypass.bypass_and_fetch(
                url="https://nowsecure.nl",
                max_challenge_wait=30
            )
            
            if html and len(html) > 1000:
                # Check if we actually bypassed
                if "cloudflare" not in html.lower() or "checking your browser" not in html.lower():
                    print("\n✅ TEST 2 PASSED - Cloudflare bypassed!")
                    print(f"📏 Page size: {len(html):,} bytes")
                    print(f"🍪 Cookies: {len(bypass.get_cookies())} items")
                    
                    # Save results
                    with open("cloudflare_bypass_result.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("💾 HTML saved to: cloudflare_bypass_result.html")
                    
                    bypass.screenshot("cloudflare_bypass_result.png")
                    print("📸 Screenshot saved to: cloudflare_bypass_result.png")
                    
                    return True
                else:
                    print("\n⚠️ TEST 2 PARTIAL - Page fetched but challenge may still be present")
                    return False
            else:
                print("\n❌ TEST 2 FAILED")
                return False
                
    except Exception as e:
        print(f"\n❌ TEST 2 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fingerprint():
    """Test 3: Fingerprint generation"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Fingerprint Generation")
    print("=" * 70)
    
    try:
        bypass = CustomCloudflareBypass(headless=True, verbose=False)
        fingerprint = bypass.fingerprint
        
        print(f"\n📋 Generated Fingerprint:")
        print(f"   User Agent: {fingerprint['user_agent'][:60]}...")
        print(f"   Resolution: {fingerprint['screen_resolution']}")
        print(f"   Timezone: {fingerprint['timezone']}")
        print(f"   Language: {fingerprint['language']}")
        print(f"   Platform: {fingerprint['platform']}")
        print(f"   CPU Cores: {fingerprint['hardware_concurrency']}")
        print(f"   Memory: {fingerprint['device_memory']} GB")
        
        # Verify all fields are present
        required_fields = ['user_agent', 'screen_resolution', 'timezone', 'language', 'platform']
        if all(field in fingerprint for field in required_fields):
            print("\n✅ TEST 3 PASSED - Fingerprint complete")
            return True
        else:
            print("\n❌ TEST 3 FAILED - Missing fields")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 3 ERROR: {e}")
        return False


def main():
    """Run all automated tests"""
    print("\n" + "🔥" * 35)
    print("   AUTOMATED CLOUDFLARE BYPASS TEST")
    print("   Running all tests automatically...")
    print("🔥" * 35)
    
    results = []
    
    # Test 1: Simple site
    print("\n⏳ Starting Test 1...")
    result1 = test_simple_site()
    results.append(("Simple Site", result1))
    
    # Test 2: Fingerprint
    print("\n⏳ Starting Test 2...")
    result2 = test_fingerprint()
    results.append(("Fingerprint", result2))
    
    # Test 3: Cloudflare site (most important)
    print("\n⏳ Starting Test 3 (this may take 30-60 seconds)...")
    result3 = test_cloudflare_site()
    results.append(("Cloudflare Bypass", result3))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("-" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Custom Cloudflare bypass is working perfectly!")
    elif passed >= 2:
        print("\n⚠️ MOST TESTS PASSED")
        print("✅ Bypass is functional but may need tuning")
    else:
        print("\n❌ MULTIPLE FAILURES")
        print("⚠️ Check your setup and try again")
    
    print("\n" + "🔥" * 35 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
