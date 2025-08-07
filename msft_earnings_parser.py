# Non-Selenium Microsoft Earnings Downloader using Requests and BeautifulSoup

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_earnings_packages(start_year=2009, end_year=2025):
    base_url = "https://www.microsoft.com/en-us/investor/earnings/FY-{year}-Q{quarter}/press-release-webcast"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    download_dir = Path("/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    for year in range(start_year, end_year + 1):
        for quarter in [1, 2, 3, 4]:
            url = base_url.format(year=year, quarter=quarter)
            logging.info(f"Fetching page for FY{year} Q{quarter}: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Page not found for FY{year} Q{quarter}")
                continue
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the asset package link using the exact element you provided
            asset_link = soup.find('moray-anchor', {'aria-label': 'ASSET PACKAGE'})
            if not asset_link:
                logging.warning(f"No asset package found for FY{year} Q{quarter}")
                continue
            
            download_url = asset_link.get('href')
            if not download_url:
                logging.warning(f"No href in asset link for FY{year} Q{quarter}")
                continue
            
            # Download the file
            file_name = f"FY{str(year)[-2:]}Q{quarter}_earnings.zip"
            file_path = download_dir / file_name
            
            dl_response = requests.get(download_url, headers=headers, timeout=30)
            if dl_response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(dl_response.content)
                logging.info(f"✅ Downloaded: {file_name} ({len(dl_response.content)/1024/1024:.2f} MB)")
            else:
                logging.error(f"Failed to download {file_name}: Status {dl_response.status_code}")
            
            time.sleep(2)  # Polite delay

if __name__ == "__main__":
    download_earnings_packages() 