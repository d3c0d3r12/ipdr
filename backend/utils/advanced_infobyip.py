"""
Advanced InfoByIP Scraper with Anti-Detection
Uses multiple techniques to bypass Cloudflare protection
"""

import os
import time
import random
from pathlib import Path
from typing import Optional

# Try to import undetected_chromedriver, fallback if not available
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    UNDETECTED_AVAILABLE = True
except ImportError as e:
    UNDETECTED_AVAILABLE = False
    print(f"Warning: undetected_chromedriver not available: {e}")
    print("Advanced anti-detection will not work. Install with: pip install undetected-chromedriver")


def _log(log_path: Path, message: str) -> None:
    """Write log message to file"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8', newline='') as f:
        f.write(message + "\n")


def _random_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """Random human-like delay"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def _create_undetected_driver():
    """
    Create undetected Chrome driver that bypasses Cloudflare
    
    This uses undetected-chromedriver which:
    - Patches Chrome to remove automation flags
    - Uses real Chrome (not headless)
    - Randomizes fingerprints
    - Bypasses most anti-bot systems
    """
    options = uc.ChromeOptions()
    
    # Don't use headless - Cloudflare detects it
    # options.add_argument('--headless')  # NEVER use headless with Cloudflare
    
    # Performance optimizations
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    
    # Randomize window size (human-like)
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    options.add_argument(f'--window-size={width},{height}')
    
    # Create driver with undetected-chromedriver
    driver = uc.Chrome(options=options, version_main=None)
    
    # Additional anti-detection measures
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    return driver


def _human_like_typing(element, text: str):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.01, 0.05))  # 10-50ms per character


def _scroll_smoothly(driver, element):
    """Smooth scroll to element"""
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        element
    )
    _random_delay(0.5, 1.5)


def fetch_with_undetected_chrome(url: str, batch_text: str, log_path: Path) -> Optional[str]:
    """
    Fetch InfoByIP data using undetected-chromedriver
    
    This method:
    1. Uses undetected-chromedriver (bypasses most detection)
    2. Waits for Cloudflare challenge to complete
    3. Acts like a human (scrolling, delays, typing)
    4. Extracts results table
    
    Args:
        url: InfoByIP URL
        batch_text: IPs to lookup (one per line)
        log_path: Path to log file
    
    Returns:
        CSV text if successful, None otherwise
    """
    driver = None
    try:
        _log(log_path, "[advanced] 🚀 Starting undetected Chrome...")
        driver = _create_undetected_driver()
        
        # Navigate to page
        _log(log_path, "[advanced] 📡 Loading InfoByIP...")
        driver.get(url)
        
        # Wait for Cloudflare challenge to complete (if present)
        _log(log_path, "[advanced] ⏳ Waiting for Cloudflare challenge...")
        time.sleep(8)  # Give Cloudflare time to complete
        
        # Check if we're past Cloudflare
        page_source = driver.page_source.lower()
        if 'just a moment' in page_source or 'cloudflare' in page_source:
            _log(log_path, "[advanced] ⏳ Cloudflare detected, waiting longer...")
            time.sleep(15)  # Wait for challenge to complete
        
        # Random human-like actions before interacting
        _log(log_path, "[advanced] 🎭 Performing human-like actions...")
        driver.execute_script("window.scrollTo(0, 300);")
        _random_delay(1, 2)
        driver.execute_script("window.scrollTo(0, 0);")
        _random_delay(1, 2)
        
        # Find textarea with multiple fallback selectors
        _log(log_path, "[advanced] 🔍 Finding form elements...")
        textarea = None
        selectors = [
            (By.NAME, 'ips'),
            (By.ID, 'ips'),
            (By.CSS_SELECTOR, 'textarea[name="ips"]'),
            (By.CSS_SELECTOR, 'textarea'),
            (By.XPATH, '//textarea[@name="ips"]'),
        ]
        
        for by, selector in selectors:
            try:
                textarea = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                if textarea:
                    _log(log_path, f"[advanced] ✅ Found textarea using {by}={selector}")
                    break
            except:
                continue
        
        if not textarea:
            _log(log_path, "[advanced] ❌ Textarea not found")
            driver.save_screenshot(str(log_path.parent / "debug_screenshot.png"))
            (log_path.parent / "debug_page_advanced.html").write_text(driver.page_source, encoding='utf-8')
            return None
        
        # Scroll to textarea
        _scroll_smoothly(driver, textarea)
        
        # Click textarea (human-like)
        _random_delay(0.5, 1.0)
        textarea.click()
        _random_delay(0.3, 0.7)
        
        # Type IPs with human-like delays
        _log(log_path, "[advanced] ⌨️ Typing IPs (human-like)...")
        _human_like_typing(textarea, batch_text)
        _random_delay(1, 2)
        
        # Find and click submit button
        _log(log_path, "[advanced] 🔍 Finding submit button...")
        submit_button = None
        submit_selectors = [
            (By.CSS_SELECTOR, 'input[type="submit"]'),
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.XPATH, '//input[@type="submit"]'),
            (By.XPATH, '//button[type="submit"]'),
        ]
        
        for by, selector in submit_selectors:
            try:
                submit_button = driver.find_element(by, selector)
                if submit_button:
                    break
            except:
                continue
        
        if not submit_button:
            _log(log_path, "[advanced] ❌ Submit button not found")
            return None
        
        # Scroll to button
        _scroll_smoothly(driver, submit_button)
        
        # Click submit
        _log(log_path, "[advanced] 🖱️ Clicking submit...")
        _random_delay(0.5, 1.0)
        submit_button.click()
        
        # Wait for results with progressive delays
        _log(log_path, "[advanced] ⏳ Waiting for results...")
        _random_delay(5, 8)
        
        # Check for Cloudflare again after submit
        page_source = driver.page_source.lower()
        if 'just a moment' in page_source or 'cloudflare' in page_source:
            _log(log_path, "[advanced] ⏳ Cloudflare challenge after submit, waiting...")
            time.sleep(15)
        
        # Find results table
        _log(log_path, "[advanced] 🔍 Looking for results table...")
        table = None
        table_selectors = [
            (By.CSS_SELECTOR, 'table'),
            (By.XPATH, '//table'),
            (By.CSS_SELECTOR, '.table'),
            (By.ID, 'results'),
        ]
        
        for by, selector in table_selectors:
            try:
                tables = driver.find_elements(by, selector)
                for t in tables:
                    # Check if table has data
                    rows = t.find_elements(By.TAG_NAME, 'tr')
                    if len(rows) > 5:  # At least some data
                        table = t
                        _log(log_path, f"[advanced] ✅ Found table with {len(rows)} rows")
                        break
                if table:
                    break
            except:
                continue
        
        if not table:
            _log(log_path, "[advanced] ❌ Results table not found")
            driver.save_screenshot(str(log_path.parent / "debug_screenshot_results.png"))
            (log_path.parent / "debug_page_results.html").write_text(driver.page_source, encoding='utf-8')
            return None
        
        # Parse table to CSV
        _log(log_path, "[advanced] 📊 Parsing table...")
        rows = table.find_elements(By.TAG_NAME, 'tr')
        csv_lines = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if not cells:
                cells = row.find_elements(By.TAG_NAME, 'th')
            if cells:
                row_data = [cell.text.strip() for cell in cells]
                csv_lines.append(','.join(row_data))
        
        if len(csv_lines) < 2:
            _log(log_path, "[advanced] ❌ No data in table")
            return None
        
        csv_text = '\n'.join(csv_lines)
        _log(log_path, f"[advanced] ✅ Parsed {len(csv_lines)} rows")
        
        return csv_text
        
    except Exception as e:
        _log(log_path, f"[advanced] ❌ Error: {e}")
        if driver:
            try:
                driver.save_screenshot(str(log_path.parent / "debug_error.png"))
                (log_path.parent / "debug_error.html").write_text(driver.page_source, encoding='utf-8')
            except:
                pass
        return None
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def fetch_for_batch_advanced(batch_file: Path, out_csv: Path, log_path: Path, retry_count: int = 0) -> bool:
	"""
	Fetch InfoByIP data for batch using advanced anti-detection
	
	Args:
		batch_file: Path to batch file
		out_csv: Path to save CSV
		log_path: Path to log file
		retry_count: Current retry attempt
	
	Returns:
		True if successful
	"""
	if not UNDETECTED_AVAILABLE:
		_log(log_path, f"[advanced] ❌ undetected_chromedriver not available")
		_log(log_path, f"[advanced] Install with: pip install undetected-chromedriver")
		return False
	
	MAX_RETRIES = 2
	url = 'https://www.infobyip.com/ipbulklookup.php'
	
	try:
		batch_text = batch_file.read_text(encoding='utf-8')
		
		_log(log_path, f"[advanced] 🎯 Attempting advanced fetch for {batch_file.name} (attempt {retry_count + 1}/{MAX_RETRIES + 1})...")
		
		csv_text = fetch_with_undetected_chrome(url, batch_text, log_path)
		
		if csv_text:
			out_csv.write_text(csv_text, encoding='utf-8')
			_log(log_path, f"[advanced] ✅ Saved {out_csv.name}")
			return True
		else:
			if retry_count < MAX_RETRIES:
				wait_time = 30 * (retry_count + 1)  # 30s, 60s
				_log(log_path, f"[advanced] ⏳ Retry {retry_count + 1}/{MAX_RETRIES} failed. Waiting {wait_time}s...")
				time.sleep(wait_time)
				return fetch_for_batch_advanced(batch_file, out_csv, log_path, retry_count + 1)
			else:
				_log(log_path, f"[advanced] ❌ Failed after {MAX_RETRIES + 1} attempts")
				return False
				
	except Exception as e:
		_log(log_path, f"[advanced] ❌ Exception: {e}")
		return False


def auto_fetch_batches_advanced(run_dir: Path) -> int:
    """
    Auto-fetch all batches using advanced anti-detection
{{ ... }}
    Args:
        run_dir: Directory containing batch files
    
    Returns:
        Number of successfully fetched batches
    """
    log_path = run_dir / 'process_log.txt'
    batches = sorted(run_dir.glob('batch_*.txt'))
    
    _log(log_path, "")
    _log(log_path, "[advanced] ═══════════════════════════════════════════")
    _log(log_path, "[advanced] 🔥 ADVANCED ANTI-DETECTION MODE")
    _log(log_path, "[advanced] Using undetected-chromedriver")
    _log(log_path, f"[advanced] Total batches: {len(batches)}")
    _log(log_path, "[advanced] ═══════════════════════════════════════════")
    
    count = 0
    
    for idx, batch in enumerate(batches, 1):
        num = batch.stem.split('_')[-1]
        out = run_dir / f"infobyip_batch_{num}.csv"
        
        if out.exists():
            _log(log_path, f"[advanced] [{idx}/{len(batches)}] Skipping {batch.name} (already exists)")
            count += 1
            continue
        
        _log(log_path, f"[advanced] [{idx}/{len(batches)}] Processing {batch.name}...")
        
        if fetch_for_batch_advanced(batch, out, log_path):
            count += 1
            _log(log_path, f"[advanced] [{idx}/{len(batches)}] ✅ Success! ({count}/{len(batches)} completed)")
        else:
            _log(log_path, f"[advanced] [{idx}/{len(batches)}] ❌ Failed")
        
        # Long delay between batches (30-60 seconds)
        if idx < len(batches):
            delay = random.uniform(30, 60)
            _log(log_path, f"[advanced] ⏳ Waiting {delay:.1f}s before next batch (anti-detection)...")
            time.sleep(delay)
    
    _log(log_path, "[advanced] ═══════════════════════════════════════════")
    _log(log_path, f"[advanced] Completed: {count}/{len(batches)} batches")
    _log(log_path, f"[advanced] Success rate: {(count/len(batches)*100):.1f}%")
    _log(log_path, "[advanced] ═══════════════════════════════════════════")
    
    return count
