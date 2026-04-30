"""
Debug script to see actual HTML from InfoByIP
This will help us understand the HTML structure
"""

import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Load cookies
cookie_file = Path(__file__).parent / "infobyip_cookies.json"

with open(cookie_file, 'r') as f:
    cookies_data = json.load(f)

# Create session with cookies
session = requests.Session()

for cookie in cookies_data:
    session.cookies.set(
        cookie.get('name'),
        cookie.get('value'),
        domain=cookie.get('domain', '.infobyip.com')
    )

# Test IP
test_ip = "8.8.8.8"
url = f"https://www.infobyip.com/ip-{test_ip}.html"

print(f"Fetching: {url}")
print(f"Using {len(session.cookies)} cookies")

response = session.get(url, timeout=10)

print(f"\nResponse Status: {response.status_code}")
print(f"Response Length: {len(response.text)} characters")

# Save full HTML
html_file = Path(__file__).parent / "debug_infobyip_response.html"
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"\nSaved full HTML to: {html_file}")

# Parse and show structure
soup = BeautifulSoup(response.text, 'html.parser')

# Find all tables
tables = soup.find_all('table')
print(f"\nFound {len(tables)} tables")

# Find all rows
rows = soup.find_all('tr')
print(f"Found {len(rows)} table rows")

# Show first 10 rows
print("\nFirst 10 rows:")
for i, row in enumerate(rows[:10]):
    cells = row.find_all('td')
    if len(cells) >= 2:
        label = cells[0].get_text(strip=True)
        value = cells[1].get_text(strip=True)
        print(f"  Row {i}: {label} = {value}")

# Look for specific keywords
keywords = ['Country', 'City', 'Region', 'ISP', 'Organization', 'United States', 'Google']
print(f"\nSearching for keywords in HTML:")
for keyword in keywords:
    if keyword in response.text:
        print(f"  FOUND: {keyword}")
    else:
        print(f"  MISSING: {keyword}")

# Check for JavaScript
if '<script' in response.text:
    scripts = soup.find_all('script')
    print(f"\nFound {len(scripts)} script tags - data might be loaded via JavaScript")

# Check for Cloudflare
if "Checking your browser" in response.text or "Just a moment" in response.text:
    print("\nCLOUDFLARE CHALLENGE DETECTED!")
else:
    print("\nNo Cloudflare challenge")

print(f"\nOpen {html_file} in browser to see full HTML")
print("\nNext steps:")
print("1. Open debug_infobyip_response.html in browser")
print("2. Inspect the HTML structure")
print("3. Find where Country, City, ISP data is located")
print("4. Update parsing logic in infobyip_cookie_manager.py")
