import puppeteer from 'puppeteer'
import fs from 'fs'
import path from 'path'

const artifactDir = 'C:\\Users\\admin\\.gemini\\antigravity\\brain\\50c056d6-7e88-4bef-8ce4-a3e804331994'

async function run() {
  console.log('Launching browser...')
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  })

  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })

  console.log('Navigating to Dashboard: http://127.0.0.1:5173/ ...')
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 30000 })
  // Wait an extra 3 seconds for animations and trending cards to render
  await new Promise((r) => setTimeout(r, 3000))

  const dashboardImg1 = path.join(artifactDir, 'dashboard.png')
  const dashboardImg2 = path.resolve('public', 'dashboard.png')
  if (!fs.existsSync(path.resolve('public'))) {
    fs.mkdirSync(path.resolve('public'), { recursive: true })
  }

  await page.screenshot({ path: dashboardImg1, fullPage: false })
  await page.screenshot({ path: dashboardImg2, fullPage: false })
  console.log('Saved dashboard screenshot to', dashboardImg1)

  console.log('Navigating to Discover: http://127.0.0.1:5173/discover ...')
  await page.goto('http://127.0.0.1:5173/discover', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await new Promise((r) => setTimeout(r, 3000))

  const discoverImg1 = path.join(artifactDir, 'discover.png')
  const discoverImg2 = path.resolve('public', 'discover.png')

  await page.screenshot({ path: discoverImg1, fullPage: false })
  await page.screenshot({ path: discoverImg2, fullPage: false })
  console.log('Saved discover screenshot to', discoverImg1)

  // Test search: navigate to search query
  console.log('Navigating to Discover Search: http://127.0.0.1:5173/discover?q=Demon%20Slayer ...')
  await page.goto('http://127.0.0.1:5173/discover?q=Demon%20Slayer', { waitUntil: 'domcontentloaded', timeout: 30000 })
  try {
    await page.waitForSelector('.grid a', { timeout: 10000 })
  } catch (e) {
    console.log('Wait for selector timed out, continuing...')
  }
  await new Promise((r) => setTimeout(r, 2500))

  const searchImg1 = path.join(artifactDir, 'discover_search.png')
  const searchImg2 = path.resolve('public', 'discover_search.png')
  await page.screenshot({ path: searchImg1, fullPage: false })
  await page.screenshot({ path: searchImg2, fullPage: false })
  console.log('Saved search screenshot to', searchImg1)

  await browser.close()
  console.log('Screenshots completed successfully!')
}

run().catch((err) => {
  console.error('Error taking screenshots:', err)
  process.exit(1)
})
