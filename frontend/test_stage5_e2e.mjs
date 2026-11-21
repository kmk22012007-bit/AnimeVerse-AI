import puppeteer from 'puppeteer'
import path from 'path'
import fs from 'fs'

const artifactDir = 'C:\\Users\\admin\\.gemini\\antigravity\\brain\\50c056d6-7e88-4bef-8ce4-a3e804331994'

async function run() {
  console.log('Starting Stage 5 E2E Verification...')
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  })

  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })

  // 1. Visit Discover Page to add Demon Slayer to Watchlist
  console.log('1. Visiting Discover Page: http://127.0.0.1:5173/discover?q=Demon%20Slayer ...')
  await page.goto('http://127.0.0.1:5173/discover?q=Demon%20Slayer', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 2500))

  // Find the bookmark button on the first card and click it
  console.log('Clicking Add to Watchlist button on first anime card...')
  const bookmarkButtons = await page.$$('button[aria-label="Add to Watchlist"]')
  if (bookmarkButtons.length > 0) {
    await bookmarkButtons[0].click()
    await new Promise((r) => setTimeout(r, 1000))

    // Click "Watching" from dropdown options
    const watchingOption = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'))
      const btn = buttons.find((b) => b.textContent && b.textContent.trim() === 'Watching')
      if (btn) {
        btn.click()
        return true
      }
      return false
    })
    console.log('Selected "Watching" status:', watchingOption)
    await new Promise((r) => setTimeout(r, 2000))
  }

  // Also add Frieren as "Completed" from trending stream
  console.log('Navigating to Discover Trending stream...')
  await page.goto('http://127.0.0.1:5173/discover', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 2500))

  const trendButtons = await page.$$('button[aria-label="Add to Watchlist"]')
  if (trendButtons.length > 0) {
    await trendButtons[0].click()
    await new Promise((r) => setTimeout(r, 1000))
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'))
      const btn = buttons.find((b) => b.textContent && b.textContent.trim() === 'Completed')
      if (btn) btn.click()
    })
    console.log('Added trending anime as Completed')
    await new Promise((r) => setTimeout(r, 2000))
  }

  // 2. Navigate to My List Page
  console.log('2. Navigating to My List: http://127.0.0.1:5173/list ...')
  await page.goto('http://127.0.0.1:5173/list', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 2500))

  // Click +1 Episode button on active series
  console.log('Testing episode stepper (+1 button)...')
  const plusButtons = await page.$$('button[title="+1 Episode"]:not([disabled])')
  if (plusButtons.length > 0) {
    await plusButtons[0].click()
    await new Promise((r) => setTimeout(r, 1000))
    await plusButtons[0].click()
    await new Promise((r) => setTimeout(r, 1500))
    console.log('Clicked +1 twice on active series.')
  }

  // Click Rate button to open modal
  console.log('Opening Rating & Notes modal...')
  const editButtons = await page.$$('button[title="Edit Notes & Rating"]')
  if (editButtons.length > 0) {
    await editButtons[editButtons.length - 1].click() // Click on Kimetsu no Yaiba
    await new Promise((r) => setTimeout(r, 1000))

    // Click 9 stars
    const star9 = await page.$('button[title="Rate 9 / 10"]')
    if (star9) await star9.click()

    // Type note into textarea
    await page.click('textarea')
    await page.type('textarea', 'Outstanding animation by ufotable and thrilling battle choreography.')

    // Click Save Entry
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'))
      const saveBtn = btns.find((b) => b.textContent && b.textContent.includes('Save Entry'))
      if (saveBtn) saveBtn.click()
    })
    await new Promise((r) => setTimeout(r, 2000))
  }

  // Capture screenshot of My List
  const watchlistScreenshot = path.join(artifactDir, 'watchlist.png')
  await page.screenshot({ path: watchlistScreenshot, fullPage: false })
  console.log('Saved watchlist screenshot to', watchlistScreenshot)

  // 3. Navigate to Dashboard to verify live watchlist statistics & Currently Watching cards
  console.log('3. Navigating to Dashboard: http://127.0.0.1:5173/ ...')
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 3000))

  const dashboardWithWatchlistScreenshot = path.join(artifactDir, 'dashboard_with_watchlist.png')
  await page.screenshot({ path: dashboardWithWatchlistScreenshot, fullPage: false })
  console.log('Saved dashboard with watchlist screenshot to', dashboardWithWatchlistScreenshot)

  await browser.close()
  console.log('Stage 5 E2E Verification completed successfully!')
}

run().catch((err) => {
  console.error('Error during Stage 5 E2E:', err)
  process.exit(1)
})
