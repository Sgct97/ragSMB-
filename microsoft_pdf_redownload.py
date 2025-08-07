#!/usr/bin/env python3
"""
Microsoft SEC PDF Re-downloader
Re-downloads the 137 deleted TXT files as authentic SEC PDF versions
Maintains temporal consistency while adding file format diversity
"""

import requests
import os
import time
from datetime import datetime

# Microsoft CIK and SEC base URL
MICROSOFT_CIK = "0000789019"
BASE_DIR = "data"

# List of deleted files to re-download as PDFs
# Format: form_date.txt -> need to extract form, date, and find accession number
deleted_files = [
    # 2009 filings
    "10-K_2009-07-30", "10-Q_2009-01-22", "10-Q_2009-04-23", "10-Q_2009-10-23",
    "8-K_2009-01-22", "8-K_2009-03-10", "8-K_2009-03-13", "8-K_2009-04-23", 
    "8-K_2009-05-15", "8-K_2009-07-23", "8-K_2009-09-11", "8-K_2009-10-23", 
    "8-K_2009-11-24", "8-K_2009-12-04", "DEF_14A_2009-09-29",
    
    # 2010 filings
    "10-K_2010-07-30", "10-Q_2010-01-28", "10-Q_2010-04-22", "10-Q_2010-10-28",
    "8-K_2010-01-28", "8-K_2010-04-22", "8-K_2010-05-25", "8-K_2010-06-08", 
    "8-K_2010-06-09", "8-K_2010-06-18", "8-K_2010-07-22", "8-K_2010-09-13", 
    "8-K_2010-09-27", "8-K_2010-10-28", "8-K_2010-11-19", "DEF_14A_2010-09-30",
    
    # 2011 filings
    "10-K_2011-07-28", "10-Q_2011-01-27", "10-Q_2011-04-28", "10-Q_2011-10-20",
    "8-K_2011-01-27", "8-K_2011-02-08", "8-K_2011-04-28", "8-K_2011-05-10", 
    "8-K_2011-07-21", "8-K_2011-10-20", "8-K_2011-11-17", "DEF_14A_2011-10-03",
    
    # 2012 filings
    "10-K_2012-07-26", "10-Q_2012-01-19", "10-Q_2012-04-19", "10-Q_2012-10-18",
    "8-K_2012-01-19", "8-K_2012-02-21", "8-K_2012-04-19", "8-K_2012-05-03", 
    "8-K_2012-06-18", "8-K_2012-07-02", "8-K_2012-07-19", "8-K_2012-09-18", 
    "8-K_2012-10-09", "8-K_2012-10-18", "8-K_2012-11-02", "8-K_2012-11-07", 
    "8-K_2012-11-16", "8-K_2012-11-29", "DEF_14A_2012-10-09",
    
    # 2013 filings
    "10-K_2013-07-30", "10-Q_2013-01-24", "10-Q_2013-04-18", "10-Q_2013-10-24",
    "8-K_2013-01-24", "8-K_2013-04-18", "8-K_2013-05-01", "8-K_2013-05-13", 
    "8-K_2013-07-03", "8-K_2013-07-11", "8-K_2013-07-18", "8-K_2013-08-23", 
    "8-K_2013-08-30", "8-K_2013-09-03", "8-K_2013-09-20", "8-K_2013-09-23", 
    "8-K_2013-09-26", "8-K_2013-10-24", "8-K_2013-11-20", "8-K_2013-11-26", 
    "8-K_2013-12-06", "DEF_14A_2013-10-03",
    
    # 2014 filings
    "10-K_2014-07-31", "10-Q_2014-01-23", "10-Q_2014-04-24", "10-Q_2014-10-23",
    "8-K_2014-01-23", "8-K_2014-02-04", "8-K_2014-03-12", "8-K_2014-03-20", 
    "8-K_2014-04-24", "8-K_2014-07-17", "8-K_2014-07-22", "8-K_2014-07-31", 
    "8-K_2014-08-19", "8-K_2014-09-17", "8-K_2014-10-23", "8-K_2014-12-04", 
    "DEF_14A_2014-10-20",
    
    # 2015 filings
    "10-K_2015-07-31", "10-Q_2015-01-26", "10-Q_2015-04-23", "10-Q_2015-10-22",
    "8-K_2015-01-26", "8-K_2015-02-12", "8-K_2015-04-23", "8-K_2015-07-08", 
    "8-K_2015-07-21", "8-K_2015-08-07", "8-K_2015-09-11", "8-K_2015-09-29", 
    "8-K_2015-10-22", "8-K_2015-10-27", "8-K_2015-11-03", "8-K_2015-12-03", 
    "8-K_2015-12-04", "DEF_14A_2015-10-19",
    
    # 2016 filings
    "10-K_2016-07-28", "10-Q_2016-01-28", "10-Q_2016-04-21", "10-Q_2016-10-20",
    "8-K_2016-01-28", "8-K_2016-03-17", "8-K_2016-04-21", "8-K_2016-05-25", 
    "8-K_2016-06-13", "8-K_2016-07-05", "8-K_2016-07-07", "8-K_2016-07-19", 
    "8-K_2016-08-05", "8-K_2016-09-22", "8-K_2016-10-20", "8-K_2016-12-01", 
    "8-K_2016-12-08", "DEF_14A_2016-10-18"
]

def get_accession_number_for_filing(form, date):
    """Get accession number for a specific Microsoft filing"""
    
    # Get Microsoft's filing data from SEC API
    url = f"https://data.sec.gov/submissions/CIK{MICROSOFT_CIK}.json"
    headers = {'User-Agent': 'RAGTest Microsoft PDF Redownload research@example.com'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Search in recent filings first
            recent = data['filings']['recent']
            for i, (filing_date, filing_form, accession) in enumerate(zip(
                recent['filingDate'], recent['form'], recent['accessionNumber']
            )):
                if filing_date == date and filing_form == form:
                    return accession
            
            # Search in historical files if not found in recent
            if 'files' in data['filings'] and data['filings']['files']:
                for file_info in data['filings']['files']:
                    hist_url = f"https://data.sec.gov/submissions/{file_info['name']}"
                    
                    try:
                        hist_response = requests.get(hist_url, headers=headers)
                        if hist_response.status_code == 200:
                            hist_data = hist_response.json()
                            
                            for filing_date, filing_form, accession in zip(
                                hist_data['filingDate'], hist_data['form'], hist_data['accessionNumber']
                            ):
                                if filing_date == date and filing_form == form:
                                    return accession
                    except:
                        continue
                        
    except Exception as e:
        print(f"❌ Error getting accession for {form} {date}: {str(e)}")
    
    return None

def download_pdf_filing(form, date, accession):
    """Download SEC filing as PDF"""
    
    # Clean form name for filename
    clean_form = form.replace(' ', '_').replace('/', '_')
    
    # SEC PDF URL (try common PDF patterns)
    accession_clean = accession.replace('-', '')
    
    # Common SEC PDF patterns to try
    pdf_urls = [
        f"https://www.sec.gov/Archives/edgar/data/{MICROSOFT_CIK}/{accession_clean}/{accession}.pdf",
        f"https://www.sec.gov/Archives/edgar/data/{MICROSOFT_CIK}/{accession_clean}/msft-{form.lower()}.pdf",
        f"https://www.sec.gov/Archives/edgar/data/{MICROSOFT_CIK}/{accession_clean}/msft{form.replace('-', '').replace(' ', '').lower()}.pdf"
    ]
    
    headers = {'User-Agent': 'RAGTest Microsoft PDF Redownload research@example.com'}
    
    for pdf_url in pdf_urls:
        try:
            response = requests.get(pdf_url, headers=headers, timeout=30)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/pdf'):
                
                filename = f"{clean_form}_{date}.pdf"
                filepath = os.path.join(BASE_DIR, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded PDF: {form} {date} -> {filename}")
                return True
                
        except Exception as e:
            continue
    
    print(f"❌ No PDF found for {form} {date} (accession: {accession})")
    return False

def main():
    print("🏢 Microsoft SEC Filing PDF Re-download")
    print("📋 Converting 137 deleted TXT files to authentic SEC PDFs")
    print("🎯 Maintaining temporal consistency with format diversity")
    print("")
    
    success_count = 0
    
    for i, file_identifier in enumerate(deleted_files, 1):
        # Parse form and date from identifier
        if file_identifier.startswith("DEF_14A_"):
            form = "DEF 14A"
            date = file_identifier.replace("DEF_14A_", "")
        else:
            parts = file_identifier.split('_', 1)
            form = parts[0]
            date = parts[1]
        
        print(f"[{i}/{len(deleted_files)}] Processing {form} from {date}...")
        
        # Get accession number
        accession = get_accession_number_for_filing(form, date)
        
        if accession:
            if download_pdf_filing(form, date, accession):
                success_count += 1
            time.sleep(0.5)  # Rate limiting
        else:
            print(f"❌ No accession found for {form} {date}")
        
        time.sleep(0.3)  # Additional rate limiting
    
    print(f"\n🎯 PDF RE-DOWNLOAD COMPLETE!")
    print(f"✅ Successfully downloaded: {success_count}/{len(deleted_files)} PDF filings")
    print(f"📁 All PDF files saved to: {BASE_DIR}/")
    print(f"📊 Format diversity achieved: TXT (newer) + PDF (older)")

if __name__ == "__main__":
    main()