#!/usr/bin/env python3
"""
Microsoft SEC EDGAR Exhibit Downloader
Downloads ONLY REAL exhibit files (PDF, XLSX, etc.) that Microsoft actually filed with SEC
Strictly follows rules.yaml - 100% authentic documents only
"""

import requests
import os
import json
import time
from datetime import datetime
import re

# Configuration per rules.yaml
BASE_DIR = "data"
MICROSOFT_CIK = "0000789019"
START_YEAR = 2009
END_YEAR = 2024

# SEC EDGAR API configuration
SEC_BASE = "https://www.sec.gov"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
HEADERS = {
    'User-Agent': 'RAGTest Research (research@example.com)',
    'Accept': 'application/json,text/html,application/pdf'
}

def ensure_data_dir():
    """Create data directory if it doesn't exist"""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

def get_filing_details(cik, filing_url):
    """Get detailed information about a specific filing including exhibits"""
    try:
        # Convert the filing URL to get the index.json
        # Example: /Archives/edgar/data/789019/000119312520284096/0001193125-20-284096-index.html
        # Becomes: /Archives/edgar/data/789019/000119312520284096/index.json
        
        parts = filing_url.split('/')
        if len(parts) >= 7:
            base_path = '/'.join(parts[:-1])
            json_url = f"{SEC_BASE}{base_path}/index.json"
            
            response = requests.get(json_url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Error getting filing details: {e}")
    
    return None

def download_exhibit(exhibit_url, form_type, filing_date, exhibit_type, exhibit_num):
    """Download a real SEC exhibit file"""
    
    # Determine file extension from exhibit type
    ext = '.txt'  # default
    if 'PDF' in exhibit_type.upper() or exhibit_url.lower().endswith('.pdf'):
        ext = '.pdf'
    elif 'EXCEL' in exhibit_type.upper() or 'XLSX' in exhibit_type.upper() or exhibit_url.lower().endswith(('.xlsx', '.xls')):
        ext = '.xlsx'
    elif 'WORD' in exhibit_type.upper() or exhibit_url.lower().endswith(('.docx', '.doc')):
        ext = '.docx'
    elif 'POWERPOINT' in exhibit_type.upper() or 'PPTX' in exhibit_type.upper() or exhibit_url.lower().endswith(('.pptx', '.ppt')):
        ext = '.pptx'
    elif 'XML' in exhibit_type.upper() or exhibit_url.lower().endswith('.xml'):
        ext = '.xml'
    elif 'HTML' in exhibit_type.upper() or exhibit_url.lower().endswith(('.html', '.htm')):
        ext = '.html'
    
    # Clean exhibit number for filename
    exhibit_num_clean = exhibit_num.replace(' ', '_').replace('.', '_').replace('/', '_')
    
    # Create filename with metadata
    year = filing_date[:4]
    filename = f"microsoft-{form_type}-{year}-exhibit-{exhibit_num_clean}{ext}"
    filepath = os.path.join(BASE_DIR, filename)
    
    # Skip if already downloaded
    if os.path.exists(filepath):
        print(f"✓ Already exists: {filename}")
        return True
    
    # Download the exhibit
    try:
        full_url = f"{SEC_BASE}{exhibit_url}" if exhibit_url.startswith('/') else exhibit_url
        print(f"📥 Downloading exhibit: {filename}")
        
        response = requests.get(full_url, headers=HEADERS, timeout=60, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            if file_size > 500:  # Verify it's not an error page
                print(f"✅ Downloaded: {filename} ({file_size/1024/1024:.1f} MB)")
                return True
            else:
                os.remove(filepath)
                print(f"❌ File too small, likely error page: {filename}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} for exhibit")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading exhibit: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

def get_all_filings_with_exhibits():
    """Get all Microsoft filings and their exhibits"""
    
    print(f"🔍 Fetching Microsoft filings with exhibits (CIK: {MICROSOFT_CIK})")
    
    # Get the company submissions
    url = f"https://data.sec.gov/submissions/CIK{MICROSOFT_CIK}.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to get company data: HTTP {response.status_code}")
            return []
        
        data = response.json()
        all_exhibits = []
        
        # Process recent filings
        recent_filings = data.get('filings', {}).get('recent', {})
        
        if recent_filings:
            forms = recent_filings.get('form', [])
            dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            
            for i in range(min(len(forms), len(dates), len(accession_numbers))):
                form = forms[i]
                date = dates[i]
                accession = accession_numbers[i].replace('-', '')
                
                # Check if date is in our range
                year = int(date[:4])
                if year < START_YEAR or year > END_YEAR:
                    continue
                
                # Focus on forms that commonly have exhibits
                if form in ['10-K', '10-Q', '8-K', 'DEF 14A', '10-K/A', '10-Q/A', 'S-8', '20-F']:
                    filing_url = f"/Archives/edgar/data/{MICROSOFT_CIK.lstrip('0')}/{accession}/"
                    
                    print(f"\n📂 Checking {form} from {date} for exhibits...")
                    
                    # Get filing details including exhibits
                    filing_details = get_filing_details(MICROSOFT_CIK, filing_url)
                    
                    if filing_details and 'directory' in filing_details:
                        items = filing_details['directory'].get('item', [])
                        
                        for item in items:
                            # Look for exhibit files (not the main document)
                            item_name = item.get('name', '')
                            item_type = item.get('type', '')
                            item_desc = item.get('description', '')
                            
                            # Skip main documents and focus on exhibits
                            if 'EX-' in item_name.upper() or 'EXHIBIT' in item_desc.upper():
                                # Check if it's a file type we want
                                if any(ext in item_name.lower() for ext in ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.pptx', '.ppt']):
                                    exhibit_info = {
                                        'form': form,
                                        'date': date,
                                        'exhibit_name': item_name,
                                        'exhibit_type': item_type,
                                        'exhibit_desc': item_desc,
                                        'url': f"{filing_url}{item_name}"
                                    }
                                    all_exhibits.append(exhibit_info)
                                    print(f"  Found exhibit: {item_name} - {item_desc}")
                    
                    # Rate limiting
                    time.sleep(0.2)
        
        # Also check historical filings files
        files = data.get('filings', {}).get('files', [])
        for file_info in files:
            file_name = file_info.get('name', '')
            
            if file_name:
                print(f"\n📦 Fetching historical filing file: {file_name}")
                historical_url = f"https://data.sec.gov/submissions/{file_name}"
                
                try:
                    hist_response = requests.get(historical_url, headers=HEADERS, timeout=30)
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        
                        hist_forms = hist_data.get('form', [])
                        hist_dates = hist_data.get('filingDate', [])
                        hist_accessions = hist_data.get('accessionNumber', [])
                        
                        for i in range(min(len(hist_forms), len(hist_dates), len(hist_accessions))):
                            form = hist_forms[i]
                            date = hist_dates[i]
                            accession = hist_accessions[i].replace('-', '')
                            
                            # Check if date is in our range
                            year = int(date[:4])
                            if year < START_YEAR or year > END_YEAR:
                                continue
                            
                            if form in ['10-K', '10-Q', '8-K', 'DEF 14A', '10-K/A', '10-Q/A', 'S-8']:
                                filing_url = f"/Archives/edgar/data/{MICROSOFT_CIK.lstrip('0')}/{accession}/"
                                
                                print(f"  Checking {form} from {date}...")
                                
                                filing_details = get_filing_details(MICROSOFT_CIK, filing_url)
                                
                                if filing_details and 'directory' in filing_details:
                                    items = filing_details['directory'].get('item', [])
                                    
                                    for item in items:
                                        item_name = item.get('name', '')
                                        item_type = item.get('type', '')
                                        item_desc = item.get('description', '')
                                        
                                        if 'EX-' in item_name.upper() or 'EXHIBIT' in item_desc.upper():
                                            if any(ext in item_name.lower() for ext in ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.pptx', '.ppt']):
                                                exhibit_info = {
                                                    'form': form,
                                                    'date': date,
                                                    'exhibit_name': item_name,
                                                    'exhibit_type': item_type,
                                                    'exhibit_desc': item_desc,
                                                    'url': f"{filing_url}{item_name}"
                                                }
                                                all_exhibits.append(exhibit_info)
                                                print(f"    Found exhibit: {item_name}")
                                
                                time.sleep(0.2)
                
                except Exception as e:
                    print(f"Error processing historical file {file_name}: {e}")
                    continue
        
        return all_exhibits
        
    except Exception as e:
        print(f"❌ Error fetching filings: {e}")
        return []

def main():
    """Main workflow following rules.yaml"""
    
    print("=" * 60)
    print("Microsoft SEC EDGAR Exhibit Acquisition")
    print("Following rules.yaml: ONLY Real Filed Documents")
    print("=" * 60)
    
    ensure_data_dir()
    
    # Get all filings with exhibits
    all_exhibits = get_all_filings_with_exhibits()
    
    print(f"\n📊 Found {len(all_exhibits)} total exhibits to download")
    
    # Download exhibits
    downloaded = 0
    failed = 0
    
    for exhibit in all_exhibits:
        success = download_exhibit(
            exhibit['url'],
            exhibit['form'],
            exhibit['date'],
            exhibit['exhibit_type'],
            exhibit['exhibit_name']
        )
        
        if success:
            downloaded += 1
        else:
            failed += 1
        
        # Rate limiting to be respectful to SEC servers
        time.sleep(0.5)
        
        # Progress update every 10 files
        if (downloaded + failed) % 10 == 0:
            print(f"\n📈 Progress: {downloaded} downloaded, {failed} failed, {len(all_exhibits) - downloaded - failed} remaining\n")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"EXHIBIT ACQUISITION COMPLETE")
    print(f"Successfully downloaded: {downloaded} exhibits")
    print(f"Failed downloads: {failed}")
    print(f"Documents saved to: {BASE_DIR}/")
    print("=" * 60)
    
    # Save manifest for verification
    manifest = {
        "acquisition_date": datetime.now().isoformat(),
        "source": "SEC EDGAR (Official Exhibits Only)",
        "date_range": f"{START_YEAR}-{END_YEAR}",
        "total_exhibits_found": len(all_exhibits),
        "successfully_downloaded": downloaded,
        "failed_downloads": failed,
        "exhibits": all_exhibits[:100]  # Save first 100 for reference
    }
    
    with open(os.path.join(BASE_DIR, "microsoft_exhibits_manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Manifest saved to {BASE_DIR}/microsoft_exhibits_manifest.json")

if __name__ == "__main__":
    main()