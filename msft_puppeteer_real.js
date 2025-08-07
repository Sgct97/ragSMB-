const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    userDataDir: '/Users/spensercourville-taylor/Library/Application Support/Google/Chrome/Default',
    slowMo: 250
  });
  const page = await browser.newPage();
  await page.goto('https://www.microsoft.com/en-us/investor/earnings/FY-2025-Q3/press-release-webcast', {waitUntil: 'networkidle0', timeout: 120000});
  
  const years = Array.from({length: 17}, (_, i) => (2025 - i).toString());
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];
  
  for (const year of years) {
    for (const quarter of quarters) {
      const url = `https://www.microsoft.com/en-us/investor/earnings/FY-${year}-Q${quarter}/press-release-webcast`;
      console.log(`Loading ${year} ${quarter}: ${url}`);
      await page.goto(url, {waitUntil: 'networkidle0', timeout: 120000});
      
      try {
        const asset = await page.waitForSelector('moray-anchor[aria-label="ASSET PACKAGE"]', {timeout: 60000, visible: true});
        if (asset) {
          await asset.click();
          console.log(`✅ Downloaded ${year} ${quarter}`);
          await page.waitForTimeout(5000);
        } else {
          console.log(`No asset button on page for ${year} ${quarter}`);
        }
      } catch (e) {
        console.error(e.message);
      }
    }
  }
  
  await browser.close();
})(); 