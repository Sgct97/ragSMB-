#!/usr/bin/env python3
"""
Microsoft XLSX Sheet Extractor & PDF Converter
Extracts individual sheets from XLSX files and converts half to PDF format
"""

import pandas as pd
import os
import sys
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_xlsx_sheets(source_dirs, output_base_dir, convert_to_pdf_ratio=0.5):
    """
    Extract individual sheets from XLSX files and convert some to PDF
    
    Args:
        source_dirs: List of directories to scan for XLSX files
        output_base_dir: Base directory for output files
        convert_to_pdf_ratio: Fraction of sheets to convert to PDF (0.5 = 50%)
    """
    
    # Create output directories
    csv_dir = os.path.join(output_base_dir, 'extracted_csv')
    pdf_dir = os.path.join(output_base_dir, 'extracted_pdf')
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    xlsx_files = []
    
    # Find all XLSX files
    for source_dir in source_dirs:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.xlsx') and not file.startswith('~'):
                    xlsx_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(xlsx_files)} XLSX files")
    
    total_sheets = 0
    pdf_count = 0
    csv_count = 0
    
    for xlsx_file in xlsx_files:
        try:
            # Extract base filename for naming
            base_name = os.path.splitext(os.path.basename(xlsx_file))[0]
            
            # Read Excel file
            xl_file = pd.ExcelFile(xlsx_file)
            sheets = xl_file.sheet_names
            
            logger.info(f"Processing {base_name}: {len(sheets)} sheets")
            
            for i, sheet_name in enumerate(sheets):
                try:
                    # Read sheet data
                    df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
                    
                    # Skip empty sheets
                    if df.empty:
                        continue
                    
                    # Clean sheet name for filename
                    clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    clean_sheet_name = clean_sheet_name.replace(' ', '_')
                    
                    # Create filename with temporal info
                    output_name = f"{base_name}_{clean_sheet_name}"
                    
                    # Decide format: PDF or CSV (50/50 split roughly)
                    should_convert_to_pdf = (total_sheets % 2 == 0)
                    
                    if should_convert_to_pdf:
                        # Convert to PDF
                        pdf_path = os.path.join(pdf_dir, f"{output_name}.pdf")
                        convert_dataframe_to_pdf(df, pdf_path, f"{base_name} - {sheet_name}")
                        pdf_count += 1
                        logger.debug(f"  Created PDF: {output_name}.pdf")
                    else:
                        # Save as CSV
                        csv_path = os.path.join(csv_dir, f"{output_name}.csv")
                        df.to_csv(csv_path, index=False)
                        csv_count += 1
                        logger.debug(f"  Created CSV: {output_name}.csv")
                    
                    total_sheets += 1
                    
                except Exception as e:
                    logger.warning(f"  Error processing sheet '{sheet_name}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing {xlsx_file}: {e}")
            continue
    
    logger.info(f"Extraction complete!")
    logger.info(f"Total sheets processed: {total_sheets}")
    logger.info(f"CSV files created: {csv_count}")
    logger.info(f"PDF files created: {pdf_count}")
    
    return csv_count, pdf_count

def convert_dataframe_to_pdf(df, output_path, title):
    """Convert pandas DataFrame to PDF"""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_para = Paragraph(title, styles['Title'])
        story.append(title_para)
        
        # Limit data size for PDF (first 50 rows, first 10 columns)
        df_limited = df.iloc[:50, :10]
        
        # Convert DataFrame to list of lists for ReportLab
        data = [df_limited.columns.tolist()]  # Header
        data.extend(df_limited.fillna('').astype(str).values.tolist())  # Data
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
    except Exception as e:
        logger.error(f"Error creating PDF {output_path}: {e}")
        # Fallback: create simple text-based PDF
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            story.append(Paragraph(title, styles['Title']))
            story.append(Paragraph(f"Data summary: {len(df)} rows, {len(df.columns)} columns", styles['Normal']))
            doc.build(story)
        except Exception as e:
            logger.error(f"Fallback PDF creation failed for {output_path}: {e}")

if __name__ == "__main__":
    # Define source directories
    source_dirs = [
        '/Users/spensercourville-taylor/htmlfiles/RAGtest/data',
        '/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data'
    ]
    
    output_base = '/Users/spensercourville-taylor/htmlfiles/RAGtest'
    
    print("=== XLSX EXTRACTION PREVIEW ===")
    print(f"Source directories: {source_dirs}")
    print(f"Output directories:")
    print(f"  CSV: {output_base}/extracted_csv/")
    print(f"  PDF: {output_base}/extracted_pdf/")
    print("Starting XLSX sheet extraction...")
    csv_count, pdf_count = extract_xlsx_sheets(source_dirs, output_base, convert_to_pdf_ratio=0.5)
    
    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"CSV files created: {csv_count}")
    print(f"PDF files created: {pdf_count}")
    print(f"Total new documents: {csv_count + pdf_count}")