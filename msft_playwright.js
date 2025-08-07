const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 250 });
  const page = await browser.newPage();
  const downloadDir = '/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data';
  await page.context().setDefaultTimeout(120000);

  const years = Array.from({length: 10}, (_, i) => (2016 + i).toString());
  const quarters = ['1', '2', '3', '4'];

  for (const year of years) {
    for (const quarter of quarters) {
      const url = `https://www.microsoft.com/en-us/investor/earnings/FY-${year}-Q${quarter}/press-release-webcast`;
      console.log(`Loading ${year} Q${quarter}: ${url}`);
      let success = false;
      for (let retry = 0; retry < 3; retry++) {
        try {
          await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
          await page.waitForTimeout(10000); // Wait for JS render
          console.log('Checking for asset button...');
          let buttonExists = false;
          for (let check = 0; check < 10; check++) {
            buttonExists = await page.evaluate(() => !!document.querySelector('moray-anchor[aria-label="ASSET PACKAGE"]'));
            if (buttonExists) break;
            await page.waitForTimeout(5000);
          }
          if (buttonExists) {
            console.log('Found asset button');
            await page.evaluate(() => document.querySelector('moray-anchor[aria-label="ASSET PACKAGE"]').click());
            console.log('Clicked, downloading...');
            await page.waitForTimeout(10000); // Wait for download
            success = true;
            break;
          } else {
            console.log('Button not found');
          }
        } catch (e) {
          console.error(`Retry ${retry+1} failed: ${e.message}`);
          await page.waitForTimeout(5000);
        }
      }
      if (!success) console.log(`Skipping ${year} Q${quarter}`);
    }
  }

  await browser.close();
})(); 