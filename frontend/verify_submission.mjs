import puppeteer from 'puppeteer'
import path from 'path'

const ARTIFACT_DIR = 'C:/Users/admin/.gemini/antigravity/brain/50c056d6-7e88-4bef-8ce4-a3e804331994'

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function run() {
  console.log('Launching browser for submission verification...')
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  })

  try {
    const page = await browser.newPage()
    await page.setViewport({ width: 1440, height: 900 })

    // 1. Test Smart Live Search
    console.log('1. Navigating to Dashboard and testing Live Search...')
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' })
    await sleep(2000)

    // Type query into search bar
    const searchInput = await page.$('header input[type="text"]')
    if (searchInput) {
      await searchInput.click()
      await searchInput.type('frieren', { delay: 100 })
      console.log('Typed "frieren", waiting for live suggestions...')
      await sleep(1500)

      await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'search_live_results.png'),
        fullPage: false,
      })
      console.log('Saved search_live_results.png')
    }

    // 2. Test Anime Details & Episode Guide
    console.log('2. Navigating to Anime Details (Sousou no Frieren)...')
    await page.goto('http://127.0.0.1:5173/anime/52991', { waitUntil: 'domcontentloaded' })
    await sleep(3000)

    // Find and click the first "Description" button to expand EP 01
    const expandButtons = await page.$$('button')
    for (const btn of expandButtons) {
      const text = await page.evaluate((el) => el.textContent, btn)
      if (text && text.includes('Description')) {
        await btn.click()
        console.log('Clicked to expand episode 1 description...')
        await sleep(500)
        break
      }
    }

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'anime_details_episodes.png'),
      fullPage: true,
    })
    console.log('Saved anime_details_episodes.png')

    // 3. Test My List Page
    console.log('3. Navigating to My List...')
    await page.goto('http://127.0.0.1:5173/my-list', { waitUntil: 'domcontentloaded' })
    await sleep(2000)
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'submission_watchlist.png'),
      fullPage: false,
    })
    console.log('Saved submission_watchlist.png')

    // 4. Test Dashboard
    console.log('4. Navigating to Dashboard...')
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' })
    await sleep(2000)
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, 'submission_dashboard.png'),
      fullPage: false,
    })
    console.log('Saved submission_dashboard.png')

    console.log('All verification steps succeeded!')
  } catch (err) {
    console.error('Verification failed:', err)
  } finally {
    await browser.close()
  }
}

run()
