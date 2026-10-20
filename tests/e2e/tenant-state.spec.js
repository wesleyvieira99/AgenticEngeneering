const { test, expect } = require('@playwright/test');

const API = process.env.ATLAS_E2E_API || 'http://127.0.0.1:8011';
const clients = [
  ['React', process.env.ATLAS_REACT_URL || 'http://127.0.0.1:5173'],
  ['Angular', process.env.ATLAS_ANGULAR_URL || 'http://127.0.0.1:4210'],
];

async function login(page, tenant) {
  await page.getByLabel('Endereço da API').fill(API);
  await page.getByLabel('Organização', { exact: true }).selectOption(tenant);
  await page.getByLabel('Senha', { exact: true }).fill('atlas-local-only');
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page.getByLabel('Pergunta', { exact: true })).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Atualizar workspace' }),
  ).toBeEnabled();
}

async function stagePrivateDraft(page, tenant) {
  await page
    .getByLabel('Pergunta', { exact: true })
    .fill(`${tenant} — rascunho privado`);
  await page.getByRole('button', { name: 'Documentos', exact: true }).click();
  await page
    .getByLabel('Título do documento')
    .fill(`${tenant} — arquivo privado`);
  await page.getByLabel('Arquivo do documento').setInputFiles({
    name: `${tenant}-draft.txt`,
    mimeType: 'text/plain',
    buffer: Buffer.from(`Conteúdo sintético privado de ${tenant}.`),
  });
  await expect(
    page.getByRole('button', { name: 'Enviar documento', exact: true }),
  ).toBeEnabled();
}

async function expectCleanDraft(page) {
  await expect(page.getByLabel('Pergunta', { exact: true })).toHaveValue('');
  await page.getByRole('button', { name: 'Documentos', exact: true }).click();
  await expect(page.getByLabel('Título do documento')).toHaveValue('');
  await expect(page.getByLabel('Arquivo do documento')).toHaveValue('');
  await expect(
    page.getByRole('button', { name: 'Enviar documento', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Workspace', exact: true }).click();
}

for (const [name, url] of clients) {
  test(`${name}: private drafts are cleared after logout and expired-session login`, async ({
    page,
  }) => {
    const errors = [];
    const writes = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => {
      if (
        request.method() === 'POST' &&
        /\/api\/(documents|runs)$/.test(request.url())
      ) {
        writes.push(request.url());
      }
    });
    await page.goto(url);
    await login(page, 'acme');
    await stagePrivateDraft(page, 'acme');
    await page
      .getByRole('button', { name: 'Sair do workspace' })
      .first()
      .click();
    await login(page, 'orbit');
    await expectCleanDraft(page);

    await stagePrivateDraft(page, 'orbit');
    // Controlled HTTP failure tests client cleanup; server authentication has separate coverage.
    await page.route('**/api/usage', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Expired test session' }),
      }),
    );
    await page.getByRole('button', { name: 'Atualizar workspace' }).click();
    await expect(
      page.getByRole('button', { name: 'Entrar no workspace' }),
    ).toBeVisible();
    await page.unroute('**/api/usage');
    await login(page, 'acme');
    await expectCleanDraft(page);

    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  });
}
