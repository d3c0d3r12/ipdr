"""
Background Cookie Refresh Service
Automatically refreshes InfoByIP cookies every 24 hours
Runs in background without user interaction
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class CookieRefreshService:
    """
    Background service that automatically refreshes cookies
    Runs independently without user interaction
    """
    
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.refresh_interval = 24 * 60 * 60  # 24 hours in seconds
        self.last_refresh = None
        self.next_refresh = None
        self.auto_refresh_enabled = True
        self.refresh_count = 0
        self.error_count = 0
        
    def start(self):
        """
        Start the background service
        """
        if self.running:
            logger.warning("Cookie refresh service already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        
        logger.info("🚀 Cookie refresh service started")
        logger.info(f"📅 Auto-refresh interval: {self.refresh_interval / 3600} hours")
    
    def stop(self):
        """
        Stop the background service
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("🛑 Cookie refresh service stopped")
    
    def _run_service(self):
        """
        Main service loop - runs in background thread
        """
        logger.info("🔄 Cookie refresh service loop started")
        
        # Initial refresh on startup
        self._refresh_cookies_sync()
        
        while self.running:
            try:
                # Check if refresh is needed
                if self._should_refresh():
                    logger.info("⏰ Time to refresh cookies...")
                    self._refresh_cookies_sync()
                
                # Sleep for 1 hour, check every hour
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Error in cookie refresh service: {e}")
                self.error_count += 1
                time.sleep(300)  # Wait 5 minutes on error
    
    def _should_refresh(self) -> bool:
        """
        Check if cookies should be refreshed
        """
        if not self.auto_refresh_enabled:
            return False
        
        if self.last_refresh is None:
            return True
        
        time_since_refresh = (datetime.now(timezone.utc) - self.last_refresh).total_seconds()
        return time_since_refresh >= self.refresh_interval
    
    def _refresh_cookies_sync(self):
        """
        Synchronous cookie refresh (runs in background thread)
        """
        try:
            logger.info("🍪 Starting automatic cookie refresh...")
            
            # Import here to avoid circular imports
            from utils.auto_cookie_fetcher import auto_fetcher
            
            # Fetch cookies
            result = auto_fetcher.fetch_cookies(headless=True, max_wait=45)
            
            if result.get('success'):
                self.last_refresh = datetime.now(timezone.utc)
                self.next_refresh = self.last_refresh + timedelta(seconds=self.refresh_interval)
                self.refresh_count += 1
                
                logger.info(f"✅ Cookies refreshed successfully! (Count: {self.refresh_count})")
                logger.info(f"📅 Next refresh: {self.next_refresh.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                # Reload cookies into cookie manager
                try:
                    from utils.infobyip_cookie_manager import cookie_manager
                    cookie_manager.load_cookies()
                    logger.info("✅ Cookies loaded into cookie manager")
                except Exception as e:
                    logger.warning(f"Could not load into cookie manager: {e}")
                
            else:
                logger.error(f"❌ Cookie refresh failed: {result.get('message')}")
                self.error_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error refreshing cookies: {e}")
            self.error_count += 1
    
    async def manual_refresh(self) -> dict:
        """
        Manually trigger cookie refresh (for dashboard button)
        """
        try:
            logger.info("🔄 Manual cookie refresh triggered")
            
            # Import here to avoid circular imports
            from utils.auto_cookie_fetcher import auto_fetcher
            
            # Fetch cookies
            result = auto_fetcher.fetch_cookies(headless=True, max_wait=45)
            
            if result.get('success'):
                self.last_refresh = datetime.now(timezone.utc)
                self.next_refresh = self.last_refresh + timedelta(seconds=self.refresh_interval)
                self.refresh_count += 1
                
                logger.info(f"✅ Manual refresh successful! (Count: {self.refresh_count})")
                
                # Reload cookies into cookie manager
                try:
                    from utils.infobyip_cookie_manager import cookie_manager
                    cookie_manager.load_cookies()
                except Exception as e:
                    logger.warning(f"Could not load into cookie manager: {e}")
                
                return {
                    "success": True,
                    "message": "Cookies refreshed successfully!",
                    "cookie_count": result.get('cookie_count'),
                    "last_refresh": self.last_refresh.isoformat(),
                    "next_refresh": self.next_refresh.isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": result.get('message', 'Refresh failed')
                }
                
        except Exception as e:
            logger.error(f"❌ Manual refresh error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_status(self) -> dict:
        """
        Get current service status
        """
        return {
            "running": self.running,
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "next_refresh": self.next_refresh.isoformat() if self.next_refresh else None,
            "refresh_count": self.refresh_count,
            "error_count": self.error_count,
            "refresh_interval_hours": self.refresh_interval / 3600
        }
    
    def enable_auto_refresh(self):
        """Enable automatic refresh"""
        self.auto_refresh_enabled = True
        logger.info("✅ Auto-refresh enabled")
    
    def disable_auto_refresh(self):
        """Disable automatic refresh"""
        self.auto_refresh_enabled = False
        logger.info("⏸️ Auto-refresh disabled")


# Global service instance
cookie_refresh_service = CookieRefreshService()
