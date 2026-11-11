// Capture screenshots for every sketch listed in missing_thumbs.txt (written by build.py).
// Needs dist/ served at localhost:8080 (python3 -m http.server 8080 -d dist).
// Usage: node screenshot.mjs   (set CHROME=/path/to/chrome to use a specific binary)
import fs from 'fs'
import puppeteer from 'puppeteer'

const WAIT_MS = 5000 // let the scene load and animate a bit before capturing

const jobs = fs.readFileSync('missing_thumbs.txt', 'utf8').trim().split('\n')
  .filter(Boolean).map(line => line.split('\t'))
fs.mkdirSync('screenshots', { recursive: true })

const launch = () => puppeteer.launch({
  headless: 'shell',
  executablePath: process.env.CHROME,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'],
})
for (const [href, name] of jobs) {
  // fresh browser per sketch so one crashing sketch can't take down the rest
  const browser = await launch()
  const page = await browser.newPage()
  await page.setViewport({ width: 800, height: 600 })
  try {
    await page.goto(`http://localhost:8080/${href}`, { waitUntil: 'load', timeout: 30000 })
    await new Promise(r => setTimeout(r, WAIT_MS))
    // hide debug GUIs / stats overlays so thumbnails show just the sketch
    await page.addStyleTag({ content: '.dg, .lil-gui, .rs-base, #stats { display: none !important; }' })
    await page.screenshot({ path: `screenshots/${name}`, type: 'jpeg', quality: 80 })
    console.log('ok  ', href)
  } catch (err) {
    console.log('FAIL', href, err.message)
  }
  await browser.close().catch(() => {})
}
