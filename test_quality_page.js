const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Navigate to the quality insights page
  await page.goto('http://localhost:3000/#/experiments/1?searchFilter=&orderByKey=attributes.start_time&orderByAsc=false&startTime=ALL&lifecycleFilter=Active&modelVersionFilter=All+Runs&datasetsFilter=W10%3D&compareRunsMode=INSIGHTS&insightsTimeRange=LAST_7_DAYS&insightsSubpage=quality');
  
  // Wait for the page to load
  await page.waitForTimeout(5000);
  
  console.log('Quality insights page loaded successfully');
  
  // Keep browser open for viewing
  await page.waitForTimeout(30000);
  
  await browser.close();
})();