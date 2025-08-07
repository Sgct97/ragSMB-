#!/usr/bin/env python3
"""
Microsoft Investor Relations Earnings Asset Package Scraper
Downloads quarterly earnings asset packages from Microsoft's investor relations website
for the period 2009-2025 as per rules.yaml temporal consistency requirements.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List
import json
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('microsoft_earnings_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MicrosoftEarningsScraper:
    """Scrapes Microsoft investor relations earnings asset packages."""
    
    def __init__(self, download_dir: str = "/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data"):
        """
        Initialize the scraper with download directory configuration.
        
        Args:
            download_dir: Directory path for downloaded files
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Track download status
        self.download_status = []
        self.failed_downloads = []
        
        # Initialize driver as None
        self.driver = None
        
        logger.info(f"Initialized scraper with download directory: {self.download_dir}")
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        Set up Chrome driver with undetected-chromedriver and download preferences.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        # Chrome options for downloads
        chrome_options = uc.ChromeOptions()
        
        # Set download preferences
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True  # Download PDFs instead of opening
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize undetected Chrome driver with version matching
        driver = uc.Chrome(options=chrome_options, version_main=138)
        
        # Enable file downloads in headless mode if needed
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(self.download_dir.absolute())
        })
        
        logger.info("Chrome driver initialized successfully")
        return driver
    
    def wait_for_download_complete(self, timeout: int = 30) -> bool:
        """
        Wait for download to complete by checking for .crdownload files.
        
        Args:
            timeout: Maximum time to wait for download in seconds
            
        Returns:
            True if download completed, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for .crdownload files (Chrome partial downloads)
            partial_files = list(self.download_dir.glob("*.crdownload"))
            
            if not partial_files:
                # No partial downloads, check if new files were added
                time.sleep(1)  # Give a moment for file to finalize
                return True
            
            time.sleep(0.5)
        
        logger.warning(f"Download timeout after {timeout} seconds")
        return False
    
    def navigate_to_quarter(self, year: str, quarter: str) -> bool:
        """
        Navigate to specific year and quarter on the earnings page.
        
        Args:
            year: Fiscal year (e.g., "2025")
            quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
            
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # LONGER wait and explicit wait for the selects to be INTERACTABLE
            wait = WebDriverWait(self.driver, 30)
            
            # Wait for the page to stabilize
            time.sleep(5)
            
            # Debug: print page source to see what's actually loaded
            logger.info("Checking if elements are present on page...")
            
            # Try to find fiscal year select with multiple strategies
            year_select_element = None
            
            # Method 1: Wait for ID
            try:
                year_select_element = wait.until(
                    EC.element_to_be_clickable((By.ID, "fiscal-year-select"))
                )
                logger.info("Found year select by ID")
            except:
                logger.warning("Could not find year select by ID, trying CSS selector")
                try:
                    year_select_element = self.driver.find_element(By.CSS_SELECTOR, "select#fiscal-year-select")
                    logger.info("Found year select by CSS selector")
                except:
                    logger.warning("Could not find year select by CSS selector, trying name")
                    try:
                        year_select_element = self.driver.find_element(By.NAME, "fiscal-year-select")
                        logger.info("Found year select by name")
                    except:
                        logger.error("CANNOT FIND FISCAL YEAR SELECT ELEMENT AT ALL")
                        # Print page source to debug
                        logger.error(f"Current URL: {self.driver.current_url}")
                        logger.error(f"Page title: {self.driver.title}")
                        return False
            
            if year_select_element:
                year_select = Select(year_select_element)
                year_select.select_by_value(year)
                logger.info(f"Selected year: {year}")
                time.sleep(2)
            
            # Select quarter
            quarter_select_element = wait.until(
                EC.element_to_be_clickable((By.ID, "quarter-select"))
            )
            quarter_select = Select(quarter_select_element)
            quarter_select.select_by_value(quarter)
            logger.info(f"Selected quarter: {quarter}")
            time.sleep(2)
            
            # Click GO button
            go_button = wait.until(
                EC.element_to_be_clickable((By.ID, "go"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", go_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", go_button)
            logger.info(f"Clicked GO button for {year} {quarter}")
            
            # Wait for page to update
            time.sleep(5)
            
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout waiting for elements: {e}")
            logger.error(f"Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error navigating to {year} {quarter}: {e}")
            logger.error(f"Current URL: {self.driver.current_url}")
            return False
    
    def download_asset_package(self, year: str, quarter: str) -> bool:
        """
        Download the asset package for current year/quarter.
        
        Args:
            year: Fiscal year
            quarter: Quarter
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Look for asset package button using multiple strategies
            asset_button = None
            
            # Strategy 1: Look for moray-anchor with ASSET PACKAGE text
            try:
                asset_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//moray-anchor[contains(text(), 'ASSET PACKAGE')]"))
                )
            except TimeoutException:
                pass
            
            # Strategy 2: Look for element with aria-label
            if not asset_button:
                try:
                    asset_button = self.driver.find_element(By.XPATH, "//*[@aria-label='ASSET PACKAGE']")
                except NoSuchElementException:
                    pass
            
            # Strategy 3: Look for download link containing FY pattern
            if not asset_button:
                try:
                    asset_button = self.driver.find_element(By.XPATH, f"//a[contains(@href, 'FY{year[-2:]}Q{quarter[-1]}')]")
                except NoSuchElementException:
                    pass
            
            if not asset_button:
                logger.warning(f"No asset package found for {year} {quarter}")
                return False
            
            # Get download URL if available
            download_url = asset_button.get_attribute('href')
            if download_url:
                logger.info(f"Found download URL: {download_url}")
            
            # Record files before download
            files_before = set(self.download_dir.glob("*"))
            
            # Scroll to element and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", asset_button)
            time.sleep(1)
            
            # Try clicking with JavaScript if regular click fails
            try:
                asset_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", asset_button)
            
            logger.info(f"Clicked asset package download for {year} {quarter}")
            
            # Wait for download to complete
            if self.wait_for_download_complete(timeout=60):
                # Find new files
                files_after = set(self.download_dir.glob("*"))
                new_files = files_after - files_before
                
                if new_files:
                    # Rename downloaded file with year and quarter for organization
                    for new_file in new_files:
                        if not new_file.name.startswith(f"FY{year[-2:]}Q{quarter[-1]}"):
                            new_name = f"FY{year[-2:]}Q{quarter[-1]}_{new_file.name}"
                            new_path = new_file.parent / new_name
                            new_file.rename(new_path)
                            logger.info(f"Downloaded and renamed: {new_name}")
                    
                    self.download_status.append({
                        "year": year,
                        "quarter": quarter,
                        "status": "success",
                        "files": [str(f) for f in new_files]
                    })
                    return True
                else:
                    logger.warning(f"No new files detected for {year} {quarter}")
                    return False
            else:
                logger.error(f"Download timeout for {year} {quarter}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download asset package for {year} {quarter}: {e}")
            self.failed_downloads.append({"year": year, "quarter": quarter, "error": str(e)})
            return False
    
    def scrape_all_quarters(self, start_year: int = 2009, end_year: int = 2025):
        """
        Scrape all quarters for specified year range.
        
        Args:
            start_year: Starting fiscal year (default 2009 per rules.yaml)
            end_year: Ending fiscal year (default 2025)
        """
        base_url = "https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast"
        
        # Initialize driver
        self.driver = self.setup_driver()
        
        try:
            # Navigate to the base URL
            logger.info(f"Navigating to {base_url}")
            self.driver.get(base_url)
            time.sleep(5)  # Initial page load
            
            # Iterate through years and quarters
            quarters = ["Q1", "Q2", "Q3", "Q4"]
            total_attempts = 0
            successful_downloads = 0
            
            for year in range(start_year, end_year + 1):
                year_str = str(year)
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing fiscal year {year}")
                logger.info(f"{'='*50}")
                
                for quarter in quarters:
                    total_attempts += 1
                    logger.info(f"\nAttempt {total_attempts}: FY{year} {quarter}")
                    
                    # Navigate to the quarter
                    if self.navigate_to_quarter(year_str, quarter):
                        # Try to download asset package
                        if self.download_asset_package(year_str, quarter):
                            successful_downloads += 1
                            logger.info(f"✅ Successfully downloaded FY{year} {quarter}")
                        else:
                            logger.warning(f"⚠️ No asset package available for FY{year} {quarter}")
                    else:
                        logger.error(f"❌ Failed to navigate to FY{year} {quarter}")
                    
                    # Small delay between downloads to avoid rate limiting
                    time.sleep(2)
            
            # Save scraping report
            self.save_scraping_report(successful_downloads, total_attempts)
            
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            raise
        finally:
            if self.driver:
                logger.info("Closing browser")
                self.driver.quit()
    
    def save_scraping_report(self, successful: int, total: int):
        """
        Save a detailed report of the scraping session.
        
        Args:
            successful: Number of successful downloads
            total: Total number of attempts
        """
        report = {
            "scraping_date": datetime.now().isoformat(),
            "download_directory": str(self.download_dir),
            "total_attempts": total,
            "successful_downloads": successful,
            "success_rate": f"{(successful/total)*100:.1f}%" if total > 0 else "0%",
            "downloads": self.download_status,
            "failed_downloads": self.failed_downloads
        }
        
        report_path = self.download_dir / "scraping_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n{'='*50}")
        logger.info("SCRAPING SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total attempts: {total}")
        logger.info(f"Successful downloads: {successful}")
        logger.info(f"Success rate: {report['success_rate']}")
        logger.info(f"Report saved to: {report_path}")
        
        # List all downloaded files
        downloaded_files = list(self.download_dir.glob("FY*.zip"))
        if downloaded_files:
            logger.info(f"\nDownloaded {len(downloaded_files)} asset packages:")
            for file in sorted(downloaded_files):
                logger.info(f"  - {file.name} ({file.stat().st_size / (1024*1024):.1f} MB)")

def main():
    """Main execution function."""
    logger.info("Starting Microsoft Earnings Asset Package Scraper")
    logger.info("Target: 2009-2025 quarterly earnings packages")
    logger.info("Destination: /Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data")
    
    scraper = MicrosoftEarningsScraper()
    
    try:
        # Scrape all quarters from 2009 to 2025
        scraper.scrape_all_quarters(start_year=2009, end_year=2025)
        logger.info("\n✅ Scraping completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()