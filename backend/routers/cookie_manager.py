"""
Cookie Management API - Upload and manage InfoByIP cookies
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import logging

# Import cookie manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.infobyip_cookie_manager import cookie_manager

# Import auto fetcher
try:
    from utils.auto_cookie_fetcher import auto_fetcher
    AUTO_FETCH_AVAILABLE = True
except Exception as e:
    logger.warning(f"Auto cookie fetcher not available: {e}")
    AUTO_FETCH_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_cookie_status():
    """
    Get current cookie status
    
    Returns status of loaded cookies including:
    - Whether cookies are loaded
    - Whether cookies are valid
    - Expiry time
    - Whether refresh is needed
    """
    try:
        status = cookie_manager.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting cookie status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_cookies(file: UploadFile = File(...)):
    """
    Upload cookies file (JSON format from EditThisCookie or manual export)
    
    Accepts:
    - EditThisCookie format (array of cookie objects)
    - Simple key-value format (object with cookie names/values)
    """
    try:
        # Read uploaded file
        content = await file.read()
        cookies = json.loads(content)
        
        logger.info(f"Received cookie upload: {len(cookies) if isinstance(cookies, list) else len(cookies.keys())} cookies")
        
        # Save cookies
        success = cookie_manager.save_cookies(cookies)
        
        if success:
            status = cookie_manager.get_status()
            return JSONResponse(content={
                "success": True,
                "message": "Cookies uploaded and validated successfully",
                "status": status
            })
        else:
            raise HTTPException(
                status_code=400,
                detail="Cookies uploaded but validation failed. Please check cookies and try again."
            )
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format. Please upload a valid cookie JSON file."
        )
    except Exception as e:
        logger.error(f"Error uploading cookies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_cookies():
    """
    Validate current cookies by making a test request to InfoByIP
    
    Returns whether cookies are still valid
    """
    try:
        is_valid = cookie_manager.refresh_validation()
        status = cookie_manager.get_status()
        
        return JSONResponse(content={
            "valid": is_valid,
            "status": status,
            "message": "Cookies are valid" if is_valid else "Cookies are invalid or expired"
        })
    except Exception as e:
        logger.error(f"Error validating cookies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instructions")
async def get_instructions():
    """
    Get instructions for exporting and uploading cookies
    """
    instructions = {
        "title": "How to Export and Upload Cookies",
        "steps": [
            {
                "step": 1,
                "title": "Install EditThisCookie Extension",
                "description": "Install 'EditThisCookie' extension for Chrome",
                "url": "https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg"
            },
            {
                "step": 2,
                "title": "Visit InfoByIP",
                "description": "Go to https://www.infobyip.com/ip-8.8.8.8.html",
                "action": "Solve the Cloudflare captcha if prompted"
            },
            {
                "step": 3,
                "title": "Export Cookies",
                "description": "Click the EditThisCookie icon in Chrome toolbar",
                "action": "Click the 'Export' button (download icon)"
            },
            {
                "step": 4,
                "title": "Save Cookie File",
                "description": "Cookies are copied to clipboard",
                "action": "Paste into a text file and save as 'infobyip_cookies.json'"
            },
            {
                "step": 5,
                "title": "Upload to System",
                "description": "Use the upload button in the UI",
                "action": "Select your saved cookie file and upload"
            }
        ],
        "alternative_method": {
            "title": "Manual Cookie Export (Without Extension)",
            "steps": [
                "Open Chrome DevTools (F12)",
                "Go to Application tab",
                "Click 'Cookies' in left sidebar",
                "Select 'https://www.infobyip.com'",
                "Copy all cookie names and values",
                "Create JSON file with format: {\"cookie_name\": \"cookie_value\", ...}",
                "Upload the JSON file"
            ]
        },
        "cookie_lifetime": "Cookies typically last 24 hours",
        "refresh_frequency": "Refresh cookies once per day for best results"
    }
    
    return JSONResponse(content=instructions)


@router.delete("/clear")
async def clear_cookies():
    """
    Clear all loaded cookies (useful for troubleshooting)
    """
    try:
        cookie_manager.session.cookies.clear()
        cookie_manager.cookies_loaded = False
        cookie_manager.cookies_valid = False
        
        logger.info("Cookies cleared")
        
        return JSONResponse(content={
            "success": True,
            "message": "Cookies cleared successfully"
        })
    except Exception as e:
        logger.error(f"Error clearing cookies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-fetch")
async def auto_fetch_cookies(headless: bool = True):
    """
    Automatically fetch cookies from InfoByIP using headless browser
    
    This will:
    1. Launch a headless Chrome browser
    2. Visit InfoByIP.com
    3. Wait for Cloudflare challenge to complete
    4. Extract cookies
    5. Save and load them into the system
    
    Args:
        headless: Run browser in headless mode (default: True)
    
    Returns:
        Success status and cookie information
    """
    if not AUTO_FETCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Auto-fetch feature not available. Selenium may not be installed."
        )
    
    try:
        logger.info("🚀 Starting automatic cookie fetch...")
        
        # Fetch cookies
        result = auto_fetcher.fetch_cookies(headless=headless, max_wait=30)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Failed to fetch cookies')
            )
        
        # Reload cookies into cookie manager
        cookie_manager.load_cookies()
        
        # Get updated status
        status = cookie_manager.get_status()
        
        return JSONResponse(content={
            "success": True,
            "message": result.get('message'),
            "cookie_count": result.get('cookie_count'),
            "has_cf_clearance": result.get('has_cf_clearance'),
            "status": status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto-fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service/status")
async def get_service_status():
    """
    Get background cookie refresh service status
    
    Returns information about:
    - Service running status
    - Last refresh time
    - Next refresh time
    - Refresh count
    - Error count
    """
    try:
        from services.cookie_refresh_service import cookie_refresh_service
        status = cookie_refresh_service.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/refresh")
async def manual_service_refresh():
    """
    Manually trigger background service to refresh cookies
    
    This is for the dashboard button - triggers immediate refresh
    """
    try:
        from services.cookie_refresh_service import cookie_refresh_service
        result = await cookie_refresh_service.manual_refresh()
        
        if result.get('success'):
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=result.get('message'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/enable")
async def enable_auto_refresh():
    """
    Enable automatic cookie refresh
    """
    try:
        from services.cookie_refresh_service import cookie_refresh_service
        cookie_refresh_service.enable_auto_refresh()
        return JSONResponse(content={
            "success": True,
            "message": "Auto-refresh enabled"
        })
    except Exception as e:
        logger.error(f"Error enabling auto-refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service/disable")
async def disable_auto_refresh():
    """
    Disable automatic cookie refresh
    """
    try:
        from services.cookie_refresh_service import cookie_refresh_service
        cookie_refresh_service.disable_auto_refresh()
        return JSONResponse(content={
            "success": True,
            "message": "Auto-refresh disabled"
        })
    except Exception as e:
        logger.error(f"Error disabling auto-refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))
