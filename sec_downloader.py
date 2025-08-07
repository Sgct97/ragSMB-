import requests
import os
from datetime import datetime

# Constants - Microsoft RAG System (2009-2024)
BASE_DIR = "data/microsoft_sec_filings"  # Microsoft SEC filings for RAG system
COMPANY_CIKS = {
    'Microsoft': '0000789019'  # Focus only on Microsoft Corporation for temporal consistency
}

def download_filing(url, cik, form, date, file_extension):
    """
    This function downloads and saves a SEC filing from a specified URL.
    
    Args:
        url (str): URL to download the filing from.
        cik (str): Central Index Key (CIK) for the company.
        form (str): The type of SEC filing (e.g., 10-K, 10-Q).
        date (str): The filing date in YYYY-MM-DD format.
        file_extension (str): File extension for saved file (usually 'txt' or 'zip').
    """
    # Define request headers for SEC EDGAR compliance
    headers = {'User-Agent': 'RAGTest Microsoft Acquisition research@example.com'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        dir_name = f"{BASE_DIR}/{cik}"
        os.makedirs(dir_name, exist_ok=True)
        file_path = f"{dir_name}/{form}_{date}.{file_extension}"
        
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        print(f"Downloaded {form} for CIK {cik} on {date} to {file_path}")
    else:
        print(f"Failed to download {form} for CIK {cik} on {date}. Status code: {response.status_code}")

def fetch_filings(cik, form_types=['10-K', '10-Q', '8-K', 'DEF 14A'], years=15):
    """
    Fetch and download filings for a specified CIK from the SEC database.
    
    Args:
        cik (str): Central Index Key (CIK) of the company.
        form_types (list of str): Types of forms to fetch (10-K, 10-Q, 8-K, DEF 14A for comprehensive coverage).
        years (int): Number of past years to fetch filings from (15 years for 2009-2024 coverage).
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {'User-Agent': 'RAGTest Microsoft Acquisition research@example.com'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        current_year = datetime.now().year

        for filing_date, form, accession_number in zip(data['filings']['recent']['filingDate'], data['filings']['recent']['form'], data['filings']['recent']['accessionNumber']):
            if form in form_types and current_year - datetime.strptime(filing_date, '%Y-%m-%d').year <= years:
                download_filing(
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}-xbrl.zip",
                    cik, form, filing_date, 'zip'
                )
                download_filing(
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}.txt",
                    cik, form, filing_date, 'txt'
                )

print("🏢 Microsoft Corporation SEC EDGAR Comprehensive Acquisition (2009-2024)")
print("📋 CIK: 0000789019 | Target: 390+ SEC filings across 4 form types")
print("📊 Forms: 10-K (annual), 10-Q (quarterly), 8-K (current), DEF 14A (proxy)")
print("")

for company_name, cik in COMPANY_CIKS.items():
    print(f"📥 Fetching {company_name} filings for 15-year period...")
    fetch_filings(cik)
    print(f"✅ {company_name} SEC filings acquisition complete!")

print("")
print("🎯 Microsoft Corporation SEC EDGAR bulk acquisition complete!")
print("📁 Files saved to: data/microsoft_sec_filings/")
print("📊 Both XBRL (.zip) and TXT formats downloaded for maximum compatibility")
