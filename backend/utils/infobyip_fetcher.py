import os
import time
import random
from pathlib import Path
from typing import Optional, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _log(log_path: Path, message: str) -> None:
	log_path.parent.mkdir(parents=True, exist_ok=True)
	with log_path.open('a', encoding='utf-8', newline='') as f:
		f.write(message + "\n")


def _create_session() -> requests.Session:
	"""Create a session with retry logic and realistic headers"""
	session = requests.Session()
	
	# Retry strategy
	retry_strategy = Retry(
		total=3,
		backoff_factor=2,
		status_forcelist=[429, 500, 502, 503, 504],
		allowed_methods=["GET", "POST"]
	)
	adapter = HTTPAdapter(max_retries=retry_strategy)
	session.mount("http://", adapter)
	session.mount("https://", adapter)
	
	# Realistic browser headers
	session.headers.update({
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.9',
		'Accept-Encoding': 'gzip, deflate, br',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'none',
		'Cache-Control': 'max-age=0',
		'DNT': '1'
	})
	
	return session


def _http_submit(url: str, batch_text: str, timeout: int = 60, session: Optional[requests.Session] = None) -> Optional[str]:
	"""Submit batch to InfoByIP with realistic behavior"""
	if session is None:
		session = _create_session()
	
	# Human-like delay before request (1-3 seconds)
	time.sleep(random.uniform(1.0, 3.0))
	
	data = {"ips": batch_text}
	
	try:
		r = session.post(url, data=data, timeout=timeout)
		r.raise_for_status()
		
		# Expect CSV content in response text
		ct = r.headers.get('content-type', '')
		if 'text/csv' in ct or r.text.count('\n') > 1:
			return r.text
		return None
	except requests.exceptions.RequestException as e:
		print(f"HTTP request failed: {e}")
		return None


def _selenium_submit(url: str, batch_text: str, timeout: int = 180) -> Optional[str]:
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        
        # Enhanced Chrome options to avoid detection
        opts = ChromeOptions()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional arguments to appear more human-like
        opts.add_argument('--window-size=1920,1080')
        opts.add_argument('--start-maximized')
        opts.add_argument('--disable-extensions')
        opts.add_argument('--disable-popup-blocking')
        opts.add_argument('--disable-notifications')
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)
        
        # Execute CDP commands to hide webdriver
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    except Exception as e:
        print(f"Selenium initialization error: {e}")
        return None
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Wait for textarea to be present
        wait = WebDriverWait(driver, 10)
        
        # Try multiple reasonable selectors for the textarea
        textarea = None
        selectors = [
            'textarea#list',
            'textarea[name="list"]',
            'textarea[name="ips"]',
            'textarea[name*="ip"]',
            'textarea.form-control',
            'textarea'
        ]
        
        for sel in selectors:
            try:
                textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                if textarea and textarea.is_displayed():
                    break
            except Exception:
                pass
        
        if not textarea:
            print("Textarea not found")
            return None
        
        # Scroll to textarea
        driver.execute_script("arguments[0].scrollIntoView(true);", textarea)
        time.sleep(1)
        
        # Clear and fill textarea
        textarea.clear()
        time.sleep(0.5)
        textarea.send_keys(batch_text)
        time.sleep(1)

        # Find and click submit button
        submit = None
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button[name*="lookup"]',
            'button[name*="submit"]',
            'input[value*="Lookup"]',
            'button.btn-primary',
            'button',
            'input.btn'
        ]
        
        for sel in submit_selectors:
            try:
                submit = driver.find_element(By.CSS_SELECTOR, sel)
                if submit and submit.is_displayed():
                    break
            except Exception:
                pass
        
        if not submit:
            print("Submit button not found, trying keyboard submit")
            textarea.send_keys(Keys.CONTROL, Keys.ENTER)
        else:
            # Scroll to button and click
            driver.execute_script("arguments[0].scrollIntoView(true);", submit)
            time.sleep(0.5)
            submit.click()
        
        print("Form submitted, waiting for results...")
        time.sleep(5)  # Give more time for processing

        # Wait for results to appear
        deadline = time.time() + 90
        table = None
        while time.time() < deadline:
            try:
                # Look for result table
                tables = driver.find_elements(By.CSS_SELECTOR, 'table')
                for t in tables:
                    if t.is_displayed() and len(t.find_elements(By.CSS_SELECTOR, 'tr')) > 1:
                        table = t
                        break
                if table:
                    break
            except Exception as e:
                print(f"Waiting for table: {e}")
            time.sleep(2)
        
        if not table:
            print("Results table not found")
            # Save page source for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            return None
        print("Table found, parsing results...")
        
        # Parse table into CSV
        rows = table.find_elements(By.CSS_SELECTOR, 'tr')
        grid: List[List[str]] = []
        for i, tr in enumerate(rows):
            cells = tr.find_elements(By.CSS_SELECTOR, 'th,td')
            row_data = [c.text.strip() for c in cells if c.text.strip()]
            if row_data:  # Only add non-empty rows
                grid.append(row_data)
        
        # Ensure we have data
        if not grid or len(grid) < 2:
            print(f"Insufficient data in table: {len(grid)} rows")
            return None
        
        print(f"Parsed {len(grid)} rows from table")
        
        # Convert to CSV text
        import csv, io
        buf = io.StringIO()
        w = csv.writer(buf)
        for r in grid:
            w.writerow(r)
        
        csv_content = buf.getvalue()
        print(f"Generated CSV with {len(csv_content)} characters")
        return csv_content
        
    except Exception as e:
        print(f"Error during Selenium execution: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


def fetch_for_batch(batch_file: Path, out_csv: Path, log_path: Path, session: Optional[requests.Session] = None, retry_count: int = 0) -> bool:
	"""
	Attempt to fetch InfoByIP CSV for the given batch file with smart rate limiting.
	
	Args:
		batch_file: Path to batch file containing IPs
		out_csv: Path to save CSV output
		log_path: Path to log file
		session: Reusable requests session
		retry_count: Current retry attempt (max 3)
	
	Returns:
		True if CSV was successfully fetched and saved
	"""
	MAX_RETRIES = 3
	url = os.getenv('INFOBYIP_URL', 'https://www.infobyip.com/ipbulklookup.php').strip()
	batch_text = batch_file.read_text(encoding='utf-8')
	
	# Create session if not provided
	if session is None:
		session = _create_session()
	
	try:
		csv_text = None
		
		# Strategy 1: Try HTTP POST with realistic headers and delays
		_log(log_path, f"[auto] Attempting HTTP request for {batch_file.name} (attempt {retry_count + 1}/{MAX_RETRIES})...")
		
		try:
			csv_text = _http_submit(url, batch_text, session=session)
		except Exception as e:
			_log(log_path, f"[auto] HTTP failed for {batch_file.name}: {e}")
		
		# Strategy 2: If HTTP fails and we haven't exceeded retries, try Selenium
		if not csv_text and retry_count < MAX_RETRIES:
			# Exponential backoff: 5s, 10s, 20s
			wait_time = 5 * (2 ** retry_count)
			_log(log_path, f"[auto] HTTP failed. Waiting {wait_time}s before Selenium attempt...")
			time.sleep(wait_time)
			
			_log(log_path, f"[auto] Trying Selenium for {batch_file.name}...")
			csv_text = _selenium_submit(url, batch_text)
		
		# Strategy 3: If still no data and retries available, retry with longer delay
		if not csv_text and retry_count < MAX_RETRIES:
			wait_time = 10 * (2 ** retry_count)  # 10s, 20s, 40s
			_log(log_path, f"[auto] Retry {retry_count + 1}/{MAX_RETRIES} failed. Waiting {wait_time}s before retry...")
			time.sleep(wait_time)
			
			# Recursive retry
			return fetch_for_batch(batch_file, out_csv, log_path, session, retry_count + 1)
		
		if not csv_text:
			_log(log_path, f"[auto] ❌ Could not retrieve CSV for {batch_file.name} after {MAX_RETRIES} attempts")
			return False
		
		# Success! Save the CSV
		out_csv.write_text(csv_text, encoding='utf-8')
		_log(log_path, f"[auto] ✅ Saved {out_csv.name} from {batch_file.name}")
		return True
		
	except Exception as e:
		_log(log_path, f"[auto][error] {batch_file.name}: {e}")
		
		# Retry on exception if retries available
		if retry_count < MAX_RETRIES:
			wait_time = 10 * (2 ** retry_count)
			_log(log_path, f"[auto] Exception occurred. Retrying in {wait_time}s...")
			time.sleep(wait_time)
			return fetch_for_batch(batch_file, out_csv, log_path, session, retry_count + 1)
		
		return False


def auto_fetch_batches(run_dir: Path) -> int:
	"""
	Automatically fetch IP data for all batches with smart rate limiting.
	
	Implements:
	- Random delays between requests (5-15 seconds)
	- Session reuse for realistic behavior
	- Exponential backoff on failures
	- Maximum 3 retries per batch
	- Human-like timing patterns
	
	Args:
		run_dir: Directory containing batch files
	
	Returns:
		Number of successfully fetched batches
	"""
	log_path = run_dir / 'process_log.txt'
	count = 0
	batches = sorted(run_dir.glob('batch_*.txt'))
	
	_log(log_path, f"[auto] ═══════════════════════════════════════════")
	_log(log_path, f"[auto] Starting SMART auto-fetch for {len(batches)} batches")
	_log(log_path, f"[auto] Strategy: Rate-limited with human-like delays")
	_log(log_path, f"[auto] ═══════════════════════════════════════════")
	
	# Create persistent session for all batches
	session = _create_session()
	
	for idx, batch in enumerate(batches, 1):
		num = batch.stem.split('_')[-1]
		out = run_dir / f"infobyip_batch_{num}.csv"
		
		if out.exists():
			_log(log_path, f"[auto] [{idx}/{len(batches)}] Skipping {batch.name} (CSV already exists)")
			count += 1
			continue
		
		_log(log_path, f"[auto] [{idx}/{len(batches)}] Processing {batch.name}...")
		
		# Attempt to fetch with retries
		if fetch_for_batch(batch, out, log_path, session=session):
			count += 1
			_log(log_path, f"[auto] [{idx}/{len(batches)}] ✅ Success! ({count}/{len(batches)} completed)")
		else:
			_log(log_path, f"[auto] [{idx}/{len(batches)}] ❌ Failed after all retries")
		
		# Smart delay between batches (random 5-15 seconds to appear human)
		if idx < len(batches):
			# Random delay with slight variation
			base_delay = random.uniform(5.0, 15.0)
			
			# Add extra delay every 3rd batch to avoid pattern detection
			if idx % 3 == 0:
				base_delay += random.uniform(5.0, 10.0)
				_log(log_path, f"[auto] Taking extended break ({base_delay:.1f}s) to avoid detection...")
			else:
				_log(log_path, f"[auto] Waiting {base_delay:.1f}s before next batch (human-like delay)...")
			
			time.sleep(base_delay)
	
	_log(log_path, f"[auto] ═══════════════════════════════════════════")
	_log(log_path, f"[auto] Fetch completed: {count}/{len(batches)} batches successful")
	_log(log_path, f"[auto] Success rate: {(count/len(batches)*100):.1f}%")
	_log(log_path, f"[auto] ═══════════════════════════════════════════")
	
	return count



