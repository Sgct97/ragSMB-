#!/usr/bin/env python3
"""
FIXED Microsoft Earnings Scraper - Using EXACT elements provided
"""

import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup
download_dir = Path("/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data")
download_dir.mkdir(parents=True, exist_ok=True)

# Chrome options
chrome_options = Options()
prefs = {
    "download.default_directory": str(download_dir.absolute()),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless")

# Start Chrome
print("Starting Chrome...")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 30)

try:
    # Navigate to the page
    print("Navigating to Microsoft earnings page...")
    driver.get("https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast")
    
    # WAIT for the page to fully load - give it proper time
    print("Waiting for page to load...")
    time.sleep(10)
    
    # Start from recent years that definitely have data
    years_to_try = ["2020", "2021", "2022", "2023", "2024", "2025"]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    
    for year in years_to_try:
        print(f"\n========== Processing Year {year} ==========")
        
        for quarter in quarters:
            print(f"\nTrying {year} {quarter}...")
            
            try:
                # EXACT selector you provided: select with id="fiscal-year-select"
                print("Finding year dropdown...")
                year_select = wait.until(
                    EC.presence_of_element_located((By.ID, "fiscal-year-select"))
                )
                Select(year_select).select_by_value(year)
                time.sleep(2)
                
                # EXACT selector you provided: select with id="quarter-select"  
                print("Finding quarter dropdown...")
                quarter_select = wait.until(
                    EC.presence_of_element_located((By.ID, "quarter-select"))
                )
                Select(quarter_select).select_by_value(quarter)
                time.sleep(2)
                
                # EXACT selector you provided: button with id="go"
                print("Finding GO button...")
                go_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "go"))
                )
                driver.execute_script("arguments[0].click();", go_button)
                print(f"Clicked GO for {year} {quarter}")
                
                # Wait for page update
                time.sleep(5)
                
                # Now look for the asset package download - using the moray-anchor element
                print("Looking for asset package download...")
                try:
                    # Try finding by the aria-label first
                    asset_link = driver.find_element(By.CSS_SELECTOR, '[aria-label="ASSET PACKAGE"]')
                    href = asset_link.get_attribute('href')
                    
                    if href:
                        print(f"Found download link: {href}")
                        # Click to download
                        driver.execute_script("arguments[0].click();", asset_link)
                        print(f"✅ Downloaded {year} {quarter}")
                        time.sleep(3)  # Wait for download to start
                    else:
                        print(f"No href found for {year} {quarter}")
                        
                except Exception as e:
                    print(f"No asset package for {year} {quarter}: {e}")
                    
            except Exception as e:
                print(f"Error processing {year} {quarter}: {e}")
                continue
    
    print("\n========== DOWNLOAD COMPLETE ==========")
    print(f"Files saved to: {download_dir}")
    
    # List downloaded files
    downloaded_files = list(download_dir.glob("*"))
    if downloaded_files:
        print(f"\nDownloaded {len(downloaded_files)} files:")
        for file in downloaded_files:
            print(f"  - {file.name}")
    
    time.sleep(5);  # Wait for downloads to complete
    
finally:
    print("\nClosing browser...")
    time.sleep(5)
    driver.quit()