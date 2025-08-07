#!/usr/bin/env python3
"""
Direct Microsoft Earnings Asset Package Downloader
Downloads files directly using the URL pattern without browser automation
"""

import os
import requests
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_earnings_packages():
    """Download Microsoft earnings packages using direct URLs."""
    
    base_dir = Path("/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # The URL pattern from the website: https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/FY25Q3-zip
    base_url = "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/"
    
    successful_downloads = 0
    failed_downloads = []
    
    # Years to download (2009-2025)
    for year in range(2009, 2026):
        year_suffix = str(year)[-2:]  # Get last 2 digits
        
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            # Construct the filename pattern
            filename = f"FY{year_suffix}{quarter}-zip"
            url = base_url + filename
            
            logger.info(f"Attempting to download: FY{year} {quarter}")
            logger.info(f"URL: {url}")
            
            try:
                # Make the request
                response = requests.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    # Save the file
                    output_file = base_dir / f"FY{year_suffix}{quarter}_earnings_package.zip"
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content) / (1024 * 1024)  # Convert to MB
                    logger.info(f"✅ Downloaded: {output_file.name} ({file_size:.1f} MB)")
                    successful_downloads += 1
                    
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Not found: FY{year} {quarter} (might not exist yet)")
                    failed_downloads.append(f"FY{year} {quarter}")
                    
                else:
                    logger.error(f"❌ Failed: FY{year} {quarter} - Status code: {response.status_code}")
                    failed_downloads.append(f"FY{year} {quarter}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error downloading FY{year} {quarter}: {e}")
                failed_downloads.append(f"FY{year} {quarter}")
            
            # Small delay to be respectful
            time.sleep(1)
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*50)
    logger.info(f"Successful downloads: {successful_downloads}")
    logger.info(f"Failed/Not found: {len(failed_downloads)}")
    
    if successful_downloads > 0:
        logger.info(f"\n✅ Files saved to: {base_dir}")
        # List downloaded files
        downloaded_files = list(base_dir.glob("*.zip"))
        if downloaded_files:
            logger.info(f"Downloaded {len(downloaded_files)} files:")
            for file in sorted(downloaded_files):
                logger.info(f"  - {file.name} ({file.stat().st_size / (1024*1024):.1f} MB)")

if __name__ == "__main__":
    logger.info("Starting Direct Microsoft Earnings Downloader")
    logger.info("This will attempt to download earnings packages from 2009-2025")
    download_earnings_packages()