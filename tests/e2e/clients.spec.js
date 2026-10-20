const { test, expect } = require('@playwright/test');
const API=process.env.ATLAS_E2E_API || 'http://127.0.0.1:8011';
for (const [name, url] of [['React',process.env.ATLAS_REACT_URL || 'http://127.0.0.1:5173'], ['Angular',process.env.ATLAS_ANGULAR_URL || 'http://127.0.0.1:4210']]) {
  test(`${name}: authenticated document → answer → approved ticket`, async ({page}) => {
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url);
    await page.getByLabel('Endereço da API').fill(API);
    await page.getByLabel('Senha',{exact:true}).fill('atlas-local-only');
    await page.getByRole('button',{name:'Entrar no workspace'}).click();
    await expect(page.getByRole('heading',{name:'Pergunte. Verifique. Execute.'})).toBeVisible();
    await page.getByRole('button',{name:'Documentos',exact:true}).click();
    await page.getByLabel('Título do documento').fill(`Política E2E ${name}`);
    await page.getByLabel('Arquivo do documento').setInputFiles({name:`policy-${name}.txt`,mimeType:'text/plain',buffer:Buffer.from(`O incidente P1 recebe primeira resposta em 15 minutos. Ticket exige aprovação humana. Documento ${name}.`)});
    await page.getByRole('button',{name:'Enviar documento',exact:true}).click();
    await expect(page.getByText(`Política E2E ${name}`,{exact:true}).first()).toBeVisible();
    await page.getByRole('button',{name:'Workspace',exact:true}).click();
    await page.getByLabel('Pergunta',{exact:true}).fill('Qual o prazo do incidente P1?');
    await page.getByRole('button',{name:'Enviar pergunta'}).click();
    await expect(page.locator('.answer-text')).toContainText('15 minutos');
    await expect(page.getByRole('region',{name:'Fontes recuperadas'})).toContainText('Política E2E');
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:`../../docs/evidence/${name.toLowerCase()}-desktop.png`,fullPage:true});
    await page.getByLabel('Pergunta',{exact:true}).fill(`/ticket Ticket E2E ${name}`);
    await page.locator('.strategy-control select').selectOption('agent');
    await page.getByRole('button',{name:'Enviar pergunta'}).click();
    await expect(page.getByRole('button',{name:'Revisar ação pendente'})).toBeVisible();
    await page.getByRole('button',{name:'Revisar ação pendente'}).click();
    const card=page.locator('.approval-card').filter({hasText:`Ticket E2E ${name}`});
    await card.getByRole('button',{name:'Aprovar ação'}).click();
    await expect(page.getByText(`Ticket E2E ${name}`,{exact:true}).last()).toBeVisible();
    await page.getByRole('button',{name:'Consumo',exact:true}).click();
    await expect(page.getByRole('heading',{name:/Consumo/})).toBeVisible();
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:`../../docs/evidence/${name.toLowerCase()}-mobile.png`,fullPage:true});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    expect(errors).toEqual([]);
  });
}
for (const [name,url] of [['React',process.env.ATLAS_REACT_URL || 'http://127.0.0.1:5173'],['Angular',process.env.ATLAS_ANGULAR_URL || 'http://127.0.0.1:4210']]) {
  test(`${name}: authentication error, queued cancellation and safe resume`,async({page})=>{
    await page.goto(url);
    await page.getByLabel('Endereço da API').fill(API);
    await page.getByLabel('Senha',{exact:true}).fill('incorrect-password');
    await page.getByRole('button',{name:'Entrar no workspace'}).click();
    await expect(page.getByRole('alert')).toContainText('credenciais inválidas');
    await page.getByLabel('Senha',{exact:true}).fill('atlas-local-only');
    await page.getByRole('button',{name:'Entrar no workspace'}).click();
    await page.getByLabel('Pergunta',{exact:true}).fill('Qual prazo do incidente P1?');
    await page.getByLabel('Estratégia',{exact:true}).selectOption('async');
    await page.getByRole('button',{name:'Enviar pergunta'}).click();
    await page.getByRole('button',{name:'Cancelar execução'}).click();
    await expect(page.getByRole('button',{name:'Retomar execução'})).toBeVisible();
    await page.getByRole('button',{name:'Retomar execução'}).click();
    await expect(page.getByRole('button',{name:'Cancelar execução'})).toBeVisible();
    await page.getByRole('button',{name:'Cancelar execução'}).click();
    await expect(page.getByRole('button',{name:'Retomar execução'})).toBeVisible();
  });
}
