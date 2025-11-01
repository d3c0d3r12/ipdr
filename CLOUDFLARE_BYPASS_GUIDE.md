# 🔥 Cloudflare Bypass Guide

Complete guide to bypass Cloudflare protection for web scraping.

---

## 📦 Files Created

### 1. **`backend/utils/cloudflare_bypass.py`**
- Advanced bypass class with full features
- Context manager support
- Retry logic and exponential backoff
- Cookie management
- Screenshot capability

### 2. **`cloudflare_bypass_standalone.py`**
- Simple standalone script
- Easy to test and use
- Interactive mode
- No complex dependencies

---

## 🚀 Quick Start

### **Method 1: Standalone Script (Easiest)**

```bash
# Navigate to project directory
cd "C:\Users\saheb\Downloads\New FIR"

# Run the script
python cloudflare_bypass_standalone.py
```

**Interactive prompts:**
```
Enter URL to bypass: https://example.com
Run in headless mode? (y/n): n
```

**Or with command line:**
```bash
python cloudflare_bypass_standalone.py https://example.com
```

### **Method 2: Using the Utility Class**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass

# Simple usage
with CloudflareBypass(headless=False) as bypass:
    html = bypass.get_page("https://example.com")
    print(html)
```

---

## 📋 Installation

### **Required Dependencies:**

```bash
# Basic requirements (already in requirements.txt)
pip install selenium==4.25.0
pip install webdriver-manager==4.0.2

# Advanced bypass (HIGHLY RECOMMENDED)
pip install undetected-chromedriver==3.5.5
```

### **Update requirements.txt:**

Already added to `backend/requirements.txt`:
```
selenium==4.25.0
webdriver-manager==4.0.2
undetected-chromedriver==3.5.5
```

---

## 🎯 Features

### **1. Anti-Detection Techniques**

✅ **Undetected ChromeDriver**
- Bypasses Selenium detection
- Patches Chrome DevTools Protocol
- Removes automation flags

✅ **User Agent Rotation**
- Random user agents
- Mimics real browsers
- Multiple OS/browser combinations

✅ **WebDriver Hiding**
- Removes `navigator.webdriver` flag
- Disables automation extensions
- Hides CDP commands

✅ **Stealth Options**
- No sandbox mode
- Disable automation features
- Remove automation flags

### **2. Cloudflare Challenge Handling**

✅ **Automatic Detection**
- Detects Cloudflare challenges
- Waits for completion
- Verifies bypass success

✅ **Smart Waiting**
- Configurable timeout
- Exponential backoff
- Retry logic

✅ **Cookie Management**
- Save/load cookies
- Session persistence
- Cross-request support

### **3. Error Handling**

✅ **Retry Mechanism**
- Configurable retry count
- Exponential backoff
- Graceful degradation

✅ **Timeout Handling**
- Page load timeout
- Element wait timeout
- Challenge timeout

✅ **Screenshot Debugging**
- Capture page state
- Debug visual issues
- Verify bypass success

---

## 💻 Usage Examples

### **Example 1: Basic Bypass**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass

# Create bypass instance
bypass = CloudflareBypass(headless=True)

# Fetch page
html = bypass.get_page("https://example.com")

# Close browser
bypass.close()

print(f"Fetched {len(html)} bytes")
```

### **Example 2: Context Manager (Recommended)**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass

with CloudflareBypass(headless=False, timeout=30) as bypass:
    # Fetch page
    html = bypass.get_page("https://example.com")
    
    # Take screenshot
    bypass.screenshot("debug.png")
    
    # Get cookies
    cookies = bypass.get_cookies()
    print(f"Cookies: {cookies}")
```

### **Example 3: With Proxy**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass

# Using proxy
with CloudflareBypass(
    headless=True,
    proxy="proxy.example.com:8080"
) as bypass:
    html = bypass.get_page("https://example.com")
```

### **Example 4: Wait for Specific Element**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass

with CloudflareBypass() as bypass:
    # Wait for specific element before returning
    html = bypass.get_page(
        url="https://example.com",
        wait_for_element="div.content",
        retry_count=5
    )
```

### **Example 5: Cookie Persistence**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass
import json

# First request - save cookies
with CloudflareBypass() as bypass:
    html = bypass.get_page("https://example.com")
    cookies = bypass.get_cookies()
    
    # Save cookies
    with open("cookies.json", "w") as f:
        json.dump(cookies, f)

# Second request - load cookies
with CloudflareBypass() as bypass:
    # Load cookies
    with open("cookies.json", "r") as f:
        cookies = json.load(f)
    
    bypass.set_cookies(cookies)
    html = bypass.get_page("https://example.com")
```

---

## 🧪 Testing

### **Test Script:**

```python
"""
Test Cloudflare bypass on various sites
"""
from backend.utils.cloudflare_bypass import CloudflareBypass

# Test URLs
test_urls = [
    "https://nowsecure.nl",  # Cloudflare test site
    "https://example.com",   # Simple site
    # Add your target URLs here
]

print("🧪 Testing Cloudflare Bypass")
print("=" * 60)

for url in test_urls:
    print(f"\n🎯 Testing: {url}")
    
    with CloudflareBypass(headless=False) as bypass:
        html = bypass.get_page(url, retry_count=3)
        
        if html:
            print(f"✅ Success! ({len(html):,} bytes)")
        else:
            print(f"❌ Failed!")
    
    print("-" * 60)

print("\n✅ Testing complete!")
```

---

## 🔧 Configuration Options

### **CloudflareBypass Parameters:**

```python
CloudflareBypass(
    headless=True,          # Run browser in headless mode
    proxy=None,             # Proxy server (optional)
    timeout=30,             # Maximum wait time (seconds)
    use_undetected=True     # Use undetected_chromedriver
)
```

### **get_page Parameters:**

```python
bypass.get_page(
    url="https://example.com",     # Target URL
    wait_for_element=None,          # CSS selector to wait for
    retry_count=3                   # Number of retry attempts
)
```

---

## 🐛 Troubleshooting

### **Issue 1: ChromeDriver Not Found**

**Error:** `WebDriver not found`

**Solution:**
```bash
# webdriver-manager will auto-download
pip install webdriver-manager
```

### **Issue 2: Cloudflare Still Blocking**

**Solutions:**
1. **Use undetected_chromedriver:**
   ```bash
   pip install undetected-chromedriver
   ```

2. **Disable headless mode:**
   ```python
   bypass = CloudflareBypass(headless=False)
   ```

3. **Increase wait time:**
   ```python
   bypass = CloudflareBypass(timeout=60)
   ```

4. **Use proxy:**
   ```python
   bypass = CloudflareBypass(proxy="proxy:port")
   ```

### **Issue 3: Timeout Errors**

**Solution:**
```python
# Increase timeout and retry count
with CloudflareBypass(timeout=60) as bypass:
    html = bypass.get_page(url, retry_count=5)
```

### **Issue 4: Memory Issues**

**Solution:**
```python
# Close browser after each request
bypass = CloudflareBypass()
html = bypass.get_page(url)
bypass.close()  # Important!
```

---

## 📊 Performance Tips

### **1. Reuse Browser Instance**

```python
# Good - reuse instance
bypass = CloudflareBypass()
for url in urls:
    html = bypass.get_page(url)
bypass.close()

# Bad - create new instance each time
for url in urls:
    with CloudflareBypass() as bypass:
        html = bypass.get_page(url)
```

### **2. Use Headless Mode**

```python
# Faster but may be detected
bypass = CloudflareBypass(headless=True)
```

### **3. Optimize Timeouts**

```python
# Adjust based on site speed
bypass = CloudflareBypass(timeout=15)  # Faster sites
bypass = CloudflareBypass(timeout=60)  # Slower sites
```

### **4. Cookie Persistence**

```python
# Save cookies to avoid repeated challenges
cookies = bypass.get_cookies()
# Reuse cookies in next session
```

---

## 🔒 Legal & Ethical Considerations

⚠️ **Important:**

1. **Respect robots.txt**
2. **Follow rate limits**
3. **Don't overload servers**
4. **Check Terms of Service**
5. **Use for legitimate purposes only**

---

## 📝 Integration with IPDR System

### **Example: Scrape IP Data**

```python
from backend.utils.cloudflare_bypass import CloudflareBypass
from bs4 import BeautifulSoup

def scrape_ip_data(ip_address: str):
    """Scrape IP data from protected site"""
    
    url = f"https://example.com/ip/{ip_address}"
    
    with CloudflareBypass(headless=True) as bypass:
        html = bypass.get_page(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            data = {
                'ip': ip_address,
                'country': soup.select_one('.country').text,
                'isp': soup.select_one('.isp').text,
                # ... more fields
            }
            
            return data
    
    return None
```

---

## 🎯 Next Steps

1. ✅ **Test the standalone script**
   ```bash
   python cloudflare_bypass_standalone.py
   ```

2. ✅ **Integrate with your scraping logic**
   ```python
   from backend.utils.cloudflare_bypass import CloudflareBypass
   ```

3. ✅ **Add to your workflow**
   - Replace requests with CloudflareBypass
   - Handle Cloudflare-protected sites
   - Improve scraping success rate

4. ✅ **Monitor and optimize**
   - Check success rate
   - Adjust timeouts
   - Use proxies if needed

---

## 📞 Support

**Common Issues:**
- Check logs for detailed errors
- Use `bypass.screenshot()` for debugging
- Try non-headless mode first
- Verify Chrome is installed

**Resources:**
- Selenium docs: https://selenium-python.readthedocs.io/
- Undetected ChromeDriver: https://github.com/ultrafunkamsterdam/undetected-chromedriver

---

**Created:** 2025-11-01  
**Status:** Ready to use  
**Dependencies:** Already in requirements.txt
