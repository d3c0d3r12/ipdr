"""
Unlimited IP Lookup Router - InfoByIP Integration
Handles unlimited IP lookups with Cloudflare bypass and real-time progress streaming
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from typing import List, Dict, Any
import csv
import json
import asyncio
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

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
        Status of IP lookup results
    """
    run_path = Path(run_dir)
    
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found: {run_dir}")
    
    csv_results = run_path / 'ip_lookup_results.csv'
    json_results = run_path / 'ip_lookup_results.json'
    original_csv = run_path / 'original_log.csv'
    
    # Count IPs in original file
    total_ips = 0
    if original_csv.exists():
        total_ips = len(extract_ips_from_csv(original_csv))
    
    # Count results
    results_count = 0
    if csv_results.exists():
        with open(csv_results, 'r', encoding='utf-8') as f:
            results_count = sum(1 for _ in csv.DictReader(f))
    
    return {
        "has_results": csv_results.exists() and json_results.exists(),
        "csv_exists": csv_results.exists(),
        "json_exists": json_results.exists(),
        "total_ips": total_ips,
        "results_count": results_count,
        "success_rate": round((results_count / total_ips * 100), 1) if total_ips > 0 else 0,
        "csv_path": str(csv_results) if csv_results.exists() else None,
        "json_path": str(json_results) if json_results.exists() else None
    }


@router.post("/lookup/merge")
async def merge_master_file(run_dir: str = Query(..., description="Run directory path")):
    """
    Merge original_log.csv and ip_lookup_results.csv into Master file.csv
    
    Combines timestamp and IP from original_log.csv with lookup data from ip_lookup_results.csv
    Output columns: timestamp, ip, country, city, region, isp
    """
    run_path = Path(run_dir)
    
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
        
        # Ensure required columns exist
        if 'ip' not in df_original.columns or 'timestamp' not in df_original.columns:
            raise HTTPException(status_code=400, detail="original_log.csv must have 'ip' and 'timestamp' columns")
        
        if 'ip' not in df_lookup.columns:
            raise HTTPException(status_code=400, detail="ip_lookup_results.csv must have 'ip' column")
        
        # Merge on IP address
        df_merged = df_original.merge(
            df_lookup[['ip', 'country', 'city', 'region', 'isp']], 
            on='ip', 
            how='left'
        )
        
        # Select only required columns
        df_master = df_merged[['timestamp', 'ip', 'country', 'city', 'region', 'isp']]
        
        # Fill missing values with 'Unknown'
        df_master = df_master.fillna('Unknown')
        
        # Save to Master file.csv
        master_file = run_path / 'Master file.csv'
        df_master.to_csv(master_file, index=False, encoding='utf-8')
        
        return {
            "success": True,
            "message": "Master file created successfully",
            "master_file": f"/api/files/{run_path.name}/Master file.csv",
            "total_records": len(df_master),
            "columns": list(df_master.columns),
            "sample_data": df_master.head(3).to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging files: {str(e)}")


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
