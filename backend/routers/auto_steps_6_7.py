"""
Automatic Steps 6 & 7 Processor
Handles ISP separation, analysis reports, and letter generation
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse

from database import get_session
import pandas as pd
import io
import zipfile
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict
from collections import defaultdict

# Import ISP letter generator
from utils.isp_letter_generator import ISPLetterGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


def separate_by_isp(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Separate data by ISP
    Returns dict: {isp_name: dataframe}
    """
    isp_data = {}
    
    # Group by ISP
    for isp_name, group in df.groupby('isp'):
        if pd.notna(isp_name) and isp_name.strip() and isp_name != 'Unknown':
            isp_data[isp_name] = group.copy()
    
    return isp_data


def create_analysis_report(isp_data: Dict[str, pd.DataFrame]) -> str:
    """
    Create analysis summary report
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("ISP ANALYSIS REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Overall statistics
    total_ips = sum(len(df) for df in isp_data.values())
    report_lines.append(f"Total IPs: {total_ips}")
    report_lines.append(f"Total ISPs: {len(isp_data)}")
    report_lines.append("")
    
    # Per-ISP breakdown
    report_lines.append("ISP BREAKDOWN:")
    report_lines.append("-" * 60)
    
    for isp_name, df in sorted(isp_data.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(df)
        percentage = (count / total_ips * 100) if total_ips > 0 else 0
        
        # Get unique cities
        cities = df['city'].value_counts().head(3)
        top_cities = ", ".join([f"{city} ({count})" for city, count in cities.items()])
        
        report_lines.append(f"\n{isp_name}:")
        report_lines.append(f"  Total IPs: {count} ({percentage:.1f}%)")
        report_lines.append(f"  Top Cities: {top_cities}")
        
        # Date range
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                min_date = df['timestamp'].min()
                max_date = df['timestamp'].max()
                if pd.notna(min_date) and pd.notna(max_date):
                    report_lines.append(f"  Date Range: {min_date} to {max_date}")
            except:
                pass
    
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


@router.post("/process-steps-6-7")
async def process_steps_6_7(
    file: UploadFile = File(...),
    investigation_name: str = Form(...),
    subject: str = Form(...),
    email_reference: str = Form(...),
    body_description: str = Form(...),
    fir_number: str = Form(...),
    police_station: str = Form(...),
    db=Depends(get_session)
):
    """
    Automatically process Steps 6 & 7:
    - Step 6: Separate by ISP + Create analysis reports
    - Step 7: Generate ISP letters
    
    Returns: ZIP file with ISP_Reports/ and ISP_Letters/ folders
    """
    try:
        logger.info(f"🚀 Starting automatic Steps 6 & 7 for {investigation_name}")
        
        # Read uploaded CSV (Step 5 output)
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        logger.info(f"📊 Loaded {len(df)} records from CSV")
        
        # Validate required columns
        required_cols = ['timestamp', 'ip', 'country', 'city', 'region', 'isp']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Step 6: Separate by ISP
        logger.info("📂 Step 6: Separating data by ISP...")
        isp_data = separate_by_isp(df)
        
        if not isp_data:
            raise HTTPException(
                status_code=400,
                detail="No valid ISP data found in file"
            )
        
        logger.info(f"✅ Found {len(isp_data)} ISPs: {', '.join(isp_data.keys())}")
        
        # Create analysis report
        analysis_report = create_analysis_report(isp_data)
        
        # Step 7: Generate ISP letters
        logger.info("📝 Step 7: Generating ISP letters...")
        
        case_details = {
            'fir_number': fir_number,
            'police_station': police_station,
            'subject': subject,
            'email_reference': email_reference,
            'body_description': body_description
        }
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add ISP Reports folder
            logger.info("📁 Creating ISP_Reports folder...")
            
            for isp_name, isp_df in isp_data.items():
                # Sanitize ISP name for filename
                safe_isp_name = isp_name.replace(' ', '_').replace('/', '_')
                
                # Save ISP-specific CSV
                csv_buffer = io.BytesIO()
                isp_df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                
                zip_file.writestr(
                    f"ISP_Reports/{safe_isp_name}_Report.csv",
                    csv_buffer.getvalue()
                )
                
                logger.info(f"  ✅ Added {safe_isp_name}_Report.csv ({len(isp_df)} records)")
            
            # Add analysis summary
            zip_file.writestr(
                "ISP_Reports/Analysis_Summary.txt",
                analysis_report
            )
            logger.info("  ✅ Added Analysis_Summary.txt")
            
            # Add ISP Letters folder
            logger.info("📁 Creating ISP_Letters folder...")
            
            letter_generator = ISPLetterGenerator()
            
            for isp_name, isp_df in isp_data.items():
                safe_isp_name = isp_name.replace(' ', '_').replace('/', '_')
                
                try:
                    # Generate letter for this ISP
                    letter_bytes = letter_generator.generate_letter(
                        isp_df,
                        isp_name,
                        case_details
                    )
                    
                    zip_file.writestr(
                        f"ISP_Letters/{safe_isp_name}_Letter.docx",
                        letter_bytes
                    )
                    
                    logger.info(f"  ✅ Added {safe_isp_name}_Letter.docx")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error generating letter for {isp_name}: {e}")
                    # Continue with other ISPs
                    continue
        
        # Prepare ZIP for download
        zip_buffer.seek(0)
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{investigation_name}_complete_{timestamp}.zip"
        
        logger.info(f"✅ Steps 6 & 7 complete! Generated {zip_filename}")
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing Steps 6 & 7: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "auto-steps-6-7"}
