const { test, expect } = require('@playwright/test');

test.describe('Insights Implementation Test', () => {
  test('Test insights tab functionality and components', async ({ page }) => {
    // Navigate to the insights URL
    const url = 'http://localhost:3000/#/experiments/1?searchFilter=&orderByKey=attributes.start_time&orderByAsc=false&startTime=ALL&lifecycleFilter=Active&modelVersionFilter=All+Runs&datasetsFilter=W10%3D&compareRunsMode=INSIGHTS';

    console.log('Navigating to:', url);

    // Set up console logging to capture JavaScript errors
    const consoleMessages = [];
    const errors = [];

    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location(),
      });
      console.log(`Console [${msg.type()}]:`, msg.text());
    });

    page.on('pageerror', error => {
      errors.push(error.message);
      console.log('Page error:', error.message);
    });

    // Set up network monitoring for API calls
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/ajax-api/2.0/mlflow/traces/insights/') ||
          request.url().includes('/api/2.0/mlflow/traces/insights/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
        });
        console.log(`API Request: ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', response => {
      if (response.url().includes('/ajax-api/2.0/mlflow/traces/insights/') ||
          response.url().includes('/api/2.0/mlflow/traces/insights/')) {
        console.log(`API Response: ${response.status()} ${response.url()}`);
      }
    });

    try {
      // Navigate to the page
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

      // Wait a bit for the page to fully load
      await page.waitForTimeout(3000);

      // Take initial screenshot
      await page.screenshot({
        path: '/Users/nikhil.thorat/Code/mlflow-corey/insights-test-screenshot.png',
        fullPage: true,
      });
      console.log('Screenshot saved to insights-test-screenshot.png');

      // Check if insights tab/mode is present
      console.log('\n=== Checking for Insights Tab/Mode ===');

      // Look for insights-related elements
      const insightsElements = await page.locator('[data-testid*="insights"], [class*="insights"], [class*="Insights"]').count();
      console.log(`Found ${insightsElements} elements with insights-related selectors`);

      // Check for mode switch or tab
      const modeSwitchElements = await page.locator('[data-testid*="mode"], [class*="mode"], [class*="Mode"]').count();
      console.log(`Found ${modeSwitchElements} elements with mode-related selectors`);

      // Look for the InsightsVolumeCard component
      console.log('\n=== Checking for InsightsVolumeCard Component ===');

      const volumeCardElements = await page.locator('[data-testid*="volume"], [class*="volume"], [class*="Volume"]').count();
      console.log(`Found ${volumeCardElements} elements with volume-related selectors`);

      // Check for any card-like components
      const cardElements = await page.locator('[class*="card"], [class*="Card"]').count();
      console.log(`Found ${cardElements} card-like elements`);

      // Look for chart elements
      console.log('\n=== Checking for Chart Elements ===');

      const chartElements = await page.locator('canvas, svg, [class*="chart"], [class*="Chart"]').count();
      console.log(`Found ${chartElements} chart-related elements`);

      // Check for loading states
      const loadingElements = await page.locator('[class*="loading"], [class*="Loading"], [class*="spinner"], [class*="Spinner"]').count();
      console.log(`Found ${loadingElements} loading-related elements`);

      // Check for error states
      const errorElements = await page.locator('[class*="error"], [class*="Error"]').count();
      console.log(`Found ${errorElements} error-related elements`);

      // Wait a bit more for any async operations
      await page.waitForTimeout(5000);

      // Take final screenshot
      await page.screenshot({
        path: '/Users/nikhil.thorat/Code/mlflow-corey/insights-test-final-screenshot.png',
        fullPage: true,
      });
      console.log('Final screenshot saved to insights-test-final-screenshot.png');

      // Report findings
      console.log('\n=== TEST RESULTS SUMMARY ===');
      console.log(`JavaScript Errors: ${errors.length}`);
      if (errors.length > 0) {
        console.log('Errors found:', errors);
      }

      console.log(`Console Messages: ${consoleMessages.length}`);
      const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
      const warningMessages = consoleMessages.filter(msg => msg.type === 'warning');
      console.log(`- Errors: ${errorMessages.length}`);
      console.log(`- Warnings: ${warningMessages.length}`);

      if (errorMessages.length > 0) {
        console.log('Console Errors:');
        errorMessages.forEach(msg => console.log(`  ${msg.text}`));
      }

      console.log(`API Calls to insights endpoints: ${apiCalls.length}`);
      if (apiCalls.length > 0) {
        console.log('API calls made:');
        apiCalls.forEach(call => console.log(`  ${call.method} ${call.url}`));
      } else {
        console.log('⚠️  No API calls to insights endpoints detected');
      }

      // Check page title and URL
      const title = await page.title();
      const currentUrl = page.url();
      console.log(`Page title: ${title}`);
      console.log(`Current URL: ${currentUrl}`);

      // Look for specific text content
      const pageText = await page.textContent('body');
      const hasInsightsText = pageText.toLowerCase().includes('insights');
      console.log(`Page contains "insights" text: ${hasInsightsText}`);

    } catch (error) {
      console.error('Test execution error:', error);

      // Take error screenshot
      try {
        await page.screenshot({
          path: '/Users/nikhil.thorat/Code/mlflow-corey/insights-test-error-screenshot.png',
          fullPage: true,
        });
        console.log('Error screenshot saved to insights-test-error-screenshot.png');
      } catch (screenshotError) {
        console.error('Could not take error screenshot:', screenshotError);
      }
    }
  });
});
