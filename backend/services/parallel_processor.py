"""
Parallel Processor - Process Multiple HTML Files Simultaneously
Handles 5 files at once with unique ID extraction and cloud storage
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

from utils.html_processor import HTMLProcessor
from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass
from services.cloud_storage_service import CloudStorageService

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """Process multiple HTML files in parallel"""
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize parallel processor
        
        Args:
            max_workers: Maximum number of files to process simultaneously (default: 5)
        """
        self.max_workers = max_workers
        self.html_processor = HTMLProcessor()
    
    async def process_multiple_files(
        self,
        html_files: List[bytes],
        filenames: List[str],
        fir_number: str,
        user_id: int,
        db
    ) -> Dict:
        """
        Process multiple HTML files in parallel
        
        Args:
            html_files: List of HTML file contents (bytes)
            filenames: List of original filenames
            fir_number: FIR number for grouping
            user_id: User ID
            db: Database session
        
        Returns:
            Dict with processing results
        """
        logger.info(f"🚀 Starting parallel processing of {len(html_files)} files for FIR {fir_number}")
        
        results = {
            'fir_number': fir_number,
            'total_files': len(html_files),
            'processed': 0,
            'failed': 0,
            'investigations': [],
            'errors': []
        }
        
        # Process files in batches of max_workers
        for i in range(0, len(html_files), self.max_workers):
            batch = html_files[i:i + self.max_workers]
            batch_filenames = filenames[i:i + self.max_workers]
            
            logger.info(f"📦 Processing batch {i//self.max_workers + 1}: {len(batch)} files")
            
            # Process batch in parallel
            batch_results = await self._process_batch(
                batch, batch_filenames, fir_number, user_id, db
            )
            
            # Aggregate results
            for result in batch_results:
                if result['success']:
                    results['processed'] += 1
                    results['investigations'].append(result)
                else:
                    results['failed'] += 1
                    results['errors'].append(result)
        
        logger.info(f"✅ Parallel processing complete: {results['processed']}/{results['total_files']} successful")
        
        return results
    
    async def _process_batch(
        self,
        html_files: List[bytes],
        filenames: List[str],
        fir_number: str,
        user_id: int,
        db
    ) -> List[Dict]:
        """Process a batch of files in parallel"""
        
        tasks = []
        for html_content, filename in zip(html_files, filenames):
            task = self._process_single_file(
                html_content, filename, fir_number, user_id, db
            )
            tasks.append(task)
        
        # Run all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'filename': filenames[i],
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_single_file(
        self,
        html_content: bytes,
        filename: str,
        fir_number: str,
        user_id: int,
        db
    ) -> Dict:
        """
        Process a single HTML file
        
        Steps:
        1. Extract unique ID from HTML
        2. Extract IP data from HTML
        3. Create investigation in database
        4. Process IPs
        5. Store results with unique ID
        """
        try:
            logger.info(f"📄 Processing file: {filename}")
            
            # Decode HTML content
            html_str = html_content.decode('utf-8', errors='ignore')
            
            # Step 1: Extract unique ID
            unique_info = self.html_processor.extract_unique_id(html_str, filename)
            unique_id = unique_info['unique_id']
            
            logger.info(f"🔑 Extracted unique ID: {unique_id} (type: {unique_info['type']})")
            
            # Step 2: Extract IP data
            ip_data_list = self.html_processor.extract_ip_data(html_str)
            
            if not ip_data_list:
                logger.warning(f"⚠️  No IP data found in {filename}")
                return {
                    'success': False,
                    'filename': filename,
                    'unique_id': unique_id,
                    'error': 'No IP data found in HTML'
                }
            
            logger.info(f"📊 Found {len(ip_data_list)} IP records in {filename}")
            
            # Step 3: Create investigation
            run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}"
            
            investigation = await CloudStorageService.create_investigation(
                db,
                fir_number=fir_number,
                run_id=run_id,
                user_id=user_id,
                total_ips=len(ip_data_list),
                investigation_name=f"{unique_id} - {filename}",
                description=f"Processed from HTML file: {filename}"
            )
            
            logger.info(f"✅ Created investigation ID: {investigation.id}")
            
            # Step 4: Save original HTML file
            await CloudStorageService.save_file(
                db,
                investigation.id,
                filename,
                html_content,
                'html',
                'text/html',
                f'Original HTML file for {unique_id}'
            )
            
            # Step 5: Process and save IP data
            for ip_record in ip_data_list:
                await CloudStorageService.save_ip_result(
                    db,
                    investigation.id,
                    ip_record
                )
            
            # Step 6: Update progress
            await CloudStorageService.update_progress(
                db,
                investigation.id,
                len(ip_data_list),
                len(ip_data_list)
            )
            
            # Step 7: Generate result filename
            result_filename = self.html_processor.generate_result_filename(unique_id, 'csv')
            
            # Step 8: Generate and save CSV
            csv_bytes = await CloudStorageService.get_ip_results_as_csv(db, investigation.id)
            await CloudStorageService.save_file(
                db,
                investigation.id,
                result_filename,
                csv_bytes,
                'csv',
                'text/csv',
                f'Results CSV for {unique_id}'
            )
            
            logger.info(f"✅ Successfully processed {filename} → {result_filename}")
            
            return {
                'success': True,
                'filename': filename,
                'unique_id': unique_id,
                'investigation_id': investigation.id,
                'run_id': run_id,
                'total_ips': len(ip_data_list),
                'result_filename': result_filename
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'filename': filename,
                'error': str(e)
            }
    
    async def process_with_ip_lookup(
        self,
        html_files: List[bytes],
        filenames: List[str],
        fir_number: str,
        user_id: int,
        db,
        perform_lookup: bool = True
    ) -> Dict:
        """
        Process HTML files and optionally perform IP lookups
        
        Args:
            html_files: List of HTML file contents
            filenames: List of filenames
            fir_number: FIR number
            user_id: User ID
            db: Database session
            perform_lookup: Whether to perform actual IP lookups (default: True)
        """
        logger.info(f"🚀 Processing {len(html_files)} files with IP lookup: {perform_lookup}")
        
        # First, process all HTML files in parallel
        results = await self.process_multiple_files(
            html_files, filenames, fir_number, user_id, db
        )
        
        # If IP lookup is requested, process IPs for each investigation
        if perform_lookup:
            bypass = EnhancedCloudflareBypass(headless=True, verbose=False)
            
            try:
                for investigation_result in results['investigations']:
                    if investigation_result['success']:
                        investigation_id = investigation_result['investigation_id']
                        
                        # Get IP results
                        ip_results = await CloudStorageService.get_ip_results(db, investigation_id)
                        
                        # Perform lookups
                        for ip_result in ip_results:
                            ip_address = ip_result.ip_address
                            
                            # Lookup IP
                            lookup_result = bypass.lookup_ip(ip_address)
                            
                            # Update with lookup data
                            # (Implementation depends on your IP lookup logic)
                            pass
            finally:
                bypass.close()
        
        return results
