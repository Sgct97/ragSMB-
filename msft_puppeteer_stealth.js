const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    slowMo: 250,
    userDataDir: '/Users/spensercourville-taylor/Library/Application Support/Google/Chrome/Default'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
  
  const years = Array.from({length: 17}, (_, i) => (2025 - i).toString());
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
  
  // Load page once
  await page.goto('https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast', {waitUntil: 'networkidle0', timeout: 120000});

  // Then loop with selections
  for (const year of years) {
    for (const quarter of quarters) {
      console.log(`Trying ${year} ${quarter}`);
      try {
        await page.waitForSelector('select#fiscal-year-select', {visible: true, timeout: 60000});
        await page.select('select#fiscal-year-select', year);
        await page.waitForTimeout(3000);
        
        await page.waitForSelector('select#quarter-select', {visible: true, timeout: 60000});
        await page.select('select#quarter-select', quarter);
        await page.waitForTimeout(3000);
        
        await page.waitForSelector('button#go', {visible: true, timeout: 60000});
        await page.click('button#go');
        await page.waitForNavigation({waitUntil: 'networkidle0', timeout: 120000});
        
        const asset = await page.waitForSelector('moray-anchor[aria-label="ASSET PACKAGE"]', {visible: true, timeout: 60000});
        if (asset) {
          await asset.click();
          console.log(`Downloaded ${year} ${quarter}`);
          await page.waitForTimeout(5000);
        } else {
          console.log(`No asset for ${year} ${quarter}`);
        }
      } catch (e) {
        console.error(e.message);
        // Go back to main page if error
        await page.goto('https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast', {timeout: 60000});
      }
    }
  }
  
  await browser.close();
})(); 