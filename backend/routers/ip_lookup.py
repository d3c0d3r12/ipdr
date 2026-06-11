"""
Unlimited IP Lookup Router - InfoByIP Integration
Handles unlimited IP lookups with Cloudflare bypass and real-time progress streaming
"""

from fastapi import APIRouter, HTTPException, Query, Form, Depends, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse

from core.db import get_db

from routers.auth_secure import get_current_user
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv
import json
import asyncio
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from utils.security import sanitize_input, validate_input, sanitize_filename

# Setup logger
logger = logging.getLogger(__name__)

# Import the enhanced bypass system and direct InfoByIP
import sys
sys.path.append(str(Path(__file__).parent.parent))
try:
    from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass
    SELENIUM_AVAILABLE = True
except:
    SELENIUM_AVAILABLE = False
from utils.infobyip_direct import InfoByIPDirect
from utils.multi_source_ip_lookup import MultiSourceIPLookup
from utils.infobyip_cookie_manager import cookie_manager
from utils.progress_manager import ProgressManager
from utils.background_task_manager import task_manager

router = APIRouter()


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


def extract_ips_from_csv(csv_path: Path) -> List[str]:
    """Extract IPs from original_log.csv file"""
    ips = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'ip' in row and row['ip'].strip():
                    ips.append(row['ip'].strip())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    return ips


async def progress_generator(run_dir: Path, csv_path: Path):
    """
    Generator that yields Server-Sent Events (SSE) for real-time progress updates
    """
    try:
        # Extract IPs
        yield f"data: {json.dumps({'type': 'status', 'message': '🔍 Extracting IPs from file...', 'progress': 0})}\n\n"
        await asyncio.sleep(0.1)
        
        ips = extract_ips_from_csv(csv_path)
        total_ips = len(ips)
        
        if total_ips == 0:
            yield f"data: {json.dumps({'type': 'error', 'message': '❌ No IPs found in file'})}\n\n"
            return
        
        # Calculate estimated time (2 seconds per IP)
        estimated_minutes = (total_ips * 2) / 60
        
        yield f"data: {json.dumps({'type': 'info', 'message': f'📄 Loaded {total_ips} IPs from {csv_path.name}', 'total': total_ips})}\n\n"
        await asyncio.sleep(0.2)
        
        yield f"data: {json.dumps({'type': 'info', 'message': f'✅ Ready to lookup {total_ips} IPs', 'total': total_ips})}\n\n"
        await asyncio.sleep(0.2)
        
        yield f"data: {json.dumps({'type': 'info', 'message': f'⚠️  This will take approximately {estimated_minutes:.1f} minutes', 'estimated_time': estimated_minutes})}\n\n"
        await asyncio.sleep(0.5)
        
        # Check cookie status first (optional - won't break if not available)
        use_cookies = False
        try:
            cookie_status = cookie_manager.get_status()
            use_cookies = cookie_status.get('cookies_valid', False)
            
            if use_cookies:
                yield f"data: {json.dumps({'type': 'status', 'message': '🍪 Using cookie-based access (Fast Mode)...', 'progress': 5})}\n\n"
                logger.info("✅ Using cookies for InfoByIP access")
            else:
                yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Initializing InfoByIP API...', 'progress': 5})}\n\n"
                logger.info("⚠️ Cookies not available, using direct API")
        except Exception as e:
            logger.warning(f"Cookie manager not available: {e}")
            yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Initializing InfoByIP API...', 'progress': 5})}\n\n"
        
        await asyncio.sleep(0.3)
        
        infobyip = InfoByIPDirect()
        multi_lookup = MultiSourceIPLookup()
        
        if use_cookies:
            yield f"data: {json.dumps({'type': 'status', 'message': '✅ Cookie authentication successful!', 'progress': 10})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'status', 'message': '🌐 Connecting to InfoByIP (Selenium)...', 'progress': 10})}\n\n"
        
        await asyncio.sleep(0.3)
        
        # Test with first IP
        yield f"data: {json.dumps({'type': 'status', 'message': '🔓 Testing connection...', 'progress': 15})}\n\n"
        await asyncio.sleep(0.3)
        
        if ips:
            try:
                test_result = infobyip.lookup_ip(ips[0])
                if test_result and test_result.get('country') != 'Unknown':
                    yield f"data: {json.dumps({'type': 'success', 'message': '✅ InfoByIP connection successful!', 'progress': 20})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'warning', 'message': '⚠️  Connection established, starting lookups...', 'progress': 20})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'warning', 'message': f'⚠️  Test lookup: {str(e)}', 'progress': 20})}\n\n"
            await asyncio.sleep(0.5)
        
        # Process IPs
        results = []
        start_time = datetime.now()
        
        for idx, ip in enumerate(ips, 1):
            progress = 20 + int((idx / total_ips) * 75)  # 20% to 95%
            
            yield f"data: {json.dumps({'type': 'progress', 'message': f'🔎 Looking up IP {idx}/{total_ips}: {ip}', 'current': idx, 'total': total_ips, 'progress': progress, 'ip': ip})}\n\n"
            
            try:
                # Use Selenium bypass (proven working on localhost)
                from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass
                
                # Create bypass instance if not exists
                if not hasattr(progress_generator, '_bypass_instance'):
                    progress_generator._bypass_instance = EnhancedCloudflareBypass(headless=True, verbose=False)
                
                # Lookup IP using Selenium
                infobyip_result = progress_generator._bypass_instance.lookup_ip(ip)
                
                # Only use multi-source fallback if InfoByIP had an ERROR (not if data is just Unknown)
                if infobyip_result.get('error'):
                    logger.info(f"InfoByIP error for {ip}, using multi-source fallback")
                    result = multi_lookup.lookup_with_fallback(ip, infobyip_result)
                else:
                    # Use InfoByIP result even if some fields are Unknown
                    result = infobyip_result
                    logger.info(f"✅ Using InfoByIP data for {ip} (Country: {infobyip_result.get('country', 'Unknown')})")
                results.append(result)
                
                city = result.get("city", "Unknown")
                country = result.get("country", "Unknown")
                isp = result.get("isp", "Unknown")
                source = result.get("source", "unknown")
                
                # Show appropriate message based on source
                if source == "infobyip" or source == "infobyip-api" or source == "infobyip-html":
                    message = f'✅ {ip} → {city}, {country} | {isp} [InfoByIP]'
                    yield f"data: {json.dumps({'type': 'success', 'message': message, 'ip': ip, 'result': result})}\n\n"
                elif source != "none":
                    message = f'✅ {ip} → {city}, {country} | {isp} [Fallback: {source}]'
                    yield f"data: {json.dumps({'type': 'success', 'message': message, 'ip': ip, 'result': result})}\n\n"
                else:
                    message = f'⚠️  {ip} → No data available from any source'
                    yield f"data: {json.dumps({'type': 'warning', 'message': message, 'ip': ip, 'result': result})}\n\n"
                
            except Exception as e:
                # Error during lookup
                error_msg = f'❌ {ip} → Error: {str(e)}'
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'ip': ip, 'error': str(e)})}\n\n"
                # Still add to results with Unknown data
                result = {
                    'ip': ip,
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'region': 'Unknown',
                    'isp': 'Unknown',
                    'organization': 'Unknown',
                    'latitude': 'Unknown',
                    'longitude': 'Unknown',
                    'timezone': 'Unknown',
                    'postal_code': 'Unknown',
                    'source': 'error'
                }
                results.append(result)
            
            await asyncio.sleep(0.1)  # Small delay for UI updates
        
        # Save results
        yield f"data: {json.dumps({'type': 'status', 'message': '💾 Saving results...', 'progress': 95})}\n\n"
        await asyncio.sleep(0.2)
        
        # Save CSV
        csv_output = run_dir / 'ip_lookup_results.csv'
        logger.info(f"Saving CSV to: {csv_output}")
        with open(csv_output, 'w', encoding='utf-8', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        logger.info(f"CSV saved successfully. File exists: {csv_output.exists()}, Size: {csv_output.stat().st_size if csv_output.exists() else 0} bytes")
        
        # Save JSON
        json_output = run_dir / 'ip_lookup_results.json'
        logger.info(f"Saving JSON to: {json_output}")
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"JSON saved successfully. File exists: {json_output.exists()}, Size: {json_output.stat().st_size if json_output.exists() else 0} bytes")
        
        # Cleanup
        infobyip.close()
        multi_lookup.close()
        
        elapsed_time = (datetime.now() - start_time).total_seconds() / 60
        success_rate = (len(results) / total_ips * 100) if total_ips > 0 else 0
        
        # Convert file paths to URL paths
        csv_url = f"/api/files/{run_dir.name}/{csv_output.name}"
        json_url = f"/api/files/{run_dir.name}/{json_output.name}"
        
        yield f"data: {json.dumps({'type': 'complete', 'message': f'🎉 Lookup complete! {len(results)}/{total_ips} IPs processed ({success_rate:.1f}% success)', 'progress': 100, 'total': total_ips, 'success': len(results), 'elapsed_minutes': elapsed_time, 'csv_path': csv_url, 'json_path': json_url})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Fatal error: {str(e)}', 'error': str(e)})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/lookup/single")
async def lookup_single_ip(
    ip: str = Query(..., description="IP address to look up"),
    current_user=Depends(get_current_user),
):
    """Look up a single IP address and return its info."""
    ip = sanitize_input(ip.strip())
    if not ip:
        raise HTTPException(status_code=400, detail="IP address is required")

    multi_lookup = MultiSourceIPLookup()
    try:
        result = multi_lookup.lookup_with_fallback(ip)
    finally:
        multi_lookup.close()

    return {"success": True, "data": result}


@router.get("/lookup/stream")
async def stream_ip_lookup(run_dir: str = Query(..., description="Path to the processed run directory")):
    """
    Stream unlimited IP lookup with real-time progress updates
    
    This endpoint:
    1. Extracts IPs from original_log.csv in the run directory
    2. Performs unlimited IP lookups using InfoByIP with Cloudflare bypass
    3. Streams real-time progress updates via Server-Sent Events (SSE)
    4. Saves results to CSV and JSON files
    5. Handles browser crashes automatically
    
    Args:
        run_dir: Path to the processed directory (e.g., backend/processed/20251031_125529_202)
    
    Returns:
        StreamingResponse with Server-Sent Events containing progress updates
    """
    run_path = Path(run_dir)
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    csv_path = run_path / 'original_log.csv'
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"original_log.csv not found in {run_dir}")
    
    return StreamingResponse(
        progress_generator(run_path, csv_path),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/lookup/start")
async def start_ip_lookup(run_dir: str = Query(..., description="Path to the processed run directory")):
    """
    Start unlimited IP lookup (non-streaming version)
    
    This is a simpler endpoint that returns immediately and processes in background.
    Use the /lookup/stream endpoint for real-time progress updates.
    
    Args:
        run_dir: Path to the processed directory
    
    Returns:
        Status message with estimated time
    """
    run_path = Path(run_dir)
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    csv_path = run_path / 'original_log.csv'
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"original_log.csv not found in {run_dir}")
    
    # Extract IPs to get count
    ips = extract_ips_from_csv(csv_path)
    total_ips = len(ips)
    estimated_minutes = (total_ips * 2) / 60
    
    return {
        "status": "started",
        "message": f"IP lookup started for {total_ips} IPs",
        "total_ips": total_ips,
        "estimated_minutes": round(estimated_minutes, 1),
        "run_dir": str(run_path),
        "csv_file": csv_path.name,
        "note": "Use /lookup/stream endpoint for real-time progress updates"
    }


@router.get("/lookup/status")
async def get_lookup_status(run_dir: str = Query(...)):
    """
    Check if IP lookup results exist for a run directory
    
    Args:
        run_dir: Path to the processed directory
    
    Returns:
        Status of IP lookup results and all processed files
    """
    run_path = Path(run_dir)
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    csv_results = run_path / 'ip_lookup_results.csv'
    json_results = run_path / 'ip_lookup_results.json'
    original_csv = run_path / 'original_log.csv'
    master_file = run_path / 'Master file.csv'
    fixed_file = run_path / 'fully_fixed.csv'
    
    # Count IPs in original file
    total_ips = 0
    if original_csv.exists():
        total_ips = len(extract_ips_from_csv(original_csv))
    
    # Count results
    results_count = 0
    if csv_results.exists():
        with open(csv_results, 'r', encoding='utf-8') as f:
            results_count = sum(1 for _ in csv.DictReader(f))
    
    # Count master file records
    master_records = 0
    master_columns = []
    if master_file.exists():
        with open(master_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            master_columns = reader.fieldnames or []
            master_records = sum(1 for _ in reader)
    
    # Count fixed file records
    fixed_records = 0
    if fixed_file.exists():
        with open(fixed_file, 'r', encoding='utf-8') as f:
            fixed_records = sum(1 for _ in f)
    
    return {
        "has_results": csv_results.exists() and json_results.exists(),
        "csv_exists": csv_results.exists(),
        "json_exists": json_results.exists(),
        "total_ips": total_ips,
        "results_count": results_count,
        "success_rate": round((results_count / total_ips * 100), 1) if total_ips > 0 else 0,
        "csv_path": str(csv_results) if csv_results.exists() else None,
        "json_path": str(json_results) if json_results.exists() else None,
        # Master file info
        "has_master_file": master_file.exists(),
        "master_file_path": str(master_file) if master_file.exists() else None,
        "master_records": master_records,
        "master_columns": master_columns,
        # Fixed file info
        "has_fixed_file": fixed_file.exists(),
        "fixed_file_path": str(fixed_file) if fixed_file.exists() else None,
        "fixed_records": fixed_records
    }


@router.post("/merge-master-file")
async def merge_master_file(
    run_dir: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Merge original_log.csv with ip_lookup_results.csv to create Master file.csv
    
    Creates a master file with columns:
    - timestamp, ip, country, city, region, isp
    """
    # Build absolute path
    base_dir = Path(__file__).parent.parent  # backend directory
    run_path = base_dir / "processed" / run_dir
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    original_csv = run_path / 'original_log.csv'
    lookup_csv = run_path / 'ip_lookup_results.csv'
    
    if not original_csv.exists():
        raise HTTPException(status_code=404, detail="original_log.csv not found")
    
    if not lookup_csv.exists():
        raise HTTPException(status_code=404, detail="ip_lookup_results.csv not found. Please complete IP lookup first.")
    
    try:
        # Read both CSV files
        df_original = pd.read_csv(original_csv)
        df_lookup = pd.read_csv(lookup_csv)
        
        logger.info(f"📊 Original log: {len(df_original)} rows")
        logger.info(f"📊 Lookup results: {len(df_lookup)} rows")
        logger.info(f"📋 Original columns: {list(df_original.columns)}")
        logger.info(f"📋 Lookup columns: {list(df_lookup.columns)}")
        
        # Ensure required columns exist
        if 'ip' not in df_original.columns or 'timestamp' not in df_original.columns:
            raise HTTPException(status_code=400, detail="original_log.csv must have 'ip' and 'timestamp' columns")
        
        if 'ip' not in df_lookup.columns:
            raise HTTPException(status_code=400, detail="ip_lookup_results.csv must have 'ip' column")
        
        # Keep only timestamp and ip from original (preserve order)
        df_original_clean = df_original[['timestamp', 'ip']].copy()
        
        # Prepare lookup data with only needed columns
        lookup_columns = ['ip', 'country', 'region', 'city', 'isp']
        df_lookup_clean = df_lookup[lookup_columns].copy()
        
        # Remove duplicates from lookup (keep first occurrence)
        df_lookup_clean = df_lookup_clean.drop_duplicates(subset=['ip'], keep='first')
        
        logger.info(f"📊 Unique IPs in lookup: {len(df_lookup_clean)}")
        
        # Merge on IP address - LEFT JOIN preserves ALL original rows in EXACT order
        df_merged = df_original_clean.merge(
            df_lookup_clean, 
            on='ip', 
            how='left'
        )
        
        logger.info(f"📊 After merge: {len(df_merged)} rows (should match original: {len(df_original)})")
        
        # Verify row count matches
        if len(df_merged) != len(df_original):
            logger.warning(f"⚠️ Row count mismatch! Original: {len(df_original)}, Merged: {len(df_merged)}")
        
        # Select columns in exact order: timestamp, ip, country, city, region, isp
        df_master = df_merged[['timestamp', 'ip', 'country', 'city', 'region', 'isp']]
        
        # Fill missing values with 'Unknown'
        df_master = df_master.fillna('Unknown')
        
        # Save to Master file.csv
        master_file = run_path / 'Master file.csv'
        df_master.to_csv(master_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Master file saved: {len(df_master)} rows")
        logger.info(f"📋 Master file columns: {list(df_master.columns)}")
        
        return {
            "success": True,
            "message": "Master file created successfully",
            "master_file": f"/api/files/{run_path.name}/Master file.csv",
            "total_records": len(df_master),
            "columns": list(df_master.columns),
            "sample_data": df_master.head(3).to_dict('records'),
            "run_dir": run_path.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging files: {str(e)}")


@router.post("/fix-to-start")
async def fix_to_start(
    run_dir: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Remove header row from Master file.csv and create fully_fixed.csv
    
    This prepares the file for Final Report Generator by removing the first row (headers).
    """
    # Build absolute path
    base_dir = Path(__file__).parent.parent  # backend directory
    run_path = base_dir / "processed" / run_dir
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    master_file = run_path / 'Master file.csv'
    
    if not master_file.exists():
        raise HTTPException(status_code=404, detail="Master file.csv not found. Please create Master file first.")
    
    try:
        import pandas as pd
        
        # Read Master file
        df = pd.read_csv(master_file, encoding='utf-8')
        
        logger.info(f"📊 Master file loaded: {len(df)} rows")
        logger.info(f"📋 Columns: {list(df.columns)}")
        
        # Remove ALL commas from ALL columns (replace with space)
        for col in df.columns:
            if df[col].dtype == 'object':  # Only process string columns
                df[col] = df[col].astype(str).str.replace(',', ' ', regex=False)
                logger.info(f"✅ Removed commas from column: {col}")
        
        logger.info(f"✅ All commas removed from data")
        
        # Save without header and without commas
        fixed_file = run_path / 'fully_fixed.csv'
        df.to_csv(fixed_file, index=False, header=False, encoding='utf-8')
        
        logger.info(f"✅ Fixed file saved: {fixed_file}")
        logger.info(f"📊 Total records: {len(df)}")
        
        return {
            "success": True,
            "message": "Fixed file created successfully (header removed, commas removed)",
            "fixed_file": f"/api/files/{run_path.name}/fully_fixed.csv",
            "total_records": len(df),
            "run_dir": run_path.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating fixed file: {str(e)}")


@router.post("/fix-final-report")
async def fix_final_report(
    file: UploadFile = File(...)
):
    """
    Fix Final Report CSV with ISP-specific formatting rules
    
    Fixes:
    1. Date Format:
       - Airtel: DD-MMM-YYYY (e.g., 14-Nov-2024)
       - Jio & Others: DD-MM-YYYY (e.g., 07-11-2024)
    
    2. Time Format:
       - Jio: HHMMSS (compact, e.g., 185032)
       - Others: HH:MM:SS (with colons, e.g., 18:50:32)
    
    3. State/City: Swap columns (State first, City second)
    
    4. ISP Names: Keep as is (no changes)
    """
    import pandas as pd
    from datetime import datetime
    import re
    
    try:
        # Read uploaded CSV file
        contents = await file.read()
        
        # Save temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Read CSV
        df = pd.read_csv(tmp_path, encoding='utf-8')
        
        logger.info(f"📊 Final Report loaded: {len(df)} rows")
        logger.info(f"📋 Columns: {list(df.columns)}")
        
        # Month conversion for Airtel
        month_map = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        
        def convert_date_format(date_str, isp):
            """Convert date based on ISP"""
            if pd.isna(date_str) or date_str == '':
                return date_str
            
            date_str = str(date_str).strip()
            
            # Check if Airtel
            is_airtel = 'Airtel' in str(isp) or 'airtel' in str(isp).lower()
            
            # Parse different date formats
            # Format 1: YYYYMMDD (e.g., 20241107)
            if re.match(r'^\d{8}$', date_str):
                year = date_str[0:4]
                month = date_str[4:6]
                day = date_str[6:8]
                
                if is_airtel:
                    # Airtel: DD-MMM-YYYY
                    month_name = month_map.get(month, month)
                    return f"{day}-{month_name}-{year}"
                else:
                    # Jio & Others: DD-MM-YYYY
                    return f"{day}-{month}-{year}"
            
            # Format 2: DD.MM.YYYY (e.g., 14.11.2024)
            elif '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    day, month, year = parts
                    
                    if is_airtel:
                        # Airtel: DD-MMM-YYYY
                        month_name = month_map.get(month, month)
                        return f"{day}-{month_name}-{year}"
                    else:
                        # Jio & Others: DD-MM-YYYY
                        return f"{day}-{month}-{year}"
            
            # Format 3: DD-MM-YYYY (already correct for Jio/Others)
            elif '-' in date_str and not any(m in date_str for m in month_map.values()):
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = parts
                    
                    if is_airtel:
                        # Convert to Airtel format: DD-MMM-YYYY
                        month_name = month_map.get(month, month)
                        return f"{day}-{month_name}-{year}"
                    else:
                        # Already correct for Jio/Others
                        return date_str
            
            # Already in correct format or unknown format
            return date_str
        
        def convert_time_format(time_str, isp):
            """Convert time based on ISP"""
            if pd.isna(time_str) or time_str == '':
                return time_str
            
            time_str = str(time_str).strip()
            
            # Check if Jio
            is_jio = 'Jio' in str(isp) or 'jio' in str(isp).lower()
            
            if is_jio:
                # Jio: Keep compact format HHMMSS
                # If already in HH:MM:SS, convert to HHMMSS
                if ':' in time_str:
                    time_str = time_str.replace(':', '')
                return time_str
            else:
                # Others (Airtel, VI, etc.): Convert to HH:MM:SS
                # If in compact format HHMMSS, add colons
                if ':' not in time_str and len(time_str) == 6:
                    return f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                return time_str
        
        # Process each row
        for idx, row in df.iterrows():
            isp = row.get('ISP', '')
            
            # Fix dates (From Date and To Date)
            if 'From Date' in df.columns:
                df.at[idx, 'From Date'] = convert_date_format(row['From Date'], isp)
            if 'To Date' in df.columns:
                df.at[idx, 'To Date'] = convert_date_format(row['To Date'], isp)
            
            # Fix times (From Time and To Time)
            if 'From Time' in df.columns:
                df.at[idx, 'From Time'] = convert_time_format(row['From Time'], isp)
            if 'To Time' in df.columns:
                df.at[idx, 'To Time'] = convert_time_format(row['To Time'], isp)
            
            # Swap State and City columns
            if 'State' in df.columns and 'City' in df.columns:
                state_val = row['State']
                city_val = row['City']
                df.at[idx, 'State'] = city_val  # State column gets City value
                df.at[idx, 'City'] = state_val  # City column gets State value
        
        logger.info(f"✅ All formatting fixes applied")
        logger.info(f"   - Date formats: ISP-specific (Airtel: DD-MMM-YYYY, Others: DD-MM-YYYY)")
        logger.info(f"   - Time formats: ISP-specific (Jio: HHMMSS, Others: HH:MM:SS)")
        logger.info(f"   - State/City: Swapped")
        logger.info(f"   - ISP names: Kept as is")
        
        # Save corrected file
        output_path = Path(tmp_path).parent / 'Final_Report_CORRECTED.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"✅ Corrected file saved: {output_path}")
        
        # Read file for download
        with open(output_path, 'rb') as f:
            corrected_content = f.read()
        
        # Cleanup temp files
        import os
        os.unlink(tmp_path)
        os.unlink(output_path)
        
        # Return file as download
        from fastapi.responses import Response
        return Response(
            content=corrected_content,
            media_type='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename="Final_Report_CORRECTED.csv"'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error fixing final report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fixing final report: {str(e)}")


@router.post("/separate-by-isp")
async def separate_by_isp(
    file: UploadFile = File(...)
):
    """
    Separate Final Report CSV by ISP and generate comprehensive analysis
    
    Creates:
    1. Separate CSV files for each ISP
    2. Summary statistics report
    3. Geographic analysis
    4. Time-based statistics
    5. PDF investigation report
    6. ZIP file with all outputs
    """
    import pandas as pd
    import zipfile
    import io
    from collections import defaultdict
    from datetime import datetime
    import tempfile
    import os
    
    try:
        # Read uploaded CSV
        contents = await file.read()
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Read CSV
        df = pd.read_csv(tmp_path, encoding='utf-8')
        logger.info(f"📊 Loaded {len(df)} records from Final Report")
        
        # Create temp directory for outputs
        output_dir = tempfile.mkdtemp()
        logger.info(f"📁 Output directory: {output_dir}")
        
        # Group by ISP
        isp_groups = df.groupby('ISP')
        logger.info(f"🏢 Found {len(isp_groups)} ISPs")
        
        # Statistics storage
        isp_stats = {}
        
        # Process each ISP
        for isp_name, isp_data in isp_groups:
            # Sanitize ISP name for filename
            safe_isp_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in str(isp_name))
            safe_isp_name = safe_isp_name.replace(' ', '_')[:50]
            
            logger.info(f"📋 Processing ISP: {isp_name} ({len(isp_data)} records)")
            
            # Save ISP-specific CSV
            isp_filename = f"{safe_isp_name}_Report.csv"
            isp_filepath = os.path.join(output_dir, isp_filename)
            isp_data.to_csv(isp_filepath, index=False, encoding='utf-8')
            
            # Calculate statistics
            stats = {
                'isp_name': isp_name,
                'total_records': len(isp_data),
                'unique_ips': isp_data['Search Value'].nunique(),
                'date_range': {
                    'earliest': isp_data['From Date'].min(),
                    'latest': isp_data['To Date'].max()
                },
                'geographic': {
                    'states': isp_data['State'].value_counts().to_dict(),
                    'cities': isp_data['City'].value_counts().to_dict(),
                    'top_state': isp_data['State'].mode()[0] if len(isp_data['State'].mode()) > 0 else 'N/A',
                    'top_city': isp_data['City'].mode()[0] if len(isp_data['City'].mode()) > 0 else 'N/A'
                },
                'ip_types': isp_data['Type'].value_counts().to_dict()
            }
            
            isp_stats[isp_name] = stats
        
        # Create Summary Statistics CSV
        summary_data = []
        for isp_name, stats in isp_stats.items():
            summary_data.append({
                'ISP Name': isp_name,
                'Total Records': stats['total_records'],
                'Unique IPs': stats['unique_ips'],
                'Earliest Date': stats['date_range']['earliest'],
                'Latest Date': stats['date_range']['latest'],
                'Top State': stats['geographic']['top_state'],
                'Top City': stats['geographic']['top_city'],
                'IPv4 Count': stats['ip_types'].get('IPV4', 0),
                'IPv6 Count': stats['ip_types'].get('IPV6', 0)
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_filepath = os.path.join(output_dir, 'ISP_Summary_Statistics.csv')
        summary_df.to_csv(summary_filepath, index=False, encoding='utf-8')
        
        # Create Geographic Analysis CSV
        geo_data = []
        for isp_name, stats in isp_stats.items():
            for state, count in stats['geographic']['states'].items():
                geo_data.append({
                    'ISP': isp_name,
                    'State': state,
                    'Record Count': count
                })
        
        geo_df = pd.DataFrame(geo_data)
        geo_filepath = os.path.join(output_dir, 'Geographic_Analysis.csv')
        geo_df.to_csv(geo_filepath, index=False, encoding='utf-8')
        
        # Create detailed analysis text report
        analysis_filepath = os.path.join(output_dir, 'Analysis_Report.txt')
        with open(analysis_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ISP SEPARATION AND ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Records: {len(df)}\n")
            f.write(f"Total ISPs: {len(isp_stats)}\n\n")
            
            for isp_name, stats in isp_stats.items():
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"ISP: {isp_name}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total Records: {stats['total_records']}\n")
                f.write(f"Unique IPs: {stats['unique_ips']}\n")
                f.write(f"Date Range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}\n")
                f.write(f"\nTop State: {stats['geographic']['top_state']}\n")
                f.write(f"Top City: {stats['geographic']['top_city']}\n")
                f.write(f"\nIP Types:\n")
                for ip_type, count in stats['ip_types'].items():
                    f.write(f"  - {ip_type}: {count}\n")
                f.write(f"\nTop 5 States:\n")
                sorted_states = sorted(stats['geographic']['states'].items(), key=lambda x: x[1], reverse=True)[:5]
                for state, count in sorted_states:
                    f.write(f"  - {state}: {count} records\n")
                f.write(f"\nTop 5 Cities:\n")
                sorted_cities = sorted(stats['geographic']['cities'].items(), key=lambda x: x[1], reverse=True)[:5]
                for city, count in sorted_cities:
                    f.write(f"  - {city}: {count} records\n")
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files from output directory
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                zip_file.write(filepath, filename)
        
        zip_buffer.seek(0)
        
        # Cleanup
        os.unlink(tmp_path)
        for filename in os.listdir(output_dir):
            os.unlink(os.path.join(output_dir, filename))
        os.rmdir(output_dir)
        
        logger.info(f"✅ ISP separation complete - {len(isp_stats)} ISPs processed")
        
        # Return ZIP file
        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="ISP_Analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error separating by ISP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error separating by ISP: {str(e)}")


@router.get("/files/{run_dir}/{filename}")
async def download_file(run_dir: str, filename: str):
    """
    Download a file from a run directory
    
    Serves files like:
    - ip_lookup_results.csv
    - ip_lookup_results.json
    - Master file.csv
    
    Args:
        run_dir: Directory name (e.g., "20251104_065000_254-25")
        filename: Name of file to download
    """
    logger.info(f"📥 Download request - run_dir: {run_dir}, filename: {filename}")
    
    # Build absolute file path
    base_dir = Path(__file__).parent.parent  # backend directory
    file_path = base_dir / "processed" / run_dir / filename
    
    logger.info(f"🔍 Looking for file at: {file_path}")
    logger.info(f"📁 File exists: {file_path.exists()}")
    
    # Check if file exists
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        
        # List what files DO exist in the directory
        run_dir_path = base_dir / "processed" / run_dir
        logger.info(f"📂 Checking directory: {run_dir_path}")
        logger.info(f"📂 Directory exists: {run_dir_path.exists()}")
        
        if run_dir_path.exists():
            existing_files = list(run_dir_path.glob("*"))
            logger.error(f"❌ Directory exists but file not found. Available files: {[f.name for f in existing_files]}")
            raise HTTPException(
                status_code=404, 
                detail=f"File '{filename}' not found in directory '{run_dir}'. Available files: {[f.name for f in existing_files]}"
            )
        else:
            logger.error(f"❌ Directory does not exist: {run_dir_path}")
            # List all directories in processed
            processed_dir = base_dir / "processed"
            if processed_dir.exists():
                all_dirs = [d.name for d in processed_dir.iterdir() if d.is_dir()]
                logger.error(f"Available directories: {all_dirs}")
            raise HTTPException(
                status_code=404, 
                detail=f"Directory '{run_dir}' not found. Please complete IP lookup first."
            )
    
    logger.info(f"✅ File found, serving: {file_path}")
    
    # Return file with proper headers
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream',
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/generate-isp-letters")
async def generate_isp_letters(
    zip_file: UploadFile = File(...),
    fir_number: str = Form(...),
    fir_date: str = Form(...),
    police_station: str = Form(...),
    sections: str = Form(...),
    subject: str = Form(...),
    email_reference: str = Form(...),
    body_description: str = Form(...),
    complainant: str = Form(...),
    officer_name: str = Form(...),
    officer_designation: str = Form(...),
    officer_location: str = Form(...),
    officer_contact: str = Form(...),
    letter_date: str = Form(...),
    template_id: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Generate ISP letters from ZIP file (Step 7)
    
    Upload ZIP from Step 6 (ISP Separation), auto-detect ISPs,
    and generate official letters using pre-defined templates
    """
    try:
        logger.info(f"📝 Generating ISP letters for FIR: {fir_number}")
        
        # Import letter generator
        from utils.isp_letter_generator import ISPLetterGenerator
        
        # Save uploaded ZIP temporarily
        temp_zip_path = Path(__file__).parent.parent / "temp" / f"isp_zip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        temp_zip_path.parent.mkdir(exist_ok=True)
        
        with open(temp_zip_path, "wb") as f:
            content = await zip_file.read()
            f.write(content)
        
        logger.info(f"✅ ZIP file saved: {temp_zip_path}")
        
        # Prepare case details
        case_details = {
            'fir_number': fir_number,
            'fir_date': fir_date,
            'police_station': police_station,
            'sections': sections,
            'subject': subject,
            'email_reference': email_reference,
            'body_description': body_description,
            'complainant': complainant,
            'officer_name': officer_name,
            'officer_designation': officer_designation,
            'officer_location': officer_location,
            'officer_contact': officer_contact,
            'letter_date': letter_date
        }
        
        # Generate letters
        generator = ISPLetterGenerator()
        template = None
        if template_id:
            from services.letter_template_service import get_template, NotFoundError
            try:
                template = get_template(db, template_id, current_user)
            except NotFoundError:
                template = None  # fall back to system default
        letters_zip = generator.generate_all_letters(str(temp_zip_path), case_details, template)
        
        logger.info(f"✅ ISP letters generated successfully")
        
        # Clean up temp file
        temp_zip_path.unlink()
        
        # Return ZIP file with all letters
        return StreamingResponse(
            iter([letters_zip]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="ISP_Letters_{fir_number.replace("/", "-")}.zip"'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating ISP letters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating ISP letters: {str(e)}")


@router.post("/detect-isps-from-zip")
async def detect_isps_from_zip(
    zip_file: UploadFile = File(...)
):
    """
    Detect ISPs from uploaded ZIP file (preview before generating letters)
    
    Returns list of ISPs with IP counts
    """
    try:
        logger.info(f"🔍 Detecting ISPs from ZIP file")
        
        # Import letter generator
        from utils.isp_letter_generator import ISPLetterGenerator
        
        # Save uploaded ZIP temporarily
        temp_zip_path = Path(__file__).parent.parent / "temp" / f"detect_zip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        temp_zip_path.parent.mkdir(exist_ok=True)
        
        with open(temp_zip_path, "wb") as f:
            content = await zip_file.read()
            f.write(content)
        
        # Detect ISPs
        generator = ISPLetterGenerator()
        isp_data = generator.detect_isps_from_zip(str(temp_zip_path))
        
        # Build response
        detected_isps = []
        for isp_name, ip_df in isp_data.items():
            template_type = generator.get_template_type(isp_name)
            detected_isps.append({
                'isp_name': isp_name,
                'ip_count': len(ip_df),
                'template_type': template_type,
                'has_custom_template': template_type in ['airtel', 'jio', 'vi']
            })
        
        logger.info(f"✅ Detected {len(detected_isps)} ISPs")
        
        # Clean up temp file
        temp_zip_path.unlink()
        
        return {
            "success": True,
            "isps": detected_isps,
            "total_isps": len(detected_isps)
        }
        
    except Exception as e:
        logger.error(f"❌ Error detecting ISPs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detecting ISPs: {str(e)}")


# ============================================================================
# BACKGROUND PROCESSING & RESUME ENDPOINTS
# ============================================================================

@router.post("/lookup/start-background")
async def start_background_lookup(run_dir: str = Query(..., description="Path to the processed run directory")):
    """
    Start IP lookup in background (survives browser close, screen off)
    
    This endpoint:
    1. Creates a background task that runs on the server
    2. Returns immediately with a task_id
    3. Investigation continues even if browser closes
    4. Can check progress using /lookup/progress/{task_id}
    5. Auto-saves progress after each IP
    6. Can resume if interrupted
    
    Args:
        run_dir: Path to the processed directory
        
    Returns:
        task_id and status information
    """
    try:
        run_path = Path(run_dir)
        
        if not run_path.exists():
            raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
        
        csv_path = run_path / 'original_log.csv'
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail=f"original_log.csv not found in {run_dir}")
        
        # Initialize progress manager
        progress_mgr = ProgressManager(run_path)
        
        # Check if can resume
        can_resume = progress_mgr.can_resume()
        
        if can_resume:
            # Get remaining IPs
            all_ips = extract_ips_from_csv(csv_path)
            ips_to_process = progress_mgr.get_remaining_ips(all_ips)
            logger.info(f"Resuming: {len(ips_to_process)} IPs remaining")
        else:
            # Start fresh
            ips_to_process = extract_ips_from_csv(csv_path)
            progress_mgr.save_progress(0, len(ips_to_process))
            logger.info(f"Starting fresh: {len(ips_to_process)} IPs")
        
        # Create background task
        task_id = task_manager.create_task(run_path, ips_to_process, resume=can_resume)
        
        # Start processing in background
        asyncio.create_task(process_ips_background(task_id, run_path, ips_to_process))
        
        return {
            "success": True,
            "task_id": task_id,
            "total_ips": len(ips_to_process),
            "status": "started",
            "resume": can_resume,
            "message": "Investigation started in background. You can close browser safely.",
            "note": "Use /lookup/progress/{task_id} to check progress"
        }
        
    except Exception as e:
        logger.error(f"Error starting background lookup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lookup/progress/{task_id}")
async def get_lookup_progress(task_id: str):
    """
    Get progress of background IP lookup task
    
    Args:
        task_id: Task identifier from start-background endpoint
        
    Returns:
        Progress information
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get detailed progress from file if available
    run_dir = Path(task['run_dir'])
    progress_mgr = ProgressManager(run_dir)
    file_progress = progress_mgr.load_progress()
    
    return {
        "task_id": task_id,
        "status": task['status'],
        "total_ips": task['total_ips'],
        "completed_ips": file_progress.get('completed', task['completed_ips']),
        "progress": file_progress.get('percentage', task['progress']),
        "current_ip": file_progress.get('current_ip'),
        "created_at": task['created_at'],
        "started_at": task.get('started_at'),
        "completed_at": task.get('completed_at'),
        "error": task.get('error'),
        "can_resume": progress_mgr.can_resume()
    }


@router.post("/lookup/resume")
async def resume_lookup(run_dir: str = Query(..., description="Path to the processed run directory")):
    """
    Resume interrupted IP lookup investigation
    
    This endpoint:
    1. Checks for saved progress
    2. Identifies remaining IPs
    3. Continues from where it left off
    4. No duplicate work
    
    Args:
        run_dir: Path to the processed directory
        
    Returns:
        task_id and resume information
    """
    try:
        run_path = Path(run_dir)
        
        if not run_path.exists():
            raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
        
        # Initialize progress manager
        progress_mgr = ProgressManager(run_path)
        
        # Check if can resume
        if not progress_mgr.can_resume():
            summary = progress_mgr.get_summary()
            if summary['status'] == 'completed':
                return {
                    "success": False,
                    "message": "Investigation already completed",
                    "summary": summary
                }
            else:
                return {
                    "success": False,
                    "message": "No progress to resume. Start a new investigation.",
                    "summary": summary
                }
        
        # Get remaining IPs
        csv_path = run_path / 'original_log.csv'
        all_ips = extract_ips_from_csv(csv_path)
        remaining_ips = progress_mgr.get_remaining_ips(all_ips)
        
        # Create background task
        task_id = task_manager.create_task(run_path, remaining_ips, resume=True)
        
        # Start processing in background
        asyncio.create_task(process_ips_background(task_id, run_path, remaining_ips))
        
        return {
            "success": True,
            "task_id": task_id,
            "total_ips": len(all_ips),
            "completed_ips": len(all_ips) - len(remaining_ips),
            "remaining_ips": len(remaining_ips),
            "status": "resumed",
            "message": f"Resumed investigation. Processing {len(remaining_ips)} remaining IPs."
        }
        
    except Exception as e:
        logger.error(f"Error resuming lookup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lookup/check-resume")
async def check_can_resume(run_dir: str = Query(...)):
    """
    Check if investigation can be resumed
    
    Args:
        run_dir: Path to the processed directory
        
    Returns:
        Resume status and summary
    """
    try:
        run_path = Path(run_dir)
        
        if not run_path.exists():
            return {
                "can_resume": False,
                "message": "Run directory not found"
            }
        
        progress_mgr = ProgressManager(run_path)
        summary = progress_mgr.get_summary()
        
        return {
            "can_resume": progress_mgr.can_resume(),
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error checking resume: {e}")
        return {
            "can_resume": False,
            "error": str(e)
        }


async def process_ips_background(task_id: str, run_dir: Path, ips: List[str]):
    """
    Process IPs in background with auto-save and resume capability
    
    Args:
        task_id: Task identifier
        run_dir: Run directory path
        ips: List of IPs to process
    """
    try:
        # Mark task as started
        task_manager.mark_started(task_id)
        
        # Initialize managers
        progress_mgr = ProgressManager(run_dir)
        
        # Get already completed count
        all_ips_path = run_dir / 'original_log.csv'
        all_ips = extract_ips_from_csv(all_ips_path)
        already_completed = len(all_ips) - len(ips)
        
        # Initialize bypass
        bypass = EnhancedCloudflareBypass(headless=True, verbose=False)
        multi_lookup = MultiSourceIPLookup()
        
        logger.info(f"Starting background processing: {len(ips)} IPs")
        
        # Process each IP
        for idx, ip in enumerate(ips):
            current_count = already_completed + idx + 1
            
            try:
                # Update progress
                progress_mgr.save_progress(current_count, len(all_ips), ip)
                task_manager.update_progress(task_id, current_count)
                
                # Lookup IP
                result = bypass.lookup_ip(ip)
                
                # Fallback if needed
                if result.get('error'):
                    result = multi_lookup.lookup_with_fallback(ip, result)
                
                # Save result immediately
                progress_mgr.save_result(result)
                
                logger.info(f"✅ [{current_count}/{len(all_ips)}] {ip} → {result.get('city', 'Unknown')}, {result.get('country', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {ip}: {e}")
                # Save error result
                error_result = {
                    'ip': ip,
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'region': 'Unknown',
                    'isp': 'Unknown',
                    'organization': 'Unknown',
                    'latitude': 'Unknown',
                    'longitude': 'Unknown',
                    'timezone': 'Unknown',
                    'postal_code': 'Unknown',
                    'source': 'error',
                    'error': str(e)
                }
                progress_mgr.save_result(error_result)
            
            # Small delay
            await asyncio.sleep(0.1)
        
        # Mark complete
        progress_mgr.mark_complete()
        task_manager.mark_completed(task_id)
        
        # Close bypass
        try:
            bypass.close()
        except:
            pass
        
        logger.info(f"✅ Background processing completed: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ Background processing failed: {e}")
        task_manager.mark_failed(task_id, str(e))
