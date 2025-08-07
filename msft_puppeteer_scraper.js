const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: false, slowMo: 250 }); // Visible for debugging
  const page = await browser.newPage();
  
  const downloadDir = '/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data';
  await page._client().send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: downloadDir
  });
  
  await page.goto('https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast', { waitUntil: 'networkidle2' });
  await page.waitForNavigation({waitUntil: 'networkidle0', timeout: 120000});
  
  const years = Array.from({length: 17}, (_, i) => (2025 - i).toString());
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
  
  for (const year of years) {
    console.log(`\nProcessing Year ${year}`);
    
    for (const quarter of quarters) {
      console.log(`Trying ${year} ${quarter}`);
      
      try {
        await page.waitForSelector('#fiscal-year-select', { timeout: 60000, visible: true });
        await page.evaluate((year) => {
          document.querySelector('#fiscal-year-select').value = year;
        }, year);
        await page.waitForTimeout(3000);

        await page.waitForSelector('#quarter-select', { timeout: 60000, visible: true });
        await page.evaluate((quarter) => {
          document.querySelector('#quarter-select').value = quarter;
        }, quarter);
        await page.waitForTimeout(3000);

        await page.waitForSelector('#go', { timeout: 60000, visible: true });
        await page.click('#go');
        await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 60000 });
        await page.waitForTimeout(5000);

        const assetElement = await page.waitForSelector('moray-anchor[aria-label="ASSET PACKAGE"]', { timeout: 60000, visible: true });
        if (assetElement) {
          await assetElement.click();
          console.log(`✅ Downloaded ${year} ${quarter}`);
          await page.waitForTimeout(5000);
        } else {
          console.log(`No asset for ${year} ${quarter}`);
        }
      } catch (e) {
        console.error(`Error on ${year} ${quarter}: ${e.message}`);
      }
    }
  }
  
  await browser.close();
  console.log('\nDownloads complete! Check ' + downloadDir);
})(); 