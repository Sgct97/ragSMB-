#!/usr/bin/env python3
"""
Microsoft Corporation COMPREHENSIVE SEC Filing Acquisition (2009-2024)
Handles both recent AND historical filings to ensure complete 15-year coverage
Focuses on TXT files for optimal RAG system compatibility
"""

import requests
import os
import json
from datetime import datetime

# Constants - Microsoft RAG System (2009-2024)
BASE_DIR = "data"
MICROSOFT_CIK = "0000789019"
TARGET_FORMS = ['10-K', '10-Q', '8-K', 'DEF 14A']
START_YEAR = 2009
END_YEAR = 2024

def download_filing_txt(url, form, date, cik):
    """Download only TXT filings (better for RAG systems)"""
    headers = {'User-Agent': 'RAGTest Microsoft Comprehensive research@example.com'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Clean filename for filesystem compatibility
            clean_form = form.replace(' ', '_').replace('/', '_')
            file_path = f"{BASE_DIR}/{clean_form}_{date}.txt"
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
            print(f"✅ Downloaded {form} from {date} -> {file_path}")
            return True
        else:
            print(f"❌ Failed {form} {date}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {form} {date}: {str(e)}")
        return False

def get_comprehensive_filings(cik):
    """Get ALL Microsoft filings - recent AND historical"""
    
    print(f"🔍 Fetching comprehensive Microsoft filings (CIK: {cik})")
    
    # Step 1: Get main company data
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {'User-Agent': 'RAGTest Microsoft Comprehensive research@example.com'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get company data: HTTP {response.status_code}")
        return []
    
    data = response.json()
    all_filings = []
    
    # Step 2: Process recent filings
    print("📊 Processing recent filings...")
    recent_filings = data['filings']['recent']
    
    for i, (date, form, accession) in enumerate(zip(
        recent_filings['filingDate'], 
        recent_filings['form'], 
        recent_filings['accessionNumber']
    )):
        filing_year = datetime.strptime(date, '%Y-%m-%d').year
        
        if form in TARGET_FORMS and START_YEAR <= filing_year <= END_YEAR:
            all_filings.append({
                'form': form,
                'date': date,
                'accession': accession,
                'year': filing_year
            })
    
    # Step 3: Process historical filing files if they exist
    if 'files' in data['filings'] and data['filings']['files']:
        print("📚 Processing historical filing archives...")
        
        for file_info in data['filings']['files']:
            historical_url = f"https://data.sec.gov/submissions/{file_info['name']}"
            
            try:
                hist_response = requests.get(historical_url, headers=headers)
                if hist_response.status_code == 200:
                    hist_data = hist_response.json()
                    
                    for i, (date, form, accession) in enumerate(zip(
                        hist_data['filingDate'], 
                        hist_data['form'], 
                        hist_data['accessionNumber']
                    )):
                        filing_year = datetime.strptime(date, '%Y-%m-%d').year
                        
                        if form in TARGET_FORMS and START_YEAR <= filing_year <= END_YEAR:
                            all_filings.append({
                                'form': form,
                                'date': date,
                                'accession': accession,
                                'year': filing_year
                            })
                else:
                    print(f"⚠️ Historical file {file_info['name']}: HTTP {hist_response.status_code}")
            except Exception as e:
                print(f"⚠️ Error processing historical file {file_info['name']}: {str(e)}")
    
    # Remove duplicates and sort by date
    seen = set()
    unique_filings = []
    for filing in all_filings:
        key = (filing['form'], filing['date'], filing['accession'])
        if key not in seen:
            seen.add(key)
            unique_filings.append(filing)
    
    # Sort by date (oldest first for systematic processing)
    unique_filings.sort(key=lambda x: x['date'])
    
    return unique_filings

def main():
    print("🏢 Microsoft Corporation COMPREHENSIVE SEC Acquisition")
    print("📋 CIK: 0000789019 | Period: 2009-2024 | TXT files only")
    print("📊 Target Forms: 10-K, 10-Q, 8-K, DEF 14A")
    print("")
    
    # Ensure data directory exists
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Get all Microsoft filings
    filings = get_comprehensive_filings(MICROSOFT_CIK)
    
    if not filings:
        print("❌ No filings found!")
        return
    
    print(f"📋 Found {len(filings)} Microsoft filings in target period")
    
    # Analyze year distribution
    year_count = {}
    form_count = {}
    
    for filing in filings:
        year_count[filing['year']] = year_count.get(filing['year'], 0) + 1
        form_count[filing['form']] = form_count.get(filing['form'], 0) + 1
    
    print("\n📊 Year Distribution:")
    for year in sorted(year_count.keys()):
        print(f"   {year}: {year_count[year]} filings")
    
    print("\n📊 Form Type Distribution:")
    for form in sorted(form_count.keys()):
        print(f"   {form}: {form_count[form]} filings")
    
    print(f"\n⬇️ Downloading {len(filings)} TXT filings...")
    
    # Download all filings (TXT only)
    success_count = 0
    
    for i, filing in enumerate(filings, 1):
        # Construct TXT download URL
        accession_clean = filing['accession'].replace('-', '')
        txt_url = f"https://www.sec.gov/Archives/edgar/data/{MICROSOFT_CIK}/{accession_clean}/{filing['accession']}.txt"
        
        print(f"[{i}/{len(filings)}] ", end="")
        
        if download_filing_txt(txt_url, filing['form'], filing['date'], MICROSOFT_CIK):
            success_count += 1
    
    print(f"\n🎯 COMPREHENSIVE ACQUISITION COMPLETE!")
    print(f"✅ Successfully downloaded: {success_count}/{len(filings)} filings")
    print(f"📁 All files saved to: {BASE_DIR}/")
    print(f"📄 TXT format only (optimal for RAG system)")
    
    # Final verification
    downloaded_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.txt') and any(form.replace(' ', '_') in f for form in TARGET_FORMS)]
    print(f"📋 Verification: {len(downloaded_files)} Microsoft SEC TXT files in {BASE_DIR}/")

if __name__ == "__main__":
    main()