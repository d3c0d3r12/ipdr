"""
HTML Processor - Extract Unique IDs and Process Multiple Files
Handles parallel processing of HTML files with unique identifier extraction
"""
from bs4 import BeautifulSoup
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class HTMLProcessor:
    """Process HTML files and extract unique identifiers"""
    
    @staticmethod
    def extract_unique_id(html_content: str, filename: str = None) -> Dict[str, str]:
        """
        Extract unique identifier from HTML file
        Looks for: email, subscriber ID, username, etc.
        
        Returns:
            Dict with 'unique_id', 'type', and 'original_filename'
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to extract email
            email = HTMLProcessor._extract_email(soup, html_content)
            if email:
                return {
                    'unique_id': email.split('@')[0],  # Use part before @
                    'full_identifier': email,
                    'type': 'email',
                    'original_filename': filename or 'unknown'
                }
            
            # Try to extract subscriber ID
            subscriber_id = HTMLProcessor._extract_subscriber_id(soup, html_content)
            if subscriber_id:
                return {
                    'unique_id': subscriber_id,
                    'full_identifier': subscriber_id,
                    'type': 'subscriber_id',
                    'original_filename': filename or 'unknown'
                }
            
            # Try to extract from filename
            if filename:
                # Extract from filename like "bharatkumarumma.SubscriberInfo.html"
                name_match = re.match(r'([^.]+)', filename)
                if name_match:
                    return {
                        'unique_id': name_match.group(1),
                        'full_identifier': name_match.group(1),
                        'type': 'filename',
                        'original_filename': filename
                    }
            
            # Fallback: generate from content hash
            import hashlib
            content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
            return {
                'unique_id': f'unknown_{content_hash}',
                'full_identifier': content_hash,
                'type': 'hash',
                'original_filename': filename or 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Error extracting unique ID: {e}")
            return {
                'unique_id': 'error',
                'full_identifier': 'error',
                'type': 'error',
                'original_filename': filename or 'unknown'
            }
    
    @staticmethod
    def _extract_email(soup: BeautifulSoup, html_content: str) -> Optional[str]:
        """Extract email from HTML"""
        # Pattern 1: Look for email in text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html_content)
        if emails:
            return emails[0]
        
        # Pattern 2: Look in specific tags
        for tag in soup.find_all(['input', 'span', 'div', 'td', 'p']):
            text = tag.get_text()
            if '@' in text:
                emails = re.findall(email_pattern, text)
                if emails:
                    return emails[0]
        
        return None
    
    @staticmethod
    def _extract_subscriber_id(soup: BeautifulSoup, html_content: str) -> Optional[str]:
        """Extract subscriber ID from HTML"""
        # Pattern 1: Look for "Subscriber ID", "User ID", etc.
        patterns = [
            r'Subscriber\s*ID[:\s]+([A-Za-z0-9_-]+)',
            r'User\s*ID[:\s]+([A-Za-z0-9_-]+)',
            r'Account[:\s]+([A-Za-z0-9_-]+)',
            r'ID[:\s]+([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Pattern 2: Look in table cells
        for tag in soup.find_all(['td', 'span', 'div']):
            text = tag.get_text().strip()
            if 'subscriber' in text.lower() or 'user' in text.lower():
                # Get next sibling or parent
                next_tag = tag.find_next_sibling()
                if next_tag:
                    value = next_tag.get_text().strip()
                    if value and len(value) < 50:
                        return value
        
        return None
    
    @staticmethod
    def extract_ip_data(html_content: str) -> List[Dict]:
        """
        Extract IP data from HTML file
        Looks for tables with IP information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            ip_data = []
            
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Try to find header row
                headers = []
                data_rows = rows
                
                if rows and rows[0].find_all('th'):
                    headers = [th.get_text().strip() for th in rows[0].find_all('th')]
                    data_rows = rows[1:]
                
                # Extract data
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        row_data = {}
                        for i, cell in enumerate(cells):
                            key = headers[i] if i < len(headers) else f'column_{i}'
                            row_data[key] = cell.get_text().strip()
                        
                        # Check if this row contains IP data
                        row_text = ' '.join(row_data.values()).lower()
                        if any(keyword in row_text for keyword in ['ip', 'address', 'timestamp', 'date', 'time']):
                            ip_data.append(row_data)
            
            return ip_data
            
        except Exception as e:
            logger.error(f"Error extracting IP data: {e}")
            return []
    
    @staticmethod
    def generate_result_filename(unique_id: str, file_type: str = 'csv') -> str:
        """
        Generate result filename using unique ID
        
        Args:
            unique_id: Unique identifier extracted from HTML
            file_type: File extension (csv, json, etc.)
        
        Returns:
            Filename like "bharatkumarumma_results.csv"
        """
        # Sanitize unique_id
        safe_id = re.sub(r'[^\w\-]', '_', unique_id)
        return f"{safe_id}_results.{file_type}"
