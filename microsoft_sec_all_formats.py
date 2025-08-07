#!/usr/bin/env python3
"""
Microsoft SEC EDGAR Complete Document Acquisition
Gets ALL REAL document types from SEC filings
FOLLOWS rules.yaml - Only authentic documents from 2009-2024
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
    'Accept': '*/*'
}

def ensure_data_dir():
    """Create data directory if it doesn't exist"""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

def get_all_filing_documents(cik, accession_number, form_type, filing_date):
    """Get ALL documents from a filing - main doc + all exhibits"""
    
    documents = []
    year = int(filing_date[:4])
    
    # Skip if outside date range
    if year < START_YEAR or year > END_YEAR:
        return documents
    
    # Build the filing URL
    clean_cik = cik.lstrip('0')
    clean_accession = accession_number.replace('-', '')
    filing_base_url = f"{SEC_ARCHIVES}/{clean_cik}/{clean_accession}"
    
    # Get the filing index to see all files
    index_url = f"{filing_base_url}/index.json"
    
    try:
        response = requests.get(index_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            index_data = response.json()
            
            if 'directory' in index_data and 'item' in index_data['directory']:
                items = index_data['directory']['item']
                
                for item in items:
                    item_name = item.get('name', '')
                    item_size = item.get('size', 0)
                    
                    # Get PDF files
                    if item_name.lower().endswith('.pdf'):
                        documents.append({
                            'url': f"{filing_base_url}/{item_name}",
                            'filename': f"microsoft-{form_type}-{filing_date}-{item_name}",
                            'type': 'pdf',
                            'size': item_size
                        })
                    
                    # Get XLSX/XLS files (Excel)
                    elif item_name.lower().endswith(('.xlsx', '.xls')):
                        documents.append({
                            'url': f"{filing_base_url}/{item_name}",
                            'filename': f"microsoft-{form_type}-{filing_date}-{item_name}",
                            'type': 'xlsx',
                            'size': item_size
                        })
                    
                    # Get XML/XBRL files
                    elif item_name.lower().endswith(('.xml', '.xsd')):
                        documents.append({
                            'url': f"{filing_base_url}/{item_name}",
                            'filename': f"microsoft-{form_type}-{filing_date}-{item_name}",
                            'type': 'xml',
                            'size': item_size
                        })
                    
                    # Get graphics (JPG, PNG, GIF)
                    elif item_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        documents.append({
                            'url': f"{filing_base_url}/{item_name}",
                            'filename': f"microsoft-{form_type}-{filing_date}-{item_name}",
                            'type': 'image',
                            'size': item_size
                        })
                    
                    # Get HTML files (often contain formatted reports)
                    elif item_name.lower().endswith(('.htm', '.html')):
                        # Skip the index files
                        if 'index' not in item_name.lower():
                            documents.append({
                                'url': f"{filing_base_url}/{item_name}",
                                'filename': f"microsoft-{form_type}-{filing_date}-{item_name}",
                                'type': 'html',
                                'size': item_size
                            })
    
    except Exception as e:
        print(f"Error getting filing documents: {e}")
    
    return documents

def download_document(doc_info):
    """Download a document from SEC EDGAR"""
    
    url = doc_info['url']
    filename = doc_info['filename']
    filepath = os.path.join(BASE_DIR, filename)
    
    # Clean filename for filesystem
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    filepath = os.path.join(BASE_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(filepath):
        print(f"✓ Already exists: {filename}")
        return True
    
    try:
        # Convert size to int if it's a string
        size_kb = int(doc_info.get('size', 0)) / 1024 if doc_info.get('size') else 0
        print(f"📥 Downloading: {filename} ({size_kb:.1f} KB)")
        response = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            actual_size = os.path.getsize(filepath)
            if actual_size > 500:  # Minimum size check
                print(f"✅ Downloaded: {filename} ({actual_size/1024:.1f} KB)")
                return True
            else:
                os.remove(filepath)
                print(f"❌ File too small, removing: {filename}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} for {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

def get_all_microsoft_filings():
    """Get ALL Microsoft filings from 2009-2024"""
    
    print(f"🔍 Fetching ALL Microsoft filings (CIK: {MICROSOFT_CIK})")
    
    url = f"https://data.sec.gov/submissions/CIK{MICROSOFT_CIK}.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to get company data: HTTP {response.status_code}")
            return []
        
        data = response.json()
        all_filings = []
        
        # Get recent filings
        recent = data.get('filings', {}).get('recent', {})
        if recent:
            forms = recent.get('form', [])
            dates = recent.get('filingDate', [])
            accessions = recent.get('accessionNumber', [])
            
            for i in range(len(forms)):
                if i < len(dates) and i < len(accessions):
                    all_filings.append({
                        'form': forms[i],
                        'date': dates[i],
                        'accession': accessions[i]
                    })
        
        # Get historical filings
        files = data.get('filings', {}).get('files', [])
        for file_info in files:
            file_name = file_info.get('name', '')
            if file_name:
                print(f"📦 Fetching historical file: {file_name}")
                hist_url = f"https://data.sec.gov/submissions/{file_name}"
                
                try:
                    hist_response = requests.get(hist_url, headers=HEADERS, timeout=30)
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        
                        hist_forms = hist_data.get('form', [])
                        hist_dates = hist_data.get('filingDate', [])
                        hist_accessions = hist_data.get('accessionNumber', [])
                        
                        for i in range(len(hist_forms)):
                            if i < len(hist_dates) and i < len(hist_accessions):
                                all_filings.append({
                                    'form': hist_forms[i],
                                    'date': hist_dates[i],
                                    'accession': hist_accessions[i]
                                })
                
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    continue
        
        # Filter by date range
        filtered_filings = []
        for filing in all_filings:
            year = int(filing['date'][:4])
            if START_YEAR <= year <= END_YEAR:
                filtered_filings.append(filing)
        
        print(f"📊 Found {len(filtered_filings)} filings in date range {START_YEAR}-{END_YEAR}")
        return filtered_filings
        
    except Exception as e:
        print(f"❌ Error fetching filings: {e}")
        return []

def main():
    """Main workflow to get ALL document types"""
    
    print("=" * 60)
    print("Microsoft SEC EDGAR Complete Document Acquisition")
    print("Getting ALL File Types: PDF, XLSX, XML, HTML, Images")
    print(f"Date Range: {START_YEAR}-{END_YEAR}")
    print("=" * 60)
    
    ensure_data_dir()
    
    # Get all Microsoft filings
    all_filings = get_all_microsoft_filings()
    
    # Track statistics
    stats = {
        'pdf': 0,
        'xlsx': 0,
        'xml': 0,
        'html': 0,
        'image': 0,
        'total': 0,
        'failed': 0
    }
    
    # Process each filing
    for idx, filing in enumerate(all_filings):
        form = filing['form']
        date = filing['date']
        accession = filing['accession']
        
        # Focus on filings that commonly have exhibits
        if form in ['10-K', '10-Q', '8-K', 'DEF 14A', '10-K/A', '10-Q/A', 'S-8', '11-K', '20-F', 'SD', '4', '5']:
            print(f"\n📂 Processing {form} from {date} ({idx+1}/{len(all_filings)})")
            
            # Get all documents from this filing
            documents = get_all_filing_documents(MICROSOFT_CIK, accession, form, date)
            
            # Download each document
            for doc in documents:
                success = download_document(doc)
                
                if success:
                    stats[doc['type']] += 1
                    stats['total'] += 1
                else:
                    stats['failed'] += 1
                
                # Rate limiting
                time.sleep(0.1)
            
            # Progress report every 10 filings
            if (idx + 1) % 10 == 0:
                print(f"\n📈 Progress Report:")
                print(f"  PDFs: {stats['pdf']}")
                print(f"  Excel: {stats['xlsx']}")
                print(f"  XML/XBRL: {stats['xml']}")
                print(f"  HTML: {stats['html']}")
                print(f"  Images: {stats['image']}")
                print(f"  Total: {stats['total']}")
                print(f"  Failed: {stats['failed']}")
                print("")
            
            # Stop if we have enough documents
            if stats['total'] >= 1000:
                print(f"\n🎯 Reached 1000+ documents! Stopping acquisition.")
                break
    
    # Final summary
    print("\n" + "=" * 60)
    print("ACQUISITION COMPLETE")
    print("=" * 60)
    print(f"PDF Files: {stats['pdf']}")
    print(f"Excel Files: {stats['xlsx']}")
    print(f"XML/XBRL Files: {stats['xml']}")
    print(f"HTML Files: {stats['html']}")
    print(f"Image Files: {stats['image']}")
    print(f"Total Downloaded: {stats['total']}")
    print(f"Failed Downloads: {stats['failed']}")
    print(f"Documents saved to: {BASE_DIR}/")
    print("=" * 60)
    
    # Save manifest
    manifest = {
        "acquisition_date": datetime.now().isoformat(),
        "source": "SEC EDGAR (All Document Types)",
        "date_range": f"{START_YEAR}-{END_YEAR}",
        "statistics": stats,
        "total_filings_processed": idx + 1
    }
    
    with open(os.path.join(BASE_DIR, "microsoft_all_formats_manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Manifest saved to {BASE_DIR}/microsoft_all_formats_manifest.json")

if __name__ == "__main__":
    main()