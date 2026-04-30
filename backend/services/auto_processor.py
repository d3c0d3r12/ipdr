"""
Auto Processor Service - Automatically Process Steps 2-4
Handles IP lookup, Master file creation, and fully_fixed generation
WITH PARALLEL PROCESSING (40 IPs/second)
"""
import asyncio
import logging
from typing import List, Dict
import pandas as pd
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

from services.cloud_storage_service import CloudStorageService
from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass

logger = logging.getLogger(__name__)


class AutoProcessor:
    """Automatically process investigations through Steps 2-4"""
    
    @staticmethod
    async def process_investigation_steps_2_4(db, investigation_id: int):
        """
        Automatically process Steps 2-4 for an investigation
        
        Step 2: IP Lookup (get country, city, region, ISP)
        Step 3: Create Master File (merge original + lookup)
        Step 4: Create fully_fixed.csv (remove header)
        """
        try:
            logger.info(f"🚀 Starting auto-processing for investigation {investigation_id}")
            
            # Get investigation
            investigation = await CloudStorageService.get_investigation(db, investigation_id)
            if not investigation:
                raise Exception("Investigation not found")
            
            # Step 2: IP Lookup
            logger.info(f"📍 Step 2: Starting IP lookup for {investigation.total_ips} IPs")
            await AutoProcessor._step_2_ip_lookup(db, investigation)
            
            # Step 3: Create Master File
            logger.info(f"📊 Step 3: Creating Master File")
            await AutoProcessor._step_3_master_file(db, investigation)
            
            # Step 4: Create fully_fixed
            logger.info(f"✅ Step 4: Creating fully_fixed.csv")
            await AutoProcessor._step_4_fully_fixed(db, investigation)
            
            # Mark as complete
            investigation.status = 'step_4_complete'
            investigation.current_step = 4
            investigation.completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"✅ Auto-processing complete for investigation {investigation_id}")
            
        except Exception as e:
            logger.error(f"❌ Auto-processing failed for investigation {investigation_id}: {e}")
            import traceback
            traceback.print_exc()
            
            # Update status
            investigation = await CloudStorageService.get_investigation(db, investigation_id)
            if investigation:
                investigation.status = 'failed'
                await db.commit()
            
            raise
    
    @staticmethod
    async def _step_2_ip_lookup(db, investigation):
        """
        Step 2: Lookup all IPs and get location/ISP data
        PARALLEL PROCESSING: 40 IPs at a time for ULTRA SPEED
        """
        try:
            # Get all IP results
            ip_results = await CloudStorageService.get_ip_results(db, investigation.id)
            
            if not ip_results:
                raise Exception("No IP data found")
            
            total_ips = len(ip_results)
            logger.info(f"⚡ Starting PARALLEL processing for {total_ips} IPs (40 at a time)")
            
            # Initialize bypass (single instance, thread-safe)
            bypass = EnhancedCloudflareBypass(headless=True, verbose=False)
            
            try:
                completed = 0
                batch_size = 90  # Process 90 IPs simultaneously
                start_time = time.time()
                
                # Process in batches of 90
                for batch_start in range(0, total_ips, batch_size):
                    batch_end = min(batch_start + batch_size, total_ips)
                    batch = ip_results[batch_start:batch_end]
                    
                    logger.info(f"🚀 Processing batch {batch_start//batch_size + 1}: IPs {batch_start+1}-{batch_end}")
                    
                    # Create thread pool for this batch
                    with ThreadPoolExecutor(max_workers=batch_size) as executor:
                        # Submit all IPs in batch to thread pool
                        loop = asyncio.get_event_loop()
                        tasks = [
                            loop.run_in_executor(
                                executor,
                                AutoProcessor._lookup_single_ip,
                                bypass,
                                ip_result
                            )
                            for ip_result in batch
                        ]
                        
                        # Wait for all IPs in batch to complete
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Update completed count
                        completed += len(batch)
                        
                        # Update progress
                        investigation.completed_ips = completed
                        investigation.progress_percentage = round((completed / total_ips * 100), 2)
                        await db.commit()
                        
                        # Calculate speed
                        elapsed = time.time() - start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        logger.info(f"✅ Batch complete: {completed}/{total_ips} IPs ({speed:.1f} IPs/sec)")
                
                # Final commit
                await db.commit()
                
                # Calculate final stats
                total_time = time.time() - start_time
                avg_speed = total_ips / total_time if total_time > 0 else 0
                logger.info(f"🎉 PARALLEL PROCESSING COMPLETE!")
                logger.info(f"   Total IPs: {total_ips}")
                logger.info(f"   Total Time: {total_time:.1f} seconds")
                logger.info(f"   Average Speed: {avg_speed:.1f} IPs/second")
                
                # Save ip_lookup_results.csv
                await AutoProcessor._save_ip_lookup_csv(db, investigation)
                
                # Update step
                investigation.status = 'step_2_complete'
                investigation.current_step = 2
                await db.commit()
                
                logger.info(f"✅ Step 2 complete: {completed}/{total_ips} IPs processed")
                
            finally:
                bypass.close()
                
        except Exception as e:
            logger.error(f"❌ Step 2 failed: {e}")
            raise
    
    @staticmethod
    def _lookup_single_ip(bypass, ip_result):
        """
        Lookup single IP (runs in thread pool)
        This function is synchronous and thread-safe
        """
        try:
            logger.info(f"  🔍 Looking up: {ip_result.ip_address}")
            lookup_data = bypass.lookup_ip(ip_result.ip_address)
            
            if lookup_data and lookup_data.get('success'):
                # Update IP result with lookup data
                ip_result.country = lookup_data.get('country', 'Unknown')
                ip_result.region = lookup_data.get('region', 'Unknown')
                ip_result.city = lookup_data.get('city', 'Unknown')
                ip_result.isp = lookup_data.get('isp', 'Unknown')
                ip_result.postal_code = lookup_data.get('postal_code')
                ip_result.latitude = lookup_data.get('latitude')
                ip_result.longitude = lookup_data.get('longitude')
                ip_result.timezone = lookup_data.get('timezone')
                ip_result.lookup_source = 'infobyip'
                logger.info(f"  ✅ {ip_result.ip_address}: {ip_result.city}, {ip_result.country}")
            else:
                # Mark as failed but continue
                ip_result.country = 'Unknown'
                ip_result.region = 'Unknown'
                ip_result.city = 'Unknown'
                ip_result.isp = 'Unknown'
                logger.warning(f"  ⚠️ {ip_result.ip_address}: Lookup failed")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Error looking up {ip_result.ip_address}: {e}")
            # Mark as Unknown but don't fail
            ip_result.country = 'Unknown'
            ip_result.region = 'Unknown'
            ip_result.city = 'Unknown'
            ip_result.isp = 'Unknown'
            return False
    
    @staticmethod
    async def _save_ip_lookup_csv(db, investigation):
        """Save IP lookup results as CSV"""
        try:
            # Get all IP results
            ip_results = await CloudStorageService.get_ip_results(db, investigation.id)
            
            # Create DataFrame
            data = []
            for ip_result in ip_results:
                data.append({
                    'ip': ip_result.ip_address,
                    'country': ip_result.country or 'Unknown',
                    'region': ip_result.region or 'Unknown',
                    'city': ip_result.city or 'Unknown',
                    'isp': ip_result.isp or 'Unknown',
                    'postal_code': ip_result.postal_code or '',
                    'latitude': ip_result.latitude or '',
                    'longitude': ip_result.longitude or '',
                    'timezone': ip_result.timezone or ''
                })
            
            df = pd.DataFrame(data)
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            
            # Save to database
            await CloudStorageService.save_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_ip_lookup_results.csv",
                csv_bytes,
                'csv',
                'text/csv',
                'Step 2: IP lookup results'
            )
            
        except Exception as e:
            logger.error(f"Error saving IP lookup CSV: {e}")
            raise
    
    @staticmethod
    async def _step_3_master_file(db, investigation):
        """Step 3: Create Master File by merging original_log + ip_lookup_results"""
        try:
            # Get original_log file
            original_log_file = await CloudStorageService.get_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_original_log.csv"
            )
            
            if not original_log_file:
                raise Exception("original_log.csv not found")
            
            # Get ip_lookup_results file
            lookup_file = await CloudStorageService.get_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_ip_lookup_results.csv"
            )
            
            if not lookup_file:
                raise Exception("ip_lookup_results.csv not found")
            
            # Load DataFrames
            original_df = pd.read_csv(io.BytesIO(original_log_file.file_data))
            lookup_df = pd.read_csv(io.BytesIO(lookup_file.file_data))
            
            # Merge on 'ip' column (LEFT JOIN)
            master_df = original_df.merge(
                lookup_df[['ip', 'country', 'city', 'region', 'isp']],
                on='ip',
                how='left'
            )
            
            # Fill missing values
            master_df.fillna('Unknown', inplace=True)
            
            # Ensure column order: timestamp, ip, country, city, region, isp
            master_df = master_df[['timestamp', 'ip', 'country', 'city', 'region', 'isp']]
            
            # Save Master file.csv (WITH header)
            master_csv = master_df.to_csv(index=False).encode('utf-8')
            
            await CloudStorageService.save_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_Master_file.csv",
                master_csv,
                'csv',
                'text/csv',
                'Step 3: Master file with all data'
            )
            
            # Update step
            investigation.status = 'step_3_complete'
            investigation.current_step = 3
            await db.commit()
            
            logger.info(f"✅ Step 3 complete: Master file created")
            
        except Exception as e:
            logger.error(f"❌ Step 3 failed: {e}")
            raise
    
    @staticmethod
    async def _step_4_fully_fixed(db, investigation):
        """Step 4: Create fully_fixed.csv (same as Master file but NO header)"""
        try:
            # Get Master file
            master_file = await CloudStorageService.get_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_Master_file.csv"
            )
            
            if not master_file:
                raise Exception("Master_file.csv not found")
            
            # Load DataFrame
            master_df = pd.read_csv(io.BytesIO(master_file.file_data))
            
            # Save fully_fixed.csv (WITHOUT header)
            fully_fixed_csv = master_df.to_csv(index=False, header=False).encode('utf-8')
            
            await CloudStorageService.save_file(
                db,
                investigation.id,
                f"{investigation.investigation_name}_fully_fixed.csv",
                fully_fixed_csv,
                'csv',
                'text/csv',
                'Step 4: Fully fixed file (no header) - ready for Step 5'
            )
            
            # Update step
            investigation.status = 'step_4_complete'
            investigation.current_step = 4
            await db.commit()
            
            logger.info(f"✅ Step 4 complete: fully_fixed.csv created")
            
        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}")
            raise


async def start_auto_processing(investigation_id: int):
    """
    Start auto-processing in background
    This should be called after investigation is created
    Creates its own database session
    """
    from database import AsyncSessionLocal
    
    try:
        # Create new database session for background task
        async with AsyncSessionLocal() as db:
            await AutoProcessor.process_investigation_steps_2_4(db, investigation_id)
    except Exception as e:
        logger.error(f"Auto-processing failed: {e}")
