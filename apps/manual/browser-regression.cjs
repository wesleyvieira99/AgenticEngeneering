/** Focused manual regression. Uses the monorepo's pinned Playwright installation. */
const { chromium } = require('../../tests/e2e/node_modules/playwright');
const { createServer } = require('node:http');
const { readFile } = require('node:fs/promises');
const { resolve, extname } = require('node:path');
const assert = require('node:assert/strict');
const directory = resolve(__dirname, 'dist');
const types = { '.html': 'text/html', '.js': 'application/javascript', '.mjs': 'application/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml' };
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    const path = resolve(directory, '.' + (url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname)));
    if (!path.startsWith(directory + '/')) { res.writeHead(403); res.end(); return; }
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': types[extname(path)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/#/inicio`);
    await page.locator('h1').waitFor();
    await page.locator('#search-button').click();
    await page.locator('#global-search').fill('vetores');
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => !document.querySelector('#search-dialog').open);
    assert.equal(await page.locator('#search-dialog').evaluate(el => el.open), false, 'Escape must close a non-empty search dialog');
    await page.locator('#search-button').click();
    await page.locator('#global-search').fill('aprovação');
    await page.evaluate(() => { location.hash = '#/capitulo/seguranca'; });
    await page.waitForFunction(() => location.hash === '#/capitulo/seguranca' && !document.querySelector('#search-dialog').open);
    await page.getByRole('heading', { level: 1, name: 'Permissões fora do prompt' }).waitFor();
    assert.equal(await page.locator('#search-dialog').evaluate(el => el.open), false, 'Route navigation must dismiss stale search UI');
    await page.locator('#search-button').click();
    await page.locator('#global-search').fill('idempotência');
    await page.locator('#search-results a').first().click();
    await page.waitForFunction(() => !document.querySelector('#search-dialog').open);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'Mobile page must not overflow horizontally');
    assert.deepEqual(errors, [], 'No uncaught browser errors');
    console.log('PASS: Escape, hash navigation, search result dismissal, mobile width, and browser errors.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
