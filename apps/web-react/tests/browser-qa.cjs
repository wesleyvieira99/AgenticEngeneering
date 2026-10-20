const path = require('node:path');
const repo = path.resolve(__dirname, '../../..');
const api = process.env.ATLAS_E2E_API || 'http://127.0.0.1:8011';
const { chromium } = require(
  path.join(repo, 'tests/e2e/node_modules/playwright'),
);
const { writeFile } = require('node:fs/promises');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const checks = [];
  try {
    for (const [name, url] of [
      ['react', process.env.ATLAS_REACT_URL || 'http://127.0.0.1:5173'],
      ['angular', process.env.ATLAS_ANGULAR_URL || 'http://127.0.0.1:4210'],
    ]) {
      const page = await browser.newPage({
        viewport: { width: 1440, height: 900 },
      });
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.goto(url);
      await page.getByLabel('Endereço da API').waitFor();
      await page.keyboard.press('Tab');
      assert.equal(
        await page
          .locator('.skip-link')
          .evaluate(
            (el) =>
              document.activeElement === el &&
              getComputedStyle(el).clipPath === 'none',
          ),
        true,
      );
      await page.getByLabel('Endereço da API').fill(api);
      await page.getByLabel('Senha', { exact: true }).fill('atlas-local-only');
      await page.getByRole('button', { name: 'Entrar no workspace' }).click();
      await page
        .getByRole('heading', { name: 'Pergunte. Verifique. Execute.' })
        .waitFor();
      await page
        .getByRole('button', { name: 'Documentos', exact: true })
        .click();
      await page.locator('.record').first().waitFor();
      const dates = await page.locator('.record p').allTextContents();
      assert.equal(
        dates.some((s) => s.includes('1970')),
        false,
      );
      await page
        .getByRole('button', { name: 'Histórico', exact: true })
        .click();
      const history = page
        .locator('tbody tr')
        .filter({ hasText: 'incidente P1' })
        .filter({ hasText: 'Concluída' })
        .first();
      const first = history.getByRole('button', { name: /Abrir execução/ });
      await first.waitFor();
      let sourceAnchor = false;
      if (await first.count()) {
        await first.click();
        await page.locator('.answer-text').waitFor();
        const anchor = page.locator('.answer-text a').first();
        await anchor.waitFor();
        if (await anchor.count()) {
          const href = await anchor.getAttribute('href');
          assert.equal(await page.locator(href).count(), 1);
          sourceAnchor = true;
        }
      } else
        await page
          .getByRole('button', { name: 'Workspace', exact: true })
          .click();
      await page
        .getByRole('button', { name: 'Alternar tema', exact: true })
        .click();
      await page.waitForFunction(
        () => document.documentElement.dataset.theme === 'dark',
      );
      await page.waitForFunction(
        () => !document.querySelector('.page-heading button')?.disabled,
      );
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: path.join(repo, `docs/evidence/${name}-dark.png`),
        fullPage: true,
        animations: 'disabled',
      });
      await page.setViewportSize({ width: 390, height: 844 });
      const widths = [];
      for (const label of [
        'Workspace',
        'Documentos',
        'Aprovações',
        'Histórico',
        'Consumo',
        'Configurações',
      ]) {
        await page.getByRole('button', { name: label, exact: true }).click();
        widths.push({
          view: label,
          viewport: 390,
          document: await page.evaluate(
            () => document.documentElement.scrollWidth,
          ),
        });
      }
      assert.equal(
        widths.every((item) => item.document <= 390),
        true,
        JSON.stringify(widths),
      );
      await page.getByRole('button', { name: 'Consumo', exact: true }).click();
      await page
        .getByRole('heading', { name: 'Consumo sob controle.' })
        .waitFor();
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: path.join(repo, `docs/evidence/${name}-mobile-dark.png`),
        fullPage: true,
        animations: 'disabled',
      });
      assert.deepEqual(await page.evaluate(() => Object.keys(localStorage)), [
        'atlas-theme',
      ]);
      await page
        .getByRole('button', { name: 'Sair do workspace', exact: true })
        .click();
      await page.getByRole('button', { name: 'Entrar no workspace' }).waitFor();
      await page.getByLabel('Endereço da API').fill('http://127.0.0.1:59999');
      await page.getByLabel('Senha', { exact: true }).fill('atlas-local-only');
      await page.getByRole('button', { name: 'Entrar no workspace' }).click();
      await page.getByRole('alert').waitFor();
      assert.deepEqual(errors, []);
      checks.push({
        framework: name,
        keyboard_skip: true,
        unix_dates: dates.length > 0,
        source_anchor: sourceAnchor,
        dark_theme: true,
        mobile_views: widths,
        mobile_logout: true,
        storage_only_theme: true,
        unavailable_api_error: true,
        page_errors: errors,
      });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  await writeFile(
    path.join(repo, 'docs/evidence/client-visual-qa.json'),
    JSON.stringify(
      {
        recorded_at: new Date().toISOString(),
        api,
        mode: 'deterministic',
        checks,
      },
      null,
      2,
    ) + '\n',
  );
  console.log(JSON.stringify(checks, null, 2));
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
