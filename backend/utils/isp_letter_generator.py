"""
ISP Letter Generator Utility
Generates official letters to ISPs based on pre-defined templates
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime, timedelta
import os
import zipfile
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import io

class ISPLetterGenerator:
    """Generate ISP letters with pre-defined templates"""
    
    # ISP Template Mappings
    ISP_TEMPLATES = {
        'airtel': 'airtel',
        'jio': 'jio',
        'reliance': 'jio',
        'reliance jio': 'jio',
        'vi': 'vi',
        'vodafone': 'vi',
        'vodafone idea': 'vi',
        'idea': 'vi',
        'bsnl': 'default',
        'mtnl': 'default',
    }
    
    # Month mapping for Airtel (numeric to 3-letter)
    MONTH_MAP = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
    }
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates" / "isp_letters"
    
    def convert_date_to_airtel_format(self, date_str: str) -> str:
        """
        Convert ANY date format to Airtel format: DD-MMM-YYYY
        Handles: DD-MM-YYYY, YYYY-MM-DD, DD:MM:YYYY, DD.MM.YYYY, YYYYMMDD, DD/MM/YYYY
        Output: 28-Jan-2025 (always with 3-letter month)
        """
        try:
            # Remove any existing formatting
            date_clean = date_str.replace(':', '-').replace('/', '-').replace('.', '-').strip()
            
            # Handle YYYYMMDD format (8 digits, no separators)
            if len(date_clean) == 8 and date_clean.isdigit():
                year = date_clean[:4]
                month = date_clean[4:6]
                day = date_clean[6:8]
            # Handle YYYY-MM-DD format
            elif len(date_clean.split('-')[0]) == 4:
                parts = date_clean.split('-')
                year, month, day = parts[0], parts[1], parts[2]
            # Handle DD-MM-YYYY format
            else:
                parts = date_clean.split('-')
                day, month, year = parts[0], parts[1], parts[2]
            
            # Ensure month is zero-padded for lookup
            month = month.zfill(2)
            day = day.zfill(2)
            
            # Convert month to 3-letter format
            month_abbr = self.MONTH_MAP.get(month, month)
            
            return f"{day}-{month_abbr}-{year}"
        except Exception as e:
            # If all parsing fails, return original
            return date_str
    
    def pad_time_to_6_digits(self, time_str: str) -> str:
        """
        Pad time to 6 digits for Jio
        Input: 12532 or 1532 or 532
        Output: 012532 or 001532 or 000532
        """
        try:
            # Remove any colons or spaces
            time_clean = time_str.replace(':', '').replace(' ', '').strip()
            
            # Pad to 6 digits
            time_padded = time_clean.zfill(6)
            
            return time_padded
        except:
            return time_str
        
    def detect_isps_from_zip(self, zip_file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Extract ISP data from ZIP file (from Step 6)
        
        Returns:
            Dict with ISP name as key and DataFrame as value
        """
        isp_data = {}
        
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # List all CSV files in ZIP
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                
                for csv_file in csv_files:
                    # Extract ISP name from filename
                    # e.g., "Airtel_Report.csv" -> "Airtel"
                    # e.g., "Reliance_Jio_Report.csv" -> "Reliance Jio"
                    filename = os.path.splitext(os.path.basename(csv_file))[0]
                    
                    # Remove "_Report" suffix if present
                    if filename.endswith('_Report'):
                        isp_name = filename[:-7]  # Remove last 7 characters "_Report"
                    else:
                        isp_name = filename
                    
                    # Replace underscores with spaces for display
                    isp_name = isp_name.replace('_', ' ')
                    
                    # Read CSV data
                    with zip_ref.open(csv_file) as f:
                        df = pd.read_csv(f)
                        
                        # Skip if empty
                        if len(df) == 0:
                            continue
                        
                        isp_data[isp_name] = df
                        
        except Exception as e:
            raise Exception(f"Error reading ZIP file: {str(e)}")
        
        return isp_data
    
    def get_template_type(self, isp_name: str) -> str:
        """
        Get template type for ISP
        
        Returns:
            'airtel', 'jio', 'vi', or 'default'
        """
        isp_lower = isp_name.lower().strip()
        
        # Check for exact match first
        if isp_lower in self.ISP_TEMPLATES:
            return self.ISP_TEMPLATES[isp_lower]
        
        # Check for partial matches (more flexible)
        if 'airtel' in isp_lower or 'bharti' in isp_lower:
            return 'airtel'
        if 'jio' in isp_lower or 'reliance' in isp_lower:
            return 'jio'
        if 'vi' in isp_lower or 'vodafone' in isp_lower or 'idea' in isp_lower:
            return 'vi'
        
        return 'default'
    
    def format_timestamp_for_airtel(self, timestamp_str: str) -> Dict[str, str]:
        """
        Format timestamp for Airtel
        Format: DD-MMM-YYYY HH24:MI:SS (combined in one column)
        Month in 3-letter format (Jan, Feb, Mar, etc.)
        
        Returns:
            {'from_datetime': '28-Jan-2025 14:30:25', 'to_datetime': '28-Jan-2025 15:30:25'}
        """
        try:
            # Parse timestamp
            dt = pd.to_datetime(timestamp_str)
            
            # From datetime with 3-letter month
            from_dt = dt.strftime('%d-%b-%Y %H:%M:%S')
            
            # To datetime (from + 1 hour) with 3-letter month
            to_dt = (dt + timedelta(hours=1)).strftime('%d-%b-%Y %H:%M:%S')
            
            return {
                'from_datetime': from_dt,
                'to_datetime': to_dt
            }
        except:
            return {
                'from_datetime': 'N/A',
                'to_datetime': 'N/A'
            }
    
    def format_timestamp_for_vi(self, timestamp_str: str) -> Dict[str, str]:
        """
        Format timestamp for VI (Vodafone Idea)
        Format: DD:MM:YYYY and HH:MM:SS (IST) (separate columns)
        
        Returns:
            {'from_date': '28:01:2025', 'from_time': '14:30:25', 'to_date': '28:01:2025', 'to_time': '15:30:25'}
        """
        try:
            dt = pd.to_datetime(timestamp_str)
            
            # From date and time
            from_date = dt.strftime('%d:%m:%Y')
            from_time = dt.strftime('%H:%M:%S')
            
            # To date and time (from + 1 hour)
            to_dt = dt + timedelta(hours=1)
            to_date = to_dt.strftime('%d:%m:%Y')
            to_time = to_dt.strftime('%H:%M:%S')
            
            return {
                'from_date': from_date,
                'from_time': from_time,
                'to_date': to_date,
                'to_time': to_time
            }
        except:
            return {
                'from_date': 'N/A',
                'from_time': 'N/A',
                'to_date': 'N/A',
                'to_time': 'N/A'
            }
    
    def format_timestamp_for_jio(self, timestamp_str: str) -> Dict[str, str]:
        """
        Format timestamp for Jio
        Format: YYYYMMDD and HHMMSS (IST) (separate columns)
        Time must be 6 digits (padded with leading zeros)
        
        Returns:
            {'from_date': '20250128', 'from_time': '143025', 'to_date': '20250128', 'to_time': '153025'}
        """
        try:
            dt = pd.to_datetime(timestamp_str)
            
            # From date and time (time padded to 6 digits)
            from_date = dt.strftime('%Y%m%d')
            from_time = dt.strftime('%H%M%S')  # Always 6 digits
            
            # To date and time (from + 1 hour)
            to_dt = dt + timedelta(hours=1)
            to_date = to_dt.strftime('%Y%m%d')
            to_time = to_dt.strftime('%H%M%S')  # Always 6 digits
            
            return {
                'from_date': from_date,
                'from_time': from_time,
                'to_date': to_date,
                'to_time': to_time
            }
        except:
            return {
                'from_date': 'N/A',
                'from_time': 'N/A',
                'to_date': 'N/A',
                'to_time': 'N/A'
            }
    
    def create_letter_airtel(self, isp_name: str, ip_data: pd.DataFrame, case_details: Dict) -> Document:
        """Create letter for Airtel with 4-column format"""
        doc = Document()
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        # Header - Legal notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Seeking data under the statutory provisions contained in Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023 or Section 5(2) of the Indian Telegraph Act, 1885 read with Rule 419A of the Indian Telegraph (Amendment) Rules, 2007.")
        run.font.size = Pt(10)
        run.font.italic = True
        
        # Office header
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("OFFICE OF THE CYBER CRIME UNIT, IFSO, SPECIAL CELL, DELHI POLICE,\n")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run("SEC - 16C, DWARKA, NEW DELHI - 110078\n")
        run.font.size = Pt(10)
        run = p.add_run("Contact No. 011-20892632, E-Mail ID : acp-cybercell1@delhipolice.gov.in")
        run.font.size = Pt(9)
        
        # Notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Notice u/s 94 BNSS, 2023")
        run.bold = True
        run.font.size = Pt(11)
        
        doc.add_paragraph()  # Blank line
        
        # To address
        p = doc.add_paragraph("To,")
        p = doc.add_paragraph(f"     \t     The Nodal Officer")
        p = doc.add_paragraph(f"        \t     {isp_name}")
        
        # Subject (with custom subject and email reference)
        subject_text = case_details.get('subject', 'Reg provide information in case')
        email_ref = case_details.get('email_reference', 'N/A')
        subject = f"Subject:- {subject_text} FIR No. {case_details.get('fir_number', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')} ({email_ref})"
        p = doc.add_paragraph(subject)
        p.runs[0].bold = True
        
        # Body (use full body description from user)
        p = doc.add_paragraph("Sir,")
        body_text = case_details.get('body_description', '')
        if not body_text:
            # Fallback to default format if not provided
            body_text = f"It is submitted that case FIR No.{case_details.get('fir_number', 'N/A')}, U/s {case_details.get('sections', 'N/A')}, Dated {case_details.get('fir_date', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')}, Delhi has been registered on the complaint of {case_details.get('complainant', 'N/A')} at IFSO/CCU/Spl. Cell, New Delhi."
        doc.add_paragraph("                " + body_text + " During investigation the following IP details/numbers have emerged as suspect.")
        
        # Requests
        doc.add_paragraph("You are hereby requested to provide the following information/documents:-")
        doc.add_paragraph("1. Details of the user (Name, Address, Contact No. etc.) to whom below IP's were allotted at the mentioned Date & time against each.")
        doc.add_paragraph("2. Kindly provide the ownership of the users, to whom IP was allotted.")
        doc.add_paragraph("3. Kindly preserve the record till further directions.")
        doc.add_paragraph("4. Kindly provide any other useful details.")
        doc.add_paragraph()  # Blank line
        doc.add_paragraph("The above-mentioned information is urgent and a prompt reply is anticipated.")
        
        doc.add_paragraph()  # Blank line
        
        # IP Table - Airtel Format (4 columns)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Type'
        hdr_cells[1].text = 'Search Value'
        hdr_cells[2].text = 'From Date\n(DD-MMM-YYYY)\n(HH24:MI:SS)'
        hdr_cells[3].text = 'To Date\n(DD-MMM-YYYY)\n(HH24:MI:SS)'
        
        # Make header bold
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(9)
        
        # Add IP data rows
        for idx, row in ip_data.iterrows():
            row_cells = table.add_row().cells
            
            # Get IP address (handle both column names)
            ip_address = str(row.get('Search Value', row.get('ip', '')))
            
            # Get IP type (use existing Type column or determine from IP)
            ip_type = str(row.get('Type', ''))
            if not ip_type or ip_type == 'nan':
                ip_type = 'IPV6' if ':' in ip_address else 'IPV4'
            
            # Get timestamp (handle both column names)
            # For separated files, use From Date + From Time
            from_date = str(row.get('From Date', ''))
            from_time = str(row.get('From Time', ''))
            
            if from_date and from_date != 'nan':
                # Convert date to Airtel format (DD-MMM-YYYY)
                from_date_airtel = self.convert_date_to_airtel_format(from_date)
                to_date = str(row.get('To Date', ''))
                to_date_airtel = self.convert_date_to_airtel_format(to_date)
                
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = from_date_airtel + ' ' + from_time if from_time and from_time != 'nan' else from_date_airtel
                
                # For To Date
                to_time = str(row.get('To Time', ''))
                row_cells[3].text = to_date_airtel + ' ' + to_time if to_time and to_time != 'nan' else to_date_airtel
            else:
                # Fallback: use timestamp column
                timestamp = row.get('timestamp', '')
                formatted = self.format_timestamp_for_airtel(timestamp)
                
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = formatted['from_datetime']
                row_cells[3].text = formatted['to_datetime']
            
            # Set font size
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        
        doc.add_paragraph()  # Blank line
        
        # Officer signature
        p = doc.add_paragraph(case_details.get('officer_name', 'Inspector'))
        p = doc.add_paragraph(case_details.get('officer_designation', 'IFSO, Special Cell'))
        p = doc.add_paragraph(case_details.get('officer_location', 'Sec. 16C, Dwarka, New Delhi'))
        p = doc.add_paragraph(f"Contact No.: {case_details.get('officer_contact', 'N/A')}")
        p = doc.add_paragraph(f"Dated : {case_details.get('letter_date', datetime.now().strftime('%d.%m.%Y'))}")
        
        return doc
    
    def create_letter_vi(self, isp_name: str, ip_data: pd.DataFrame, case_details: Dict) -> Document:
        """Create letter for VI with 6-column format (DD:MM:YYYY)"""
        doc = Document()
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        # Header - Legal notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Seeking data under the statutory provisions contained in Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023 or Section 5(2) of the Indian Telegraph Act, 1885 read with Rule 419A of the Indian Telegraph (Amendment) Rules, 2007.")
        run.font.size = Pt(10)
        run.font.italic = True
        
        # Office header
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("OFFICE OF THE CYBER CRIME UNIT, IFSO, SPECIAL CELL, DELHI POLICE,\n")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run("SEC - 16C, DWARKA, NEW DELHI - 110078\n")
        run.font.size = Pt(10)
        run = p.add_run("Contact No. 011-20892632, E-Mail ID : acp-cybercell1@delhipolice.gov.in")
        run.font.size = Pt(9)
        
        # Notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Notice u/s 94 BNSS, 2023")
        run.bold = True
        run.font.size = Pt(11)
        
        doc.add_paragraph()
        
        # To address
        p = doc.add_paragraph("To,")
        p = doc.add_paragraph(f"     \t     The Nodal Officer")
        p = doc.add_paragraph(f"        \t     {isp_name}")
        
        # Subject (with custom subject and email reference)
        subject_text = case_details.get('subject', 'Reg provide information in case')
        email_ref = case_details.get('email_reference', 'N/A')
        subject = f"Subject:- {subject_text} FIR No. {case_details.get('fir_number', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')} ({email_ref})"
        p = doc.add_paragraph(subject)
        p.runs[0].bold = True
        
        # Body (use full body description from user)
        p = doc.add_paragraph("Sir,")
        body_text = case_details.get('body_description', '')
        if not body_text:
            # Fallback to default format if not provided
            body_text = f"It is submitted that case FIR No.{case_details.get('fir_number', 'N/A')}, U/s {case_details.get('sections', 'N/A')}, Dated {case_details.get('fir_date', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')}, Delhi has been registered on the complaint of {case_details.get('complainant', 'N/A')} at IFSO/CCU/Spl. Cell, New Delhi."
        doc.add_paragraph("                " + body_text + " During investigation the following IP details/numbers have emerged as suspect.")
        
        # Requests
        doc.add_paragraph("You are hereby requested to provide the following information/documents:-")
        doc.add_paragraph("1. Details of the user (Name, Address, Contact No. etc.) to whom below IP's were allotted at the mentioned Date & time against each.")
        doc.add_paragraph("2. Kindly provide the ownership of the users, to whom IP was allotted.")
        doc.add_paragraph("3. Kindly preserve the record till further directions.")
        doc.add_paragraph("4. Kindly provide any other useful details.")
        doc.add_paragraph()  # Blank line
        doc.add_paragraph("The above-mentioned information is urgent and a prompt reply is anticipated.")
        
        doc.add_paragraph()
        
        # IP Table - VI Format (6 columns)
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Type'
        hdr_cells[1].text = 'Search Value'
        hdr_cells[2].text = 'From Date\nDD:MM:YYYY'
        hdr_cells[3].text = 'From Time\nHH:MM:SS\n(IST)'
        hdr_cells[4].text = 'To Date\nDD:MM:YYYY'
        hdr_cells[5].text = 'To Time\nHH:MM:SS\n(IST)'
        
        # Make header bold
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(8)
        
        # Add IP data rows
        for idx, row in ip_data.iterrows():
            row_cells = table.add_row().cells
            
            # Get IP address (handle both column names)
            ip_address = str(row.get('Search Value', row.get('ip', '')))
            
            # Get IP type
            ip_type = str(row.get('Type', ''))
            if not ip_type or ip_type == 'nan':
                ip_type = 'IPV6' if ':' in ip_address else 'IPV4'
            
            # Get dates and times (handle both formats)
            from_date = str(row.get('From Date', ''))
            from_time = str(row.get('From Time', ''))
            to_date = str(row.get('To Date', ''))
            to_time = str(row.get('To Time', ''))
            
            if from_date and from_date != 'nan':
                # Use times as-is (NO padding for VI and other ISPs)
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = from_date
                row_cells[3].text = from_time if from_time and from_time != 'nan' else ''
                row_cells[4].text = to_date if to_date and to_date != 'nan' else ''
                row_cells[5].text = to_time if to_time and to_time != 'nan' else ''
            else:
                # Fallback: use timestamp column
                timestamp = row.get('timestamp', '')
                formatted = self.format_timestamp_for_vi(timestamp)
                
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = formatted['from_date']
                row_cells[3].text = formatted['from_time']
                row_cells[4].text = formatted['to_date']
                row_cells[5].text = formatted['to_time']
            
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(8)
        
        doc.add_paragraph()
        
        # Officer signature
        p = doc.add_paragraph(case_details.get('officer_name', 'Inspector'))
        p = doc.add_paragraph(case_details.get('officer_designation', 'IFSO, Special Cell'))
        p = doc.add_paragraph(case_details.get('officer_location', 'Sec. 16C, Dwarka, New Delhi'))
        p = doc.add_paragraph(f"Contact No.: {case_details.get('officer_contact', 'N/A')}")
        p = doc.add_paragraph(f"Dated : {case_details.get('letter_date', datetime.now().strftime('%d.%m.%Y'))}")
        
        return doc
    
    def create_letter_jio(self, isp_name: str, ip_data: pd.DataFrame, case_details: Dict) -> Document:
        """Create letter for Jio with 6-column format (YYYYMMDD)"""
        doc = Document()
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        # Header - Legal notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Seeking data under the statutory provisions contained in Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023 or Section 5(2) of the Indian Telegraph Act, 1885 read with Rule 419A of the Indian Telegraph (Amendment) Rules, 2007.")
        run.font.size = Pt(10)
        run.font.italic = True
        
        # Office header
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("OFFICE OF THE CYBER CRIME UNIT, IFSO, SPECIAL CELL, DELHI POLICE, SEC - 16C, DWARKA, NEW DELHI - 110078\n")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run("Contact No. 011-20892632, E-Mail ID : acp-cybercell1@delhipolice.gov.in")
        run.font.size = Pt(9)
        
        # Notice
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Notice u/s 94 BNSS, 2023")
        run.bold = True
        run.font.size = Pt(11)
        
        doc.add_paragraph()
        
        # To address
        p = doc.add_paragraph("To,")
        p = doc.add_paragraph(f"     \t        The Nodal Officer")
        p = doc.add_paragraph(f"        \t       {isp_name}")
        
        # Subject (with custom subject and email reference)
        subject_text = case_details.get('subject', 'Reg provide information in case')
        email_ref = case_details.get('email_reference', 'N/A')
        subject = f"Subject:- {subject_text} FIR No. {case_details.get('fir_number', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')} ({email_ref})"
        p = doc.add_paragraph(subject)
        p.runs[0].bold = True
        
        # Body (use full body description from user)
        p = doc.add_paragraph("Sir,")
        body_text = case_details.get('body_description', '')
        if not body_text:
            # Fallback to default format if not provided
            body_text = f"It is submitted that case FIR No.{case_details.get('fir_number', 'N/A')}, U/s {case_details.get('sections', 'N/A')}, Dated {case_details.get('fir_date', 'N/A')}, PS {case_details.get('police_station', 'Special Cell')}, Delhi has been registered on the complaint of {case_details.get('complainant', 'N/A')} at IFSO/CCU/Spl. Cell, New Delhi."
        doc.add_paragraph("                " + body_text + " During investigation the following IP details/numbers have emerged as suspect.")
        
        # Requests
        doc.add_paragraph()  # Blank line
        doc.add_paragraph("You are hereby requested to provide the following information/documents:-")
        doc.add_paragraph("1. Details of the user (Name, Address, Contact No. etc.) to whom below IP's were allotted at the mentioned Date & time against each.")
        doc.add_paragraph("2. Kindly provide the ownership of the users, to whom IP was allotted.")
        doc.add_paragraph("3. Kindly preserve the record till further directions.")
        doc.add_paragraph("4. Kindly provide any other useful details.")
        doc.add_paragraph()  # Blank line
        doc.add_paragraph("The above mentioned information is urgent and a prompt reply is anticipated.")
        
        doc.add_paragraph()
        
        # IP Table - Jio Format (6 columns)
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Type'
        hdr_cells[1].text = 'Search Value'
        hdr_cells[2].text = 'From Date\nYYYYMMDD'
        hdr_cells[3].text = 'From Time\nHHMMSS\n(IST)'
        hdr_cells[4].text = 'To Date\nYYYYMMDD'
        hdr_cells[5].text = 'To Time\nHHMMSS\n(IST)'
        
        # Make header bold
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(8)
        
        # Add IP data rows
        for idx, row in ip_data.iterrows():
            row_cells = table.add_row().cells
            
            # Get IP address (handle both column names)
            ip_address = str(row.get('Search Value', row.get('ip', '')))
            
            # Get IP type
            ip_type = str(row.get('Type', ''))
            if not ip_type or ip_type == 'nan':
                ip_type = 'IPV6' if ':' in ip_address else 'IPV4'
            
            # Get dates and times (handle both formats)
            from_date = str(row.get('From Date', ''))
            from_time = str(row.get('From Time', ''))
            to_date = str(row.get('To Date', ''))
            to_time = str(row.get('To Time', ''))
            
            if from_date and from_date != 'nan':
                # Pad times to 6 digits (required by Jio)
                from_time_padded = self.pad_time_to_6_digits(from_time) if from_time and from_time != 'nan' else '000000'
                to_time_padded = self.pad_time_to_6_digits(to_time) if to_time and to_time != 'nan' else '000000'
                
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = from_date
                row_cells[3].text = from_time_padded
                row_cells[4].text = to_date if to_date and to_date != 'nan' else ''
                row_cells[5].text = to_time_padded
            else:
                # Fallback: use timestamp column
                timestamp = row.get('timestamp', '')
                formatted = self.format_timestamp_for_jio(timestamp)
                
                row_cells[0].text = ip_type
                row_cells[1].text = ip_address
                row_cells[2].text = formatted['from_date']
                row_cells[3].text = formatted['from_time']
                row_cells[4].text = formatted['to_date']
                row_cells[5].text = formatted['to_time']
            
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(8)
        
        doc.add_paragraph()
        
        # Officer signature
        p = doc.add_paragraph(case_details.get('officer_name', 'Inspector'))
        p = doc.add_paragraph(case_details.get('officer_designation', 'IFSO, Special Cell'))
        p = doc.add_paragraph(case_details.get('officer_location', 'Sec. 16C, Dwarka, New Delhi'))
        p = doc.add_paragraph(f"Contact No.: {case_details.get('officer_contact', 'N/A')}")
        p = doc.add_paragraph(f"Dated : {case_details.get('letter_date', datetime.now().strftime('%d.%m.%Y'))}")
        
        return doc
    
    def create_jio_txt_file(self, isp_name: str, ip_data: pd.DataFrame, case_details: Dict) -> str:
        """
        Create plain text file for Jio (tab-separated format)
        This is for easy copy-paste into Jio's portal
        Format: Type\tSearch Value\tFrom Date\tFrom Time\tTo Date\tTo Time
        """
        lines = []
        
        # Header line
        lines.append("Type\tSearch Value\tFrom Date (YYYYMMDD)\tFrom Time (HHMMSS IST)\tTo Date (YYYYMMDD)\tTo Time (HHMMSS IST)")
        
        # Data rows
        for idx, row in ip_data.iterrows():
            # Get IP address
            ip_address = str(row.get('Search Value', row.get('ip', '')))
            
            # Get IP type
            ip_type = str(row.get('Type', ''))
            if not ip_type or ip_type == 'nan':
                ip_type = 'IPV6' if ':' in ip_address else 'IPV4'
            
            # Get dates and times
            from_date = str(row.get('From Date', ''))
            from_time = str(row.get('From Time', '')).replace(':', '').zfill(6)
            to_date = str(row.get('To Date', ''))
            to_time = str(row.get('To Time', '')).replace(':', '').zfill(6)
            
            # Add row
            lines.append(f"{ip_type}\t{ip_address}\t{from_date}\t{from_time}\t{to_date}\t{to_time}")
        
        return '\n'.join(lines)
    
    def generate_letter(self, isp_name: str, ip_data: pd.DataFrame, case_details: Dict) -> Document:
        """
        Generate letter for specific ISP using appropriate template
        
        Format Rules:
        - Airtel: 4 columns (Type, Search Value, From Date+Time, To Date+Time)
        - Jio: 6 columns with time padding to 6 digits
        - All Others: 6 columns (Type, Search Value, From Date, From Time, To Date, To Time)
        """
        template_type = self.get_template_type(isp_name)
        print(f"🔍 Generating letter for ISP: {isp_name} → Template: {template_type}")
        
        if template_type == 'airtel':
            # Airtel uses 4-column format (combined date+time)
            print(f"✅ Using Airtel 4-column format for {isp_name}")
            return self.create_letter_airtel(isp_name, ip_data, case_details)
        elif template_type == 'jio':
            # Jio uses 6-column format with time padding
            print(f"✅ Using Jio 6-column format (padded) for {isp_name}")
            return self.create_letter_jio(isp_name, ip_data, case_details)
        else:
            # All other ISPs use 6-column format (no time padding)
            # This includes VI, BSNL, MTNL, and any unknown ISPs
            print(f"✅ Using VI 6-column format (no padding) for {isp_name}")
            return self.create_letter_vi(isp_name, ip_data, case_details)
    
    def generate_all_letters(self, zip_file_path: str, case_details: Dict) -> bytes:
        """
        Generate all ISP letters from ZIP file
        
        Returns:
            ZIP file bytes containing all generated letters
        """
        # Detect ISPs from ZIP
        isp_data = self.detect_isps_from_zip(zip_file_path)
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for isp_name, ip_df in isp_data.items():
                # Generate DOCX letter
                doc = self.generate_letter(isp_name, ip_df, case_details)
                
                # Save DOCX to in-memory buffer
                doc_buffer = io.BytesIO()
                doc.save(doc_buffer)
                doc_buffer.seek(0)
                
                # Add DOCX to ZIP
                docx_filename = f"{isp_name}_Letter_{case_details.get('fir_number', 'N/A').replace('/', '-')}.docx"
                zip_file.writestr(docx_filename, doc_buffer.getvalue())
                
                # For Jio, also create TXT file
                template_type = self.get_template_type(isp_name)
                if template_type == 'jio':
                    txt_content = self.create_jio_txt_file(isp_name, ip_df, case_details)
                    txt_filename = f"{isp_name}_Data_{case_details.get('fir_number', 'N/A').replace('/', '-')}.txt"
                    zip_file.writestr(txt_filename, txt_content)
                    print(f"✅ Created Jio.txt file: {txt_filename}")
                    print(f" Have a Good Day , Thankyou 🔰")
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
