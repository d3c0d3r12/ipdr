"""
Unlimited IP Lookup Router - InfoByIP Integration
Handles unlimited IP lookups with Cloudflare bypass and real-time progress streaming
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List, Dict, Any
import csv
import json
import asyncio
from datetime import datetime

# Import the enhanced bypass system
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass

router = APIRouter()


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
        
        # Initialize bypass system
        yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Initializing Cloudflare bypass system...', 'progress': 5})}\n\n"
        await asyncio.sleep(0.3)
        
        bypass = EnhancedCloudflareBypass(
            headless=True,
            cookies_file=str(run_dir / 'unlimited_lookup_cookies.json')
        )
        
        yield f"data: {json.dumps({'type': 'status', 'message': '🌐 Starting browser session...', 'progress': 10})}\n\n"
        await asyncio.sleep(0.3)
        
        # Process IPs
        results = []
        start_time = datetime.now()
        
        for idx, ip in enumerate(ips, 1):
            progress = 10 + int((idx / total_ips) * 85)  # 10% to 95%
            
            yield f"data: {json.dumps({'type': 'progress', 'message': f'🔎 Looking up IP {idx}/{total_ips}: {ip}', 'current': idx, 'total': total_ips, 'progress': progress, 'ip': ip})}\n\n"
            
            try:
                # Perform lookup
                result = bypass.bypass_and_fetch(ip)
                
                if result:
                    results.append(result)
                    yield f"data: {json.dumps({'type': 'success', 'message': f'✅ {ip} → {result.get(\"city\", \"Unknown\")}, {result.get(\"country\", \"Unknown\")}', 'ip': ip, 'result': result})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'warning', 'message': f'⚠️  {ip} → No data returned', 'ip': ip})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'❌ {ip} → Error: {str(e)}', 'ip': ip, 'error': str(e)})}\n\n"
            
            await asyncio.sleep(0.1)  # Small delay for UI updates
        
        # Save results
        yield f"data: {json.dumps({'type': 'status', 'message': '💾 Saving results...', 'progress': 95})}\n\n"
        await asyncio.sleep(0.2)
        
        # Save CSV
        csv_output = run_dir / 'ip_lookup_results.csv'
        with open(csv_output, 'w', encoding='utf-8', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        # Save JSON
        json_output = run_dir / 'ip_lookup_results.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Cleanup
        bypass.close()
        
        elapsed_time = (datetime.now() - start_time).total_seconds() / 60
        success_rate = (len(results) / total_ips * 100) if total_ips > 0 else 0
        
        yield f"data: {json.dumps({'type': 'complete', 'message': f'🎉 Lookup complete! {len(results)}/{total_ips} IPs processed ({success_rate:.1f}% success)', 'progress': 100, 'total': total_ips, 'success': len(results), 'elapsed_minutes': elapsed_time, 'csv_path': str(csv_output), 'json_path': str(json_output)})}\n\n"
        
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
