const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const filePath = 'file://' + path.resolve('index.html');

  try {
    await page.goto(filePath, { waitUntil: 'networkidle' });

    // Check for Map tab (index 8)
    const mapTab = await page.locator('button.tab').nth(8);
    console.log('Map tab text:', await mapTab.innerText());

    // Click Map tab
    await mapTab.click();
    await page.waitForTimeout(1000); // Wait for render

    // Check if panel8 has content
    const panel8 = await page.locator('#panel8');
    const html = await panel8.innerHTML();
    console.log('Panel 8 innerHTML length:', html.length);
    if (html.includes('bracket-node')) {
      console.log('SUCCESS: Bracket nodes found.');
    } else {
      console.log('FAILURE: No bracket nodes found.');
    }

    // Take screenshot
    await page.screenshot({ path: 'final_verification.png', fullPage: true });
    console.log('Screenshot saved to final_verification.png');

  } catch (err) {
    console.error('Error during verification:', err);
  } finally {
    await browser.close();
  }
})();
