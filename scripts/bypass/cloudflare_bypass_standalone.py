"""
Standalone Cloudflare Bypass Script
Simple script to bypass Cloudflare protection and scrape websites
"""

import time
import sys

# Try to import undetected_chromedriver
try:
    import undetected_chromedriver as uc
    print("✅ Using undetected_chromedriver (best for Cloudflare)")
except ImportError:
    print("⚠️  undetected_chromedriver not found")
    print("📦 Install it with: pip install undetected-chromedriver")
    uc = None

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def bypass_cloudflare(url: str, headless: bool = False, wait_time: int = 10):
    """
    Bypass Cloudflare and fetch page content
    
    Args:
        url: Target URL to scrape
        headless: Run browser in headless mode (not recommended for Cloudflare)
        wait_time: Time to wait for Cloudflare challenge (seconds)
    
    Returns:
        Page HTML content
    """
    
    print(f"\n🔥 Cloudflare Bypass Script")
    print(f"{'=' * 60}")
    print(f"🎯 Target URL: {url}")
    print(f"👁️  Headless: {headless}")
    print(f"⏱️  Wait time: {wait_time}s")
    print(f"{'=' * 60}\n")
    
    driver = None
    
    try:
        # Method 1: Try undetected_chromedriver (best for Cloudflare)
        if uc:
            print("🚀 Initializing undetected Chrome driver...")
            options = uc.ChromeOptions()
            
            if headless:
                options.add_argument('--headless=new')
            
            # Anti-detection options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = uc.Chrome(options=options, version_main=None)
            print("✅ Undetected Chrome driver initialized")
            
        # Method 2: Fallback to standard Selenium
        else:
            print("🚀 Initializing standard Chrome driver...")
            options = Options()
            
            if headless:
                options.add_argument('--headless=new')
            
            # Anti-detection options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Hide webdriver flag
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            print("✅ Standard Chrome driver initialized")
        
        # Navigate to URL
        print(f"\n🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for Cloudflare challenge
        print(f"⏳ Waiting {wait_time}s for Cloudflare challenge...")
        time.sleep(wait_time)
        
        # Check if Cloudflare is present
        page_source = driver.page_source.lower()
        cf_indicators = ['checking your browser', 'cloudflare', 'ddos protection']
        
        if any(indicator in page_source for indicator in cf_indicators):
            print("⚠️  Cloudflare challenge detected, waiting longer...")
            time.sleep(10)
            page_source = driver.page_source
        else:
            print("✅ No Cloudflare challenge detected")
            page_source = driver.page_source
        
        # Get page title
        title = driver.title
        print(f"\n📄 Page Title: {title}")
        print(f"📏 Page Size: {len(page_source):,} bytes")
        
        # Take screenshot
        screenshot_file = "cloudflare_bypass_screenshot.png"
        driver.save_screenshot(screenshot_file)
        print(f"📸 Screenshot saved: {screenshot_file}")
        
        # Get cookies
        cookies = driver.get_cookies()
        print(f"🍪 Cookies: {len(cookies)} items")
        
        print(f"\n{'=' * 60}")
        print("✅ SUCCESS! Page fetched successfully")
        print(f"{'=' * 60}\n")
        
        return page_source
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"{'=' * 60}\n")
        return None
        
    finally:
        # Close browser
        if driver:
            print("🔒 Closing browser...")
            driver.quit()
            print("✅ Browser closed\n")


def main():
    """Main function"""
    
    # Check if URL is provided
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default test URL
        url = input("Enter URL to bypass (or press Enter for test URL): ").strip()
        if not url:
            url = "https://nowsecure.nl"  # Cloudflare test site
    
    # Ask for headless mode
    headless_input = input("Run in headless mode? (y/n, default: n): ").strip().lower()
    headless = headless_input == 'y'
    
    # Bypass Cloudflare
    html = bypass_cloudflare(url, headless=headless, wait_time=10)
    
    if html:
        # Save HTML to file
        output_file = "cloudflare_bypass_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 HTML saved to: {output_file}")
        
        # Show first 500 characters
        print(f"\n📝 First 500 characters:")
        print("-" * 60)
        print(html[:500])
        print("-" * 60)
    else:
        print("❌ Failed to fetch page")


if __name__ == "__main__":
    main()
