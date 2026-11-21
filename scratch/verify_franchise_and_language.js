import { createRequire } from 'module';
import path from 'path';
const require = createRequire('e:/LLM/AnimeVerse-AI/frontend/package.json');
const puppeteer = require('puppeteer');

const ARTIFACT_DIR = 'C:/Users/admin/.gemini/antigravity/brain/50c056d6-7e88-4bef-8ce4-a3e804331994';

async function runBrowserVerification() {
  console.log('Launching headless browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  try {
    // 1. Search Black Clover on Discover Page
    console.log('1. Testing Black Clover search & grouping on Discover...');
    await page.goto('http://127.0.0.1:5173/discover?q=Black+Clover', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(r => setTimeout(r, 2500));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'franchise_search_grouping.png'), fullPage: false });
    console.log('-> Saved franchise_search_grouping.png');

    // 2. Open Black Clover Franchise Details Page
    console.log('2. Testing Black Clover Franchise Details page...');
    await page.goto('http://127.0.0.1:5173/franchise/1', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(r => setTimeout(r, 2000));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'franchise_details_page.png'), fullPage: true });
    console.log('-> Saved franchise_details_page.png');

    // 3. Open Black Clover Anime Details & inspect Franchise Navigator
    console.log('3. Testing Anime Details Franchise Entry Navigator...');
    await page.goto('http://127.0.0.1:5173/anime/34572', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'anime_details_franchise_navigator.png'), fullPage: false });
    console.log('-> Saved anime_details_franchise_navigator.png');

    // 4. Watch Anywhere Hub - Demon Slayer Verified Languages
    console.log('4. Testing Watch Anywhere Hub (Demon Slayer)...');
    await page.goto('http://127.0.0.1:5173/watch', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(r => setTimeout(r, 2000));

    // Click Demon Slayer quick button
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const dsBtn = btns.find(b => b.textContent.includes('Demon Slayer'));
      if (dsBtn) dsBtn.click();
    });
    await new Promise(r => setTimeout(r, 2500));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'watch_demon_slayer_verified_languages.png'), fullPage: false });
    console.log('-> Saved watch_demon_slayer_verified_languages.png');

    // 5. Filter Audio: Tamil for Demon Slayer
    console.log('5. Testing Audio: Tamil filter for Demon Slayer...');
    await page.evaluate(() => {
      const selects = Array.from(document.querySelectorAll('select'));
      // Find select that has options with Tamil
      for (const sel of selects) {
        const hasTamil = Array.from(sel.options).some(o => o.value === 'Tamil');
        if (hasTamil) {
          sel.value = 'Tamil';
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    });
    await new Promise(r => setTimeout(r, 2500));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'watch_tamil_audio_filtered.png'), fullPage: false });
    console.log('-> Saved watch_tamil_audio_filtered.png');

    // 6. Test Black Clover with Audio: Tamil -> Honest empty state
    console.log('6. Testing Black Clover with Audio: Tamil (Expect honest empty state)...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const bcBtn = btns.find(b => b.textContent.includes('Black Clover') || b.textContent.includes('Naruto'));
      if (bcBtn) bcBtn.click();
    });
    // Search Black Clover
    const searchInput = await page.$('input[placeholder*="Search anime"]');
    if (searchInput) {
      await searchInput.click({ clickCount: 3 });
      await searchInput.type('Black Clover');
      await page.keyboard.press('Enter');
      await new Promise(r => setTimeout(r, 1500));
      // Click first search result dropdown item
      await page.evaluate(() => {
        const item = document.querySelector('button[type="button"] p');
        if (item) item.click();
      });
    }
    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'watch_black_clover_no_tamil.png'), fullPage: false });
    console.log('-> Saved watch_black_clover_no_tamil.png');

    console.log('All browser verifications completed successfully!');
  } catch (err) {
    console.error('Browser verification error:', err);
  } finally {
    await browser.close();
  }
}

runBrowserVerification();
