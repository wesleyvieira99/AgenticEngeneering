# Atlas: dois clientes, um contrato

Verificado em **20/10/2026**. Os clientes React e Angular são aplicações independentes: cada um possui dependências fixadas, lockfile, build e ponto de entrada. Ambos consomem a API FastAPI definida em [`packages/contracts/http.md`](../packages/contracts/http.md). Nenhum precisa de uma chave de provedor no navegador.

## O que está implementado

| Jornada | Interface | Operação real |
|---|---|---|
| Login e tenant | Organização, usuário, senha, endereço da API | `POST /api/auth/login`; tenant derivado do token no servidor |
| Ingestão | Documentos → arquivo `.txt`/`.md` | Leitura UTF-8 e `POST /api/documents` com `{title,content}` |
| Perguntas | Workspace → pergunta e estratégia | `POST /api/runs` seguido de `GET /api/runs/{id}/events` |
| Evidência | Fontes recuperadas e links na resposta | IDs de chunks retornados pela API; sem fontes inventadas |
| Ação | `/ticket Título` com estratégia Agente | Preparação de ação → aprovação → ticket persistido |
| Revisão humana | Aprovações → Aprovar / Rejeitar | `POST /api/approvals/{id}/approve` ou `/reject` |
| Cancelamento | Cancelar execução | `POST /api/runs/{id}/cancel`; só depois desconecta a observação |
| Recuperação | Retomar execução | `POST /api/runs/{id}/resume`; conflitos de segurança são exibidos |
| Histórico e comparação | Histórico | Últimas execuções retornadas pela API, com estratégia, tokens, custo e latência |
| Memória | Checkbox inicialmente desmarcado; Excluir memória | `memory_enabled` explícito; `DELETE /api/conversations/{id}` |
| Consumo | Consumo | `GET /api/usage`; dados persistidos, conclusões e custo por tarefa concluída |
| Governança | Configurações | `GET` / `PUT /api/settings`; autorização admin no servidor |
| Preferências | Alternar tema | Somente tema em `localStorage`; sem credenciais ou respostas |

`successful_runs` conta execuções com estado `completed`, incluindo abstenções. `cost_per_success_usd` é calculado no backend como custo cumulativo do tenant dividido por esse número; o numerador inclui falhas, e o resultado é `null` quando não há conclusões. O cliente exibe “—” para esse caso. O painel também mostra `active_runs`, `reserved_tokens` e `reserved_cost_usd` retornados pela API; reservas são compromissos de admissão, não cobrança confirmada. Essa conclusão operacional não comprova correção ou qualidade sem avaliação específica.

Todos os estados vazios são estados vazios: não são preenchidos com métricas demonstrativas. A barra superior mostra o modo declarado por `/api/health`. O modo `deterministic` permite testar os fluxos de engenharia; não constitui validação de inferência de um LLM real. A simulação pedagógica pertence ao manual e não substitui o backend dos clientes.

## Reproduzir localmente

Pré-condições: Node.js 24.x compatível com as versões fixadas; npm; API iniciada conforme o README. Nesta verificação foi usado Node **24.3.0** com npm **11.4.2**. Angular 21 suporta esta versão de Node; Angular 22 exige uma revisão mais recente, por isso não foi escolhido automaticamente apenas por ser mais novo.

Execute a partir da raiz do repositório, em terminais distintos:

```sh
cd apps/web-react
npm ci
npm run dev
```

Abra `http://127.0.0.1:5173`. Para encerrar, use Ctrl+C no terminal do servidor.

```sh
cd apps/web-angular
npm ci
npm run dev
```

Abra `http://127.0.0.1:4200`. Para encerrar, use Ctrl+C. Se a porta já pertencer a outra aplicação, preserve esse processo e escolha outra:

```sh
npm run dev -- --port 4210
```

Inclua a origem alternativa em `ATLAS_CORS_ORIGINS` antes de iniciar a API. CORS é controle de origem do navegador; não substitui autenticação nem isolamento entre tenants.

Na tela de login, informe **Endereço da API**. O padrão é `http://localhost:8000`; uma API executada em outra porta pode usar, por exemplo, `http://127.0.0.1:8010`. Escolha `acme` ou `orbit`, usuário `admin`, e a senha de desenvolvimento configurada no servidor. `atlas-local-only` é o padrão público exclusivamente de desenvolvimento, não uma credencial de produção.

Configuração permanente de origem:

- React: copie [`.env.example`](../apps/web-react/.env.example) para `.env.local`, ajuste `VITE_API_URL` e reinicie o Vite. Variáveis `VITE_*` são públicas; **nunca** coloque nelas segredos.
- Angular: ajuste [`public/config.js`](../apps/web-angular/public/config.js), que define `window.ATLAS_API_URL`. O arquivo vai para o build e pode ser substituído na hospedagem sem recompilar. Ele contém apenas a origem pública da API.
- Ambos permitem sobrescrever o endereço na tela de login, sem persistir esse valor junto a credenciais. URLs com credenciais embutidas, fragmentos ou query strings são recusadas.

Builds e testes:

```sh
npm --prefix apps/web-react test
npm --prefix apps/web-react run build
npm --prefix apps/web-angular test
npm --prefix apps/web-angular run build
```

Saídas: `apps/web-react/dist/` e `apps/web-angular/dist/browser/`. São arquivos estáticos, mas os fluxos do Atlas exigem a API separada. Não publique um frontend apontando para `localhost` e declare o backend implantado: `localhost` no navegador é o computador do visitante. Em produção use HTTPS para ambos, configure CORS para origens exatas, autenticação apropriada e o endereço público da API.

## Percurso verificável

1. Entre em `acme`. Em **Documentos**, envie um `.md` UTF-8 contendo uma política sintética. O título é opcional; o nome do arquivo é usado quando vazio. Um arquivo acima de 1 MiB, sem conteúdo, com UTF-8 inválido ou extensão diferente é rejeitado antes do envio. A API continua sendo responsável pela validação de segurança.
2. Volte ao **Workspace**. Selecione **RAG**, pergunte sobre uma informação existente no arquivo e envie. Confira a transição de estado, a resposta, a fonte e os eventos. Um `[ID-do-chunk]` retornado na resposta se transforma em um link `[1]` somente se o ID existir no array `sources`. O texto de citações desconhecidas permanece texto; o cliente não inventa uma evidência.
3. Verifique o ID do trecho no painel de fontes. Para fontes recuperadas por busca híbrida, `score` é **ranking RRF**, não probabilidade de acerto nem similaridade cosseno. No CAG, os trechos pertencem ao contexto em cache e o cliente mostra “sem score RRF”, pois o zero desse caminho não representa ranking.
4. Use a mesma pergunta com **CAG** e abra **Histórico** para comparar registros reais de estratégias, tokens, custo e latência. Fazer essa comparação no modo determinístico não mede qualidade nem latência de um provedor real.
5. Escolha **Agente** e envie `/ticket Revisar política de reembolso`. Abra **Aprovações**, confira a ação e seus argumentos e aprove. O ticket aparece em **Tickets persistidos** após a resposta da API. `/tickets` consulta os tickets pela jornada de ferramenta.
6. Para observar cancelamento com previsibilidade, escolha **Assíncrono** sem worker ativo. A execução permanece na fila; **Cancelar execução** solicita cancelamento no servidor. **Retomar execução** solicita nova tentativa, sujeita aos limites de idempotência e segurança do backend. Com worker ativo, o cancelamento pode disputar com uma conclusão legítima; o estado persistido é a autoridade.
7. Habilite **Usar memória desta conversa** antes de uma pergunta. O servidor devolve um `conversation_id`, que será enviado nas próximas perguntas apenas enquanto o consentimento continuar habilitado. **Excluir memória** pede confirmação e remove a memória pelo endpoint; a auditoria de execuções possui retenção própria. Desmarcar consentimento não apaga retrospectivamente o que já foi persistido.
8. Saia e entre em `orbit`. O navegador limpa dados da sessão anterior, incluindo pergunta, título e arquivo selecionado ainda não enviado. O mesmo reset ocorre quando um 401 encerra a sessão. O servidor também precisa negar acesso a IDs do outro tenant — esconder elementos no frontend não constitui isolamento.

## Mapa de componentes

| Responsabilidade | React | Angular |
|---|---|---|
| Montagem | [`src/main.tsx`](../apps/web-react/src/main.tsx), `createRoot` | [`src/main.ts`](../apps/web-angular/src/main.ts), `bootstrapApplication` |
| Shell, navegação, tema | `App` em [`App.tsx`](../apps/web-react/src/App.tsx) | `AppComponent` + [`app.component.html`](../apps/web-angular/src/app/app.component.html) |
| Login | `Login`: estado local de formulário | `AppComponent`: `FormsModule` e `ngModel` |
| Chat e envio | `Workspace`, `Answer` | Bloco `@case ('workspace')` e métodos do componente |
| Fontes e auditoria | `Sources`, `Inspector` | [`InspectorComponent`](../apps/web-angular/src/app/inspector.component.ts) com `input<Run|null>` |
| Documentos | `Documents`: estado local de arquivo/título | Bloco `@case ('documents')`, `fileChanged` e `upload` |
| Aprovações e tickets | `Approvals` | Bloco `@case ('approvals')` |
| Comparação | `History` | Bloco `@case ('history')` |
| Consumo e limites | `UsageView`, `Settings`, `Stat` | Blocos `usage` / `settings`, `draftLimits` |
| Ícones | `Icon`: SVG decorativo | [`IconComponent`](../apps/web-angular/src/app/icon.component.ts), standalone |
| Adaptador reativo | `useSyncExternalStore(store.subscribe, store.snapshot)` | [`AtlasService`](../apps/web-angular/src/app/atlas.service.ts), serviço injetável com `signal` |
| Estado de transporte | [`state.ts`](../apps/web-react/src/state.ts) | [`state.ts`](../apps/web-angular/src/app/state.ts) |
| HTTP, SSE e tipos | [`api.ts`](../apps/web-react/src/api.ts) | [`api.ts`](../apps/web-angular/src/app/api.ts) |

`App` mantém apenas preferências de navegação e campos de formulário. `AtlasStore` mantém estado de sessão, documentos, execuções, aprovações, tickets, limites e erros. `AtlasApi` trata HTTP e streaming. Essa separação permite testar transporte sem renderizar React ou Angular.

Os dois diretórios distribuem uma cópia equivalente de `api.ts` e `state.ts` para permanecerem compiláveis isoladamente. O teste de paridade no React compara as cópias; a única diferença permitida é a extensão do import, devido ao executor Node dos testes. Não há um backend exclusivo de React ou um contrato alternativo para Angular. Em uma evolução do monorepo, esse código pode virar um pacote TypeScript versionado; aqui a duplicação é pequena, explícita e verificada.

## React: estado, renderização e eventos

[`App.tsx`](../apps/web-react/src/App.tsx) usa `useSyncExternalStore` porque o transporte é um store externo ao React. `subscribe` adiciona um listener e retorna a função que o remove. `snapshot` retorna a mesma referência de estado até uma alteração. `patch` cria outro objeto e notifica listeners; assim o React detecta a nova versão sem mutações invisíveis.

Os campos `question`, `strategy`, `page` e `dark` usam `useState`. Seus valores são controlados pelo React: `value`/`checked` apresentam o estado; `onChange` atualiza o estado. `onSubmit` chama `preventDefault()` para impedir navegação do documento e então executa `store.send`. Retirar `preventDefault()` interromperia a aplicação SPA e perderia o bearer mantido em memória.

`Sources` recebe apenas o `Run` atual. Não faz outra busca e não gera títulos. `Answer` examina citações no texto e verifica o vínculo com `run.sources` antes de criar o link. React escapa o texto por padrão; nenhum conteúdo vindo do modelo ou documento é inserido com `dangerouslySetInnerHTML`.

`Settings` mantém uma cópia editável dos limites. Alterar um campo não chama imediatamente a API; **Salvar limites** envia o objeto completo. A identificação `role === 'admin'` melhora a interface, mas a autorização real continua no endpoint.

## Angular: signals, DI e templates

[`atlas.service.ts`](../apps/web-angular/src/app/atlas.service.ts) cria uma instância de `AtlasStore` por aplicação. `signal(this.store.state)` é a ponte reativa: quando o store emite uma alteração, `state.set(...)` notifica consumidores. `DestroyRef` remove a assinatura e aborta a observação ao destruir o serviço. Não há dependência obrigatória de Zone.js; Angular 21 usa o fluxo de atualização compatível com signals.

[`app.component.ts`](../apps/web-angular/src/app/app.component.ts) obtém o serviço com `inject`. Os `computed` de execução, página selecionada e contagem de aprovações derivam valores de signals; não criam cópias independentes que poderiam divergir. `effect` limpa campos privados quando a sessão muda, cuida de preferências externas, como `document.documentElement.dataset` e `localStorage`, e sincroniza o rascunho de limites apenas quando o objeto de limites é substituído.

No template, `[(ngModel)]` conecta campos a valores de formulário. `(ngSubmit)` entrega a ação ao store. `@if` representa estados vazios e autenticados; `@switch` escolhe a página; `@for (...; track id)` preserva a identidade das linhas quando a API atualiza os arrays. Retirar uma identidade estável de `track` pode recriar DOM desnecessariamente e perder foco.

`InspectorComponent` recebe `Run|null` por `input`. Ele mostra o mesmo contrato das fontes e eventos do React. Interpolação `{{ ... }}` é texto escapado; não há uso de `innerHTML` para respostas, documentos ou auditoria.

## HTTP e autenticação, bloco por bloco

Leia o bloco real em [`api.ts`](../apps/web-react/src/api.ts), classe `AtlasApi`:

1. O construtor remove uma barra final da origem. O cliente acrescenta `/api` e caminhos definidos no contrato; IDs usados em paths passam por `encodeURIComponent`.
2. `request<T>` chama `fetch` com timeout de 15 segundos nas operações JSON. `T` oferece tipagem estática; não é validação de segurança em runtime. Os contratos Pydantic validam as entradas no servidor.
3. `Accept: application/json` declara o formato esperado. `Content-Type` é incluído quando há corpo JSON. O bearer é enviado somente no header `Authorization`; não aparece em URL, query string nem armazenamento persistente.
4. `assertResponse` verifica `response.ok`. Quando existe `{detail: ...}`, o detalhe acompanha o status HTTP. Respostas HTML de proxies não são apresentadas como HTML executável nem tratadas como sucesso.
5. A resposta `204` não é parseada como JSON. Os demais retornos esperam JSON válido; conteúdo inesperado gera falha visível.
6. `post` serializa explicitamente o objeto. O cliente não acrescenta `tenant` às operações de recurso: a organização vem da identidade validada pelo backend.

O token vive em `AtlasApi.token` e no estado da sessão, em memória. Recarregar a página pede login de novo. **Sair do workspace** aborta o stream, incrementa a geração da sessão e apaga dados locais da sessão. Uma resposta GET iniciada antes do logout é descartada quando chega depois; o teste de corrida reproduz esse caso. Os campos dos componentes também são reiniciados na mudança de token, inclusive após um 401, para que um arquivo mantido em memória não possa ser enviado pela próxima organização.

Segurança de frontend não elimina risco de XSS. O projeto evita renderização de HTML externo, mas um ambiente de produção ainda precisa de política CSP, revisão de dependências e autenticação de produção. Tokens, passwords e conteúdo de documentos não devem ser enviados a serviços analíticos do navegador.

## Streaming: o mecanismo real

A requisição tem duas etapas: `POST /runs` cria uma execução e retorna seu ID; `GET /runs/{id}/events` observa essa execução. Desconectar a observação não cancela o trabalho persistido. Por isso existe um endpoint explícito de cancelamento.

`EventSource` nativo não aceita headers de autorização personalizados em sua interface padrão. Aqui usamos `fetch` com `Authorization` e `ReadableStream`, mantendo o formato SSE:

```text
event: token
data: {"text":"trecho"}

```

Leia `consumeSSE` e `createSSEParser` em [`api.ts`](../apps/web-react/src/api.ts):

1. Verificar status HTTP evita interpretar uma falha de autenticação como token.
2. Verificar `Content-Type: text/event-stream` detecta proxies ou rotas incorretas.
3. `body.getReader()` oferece blocos de bytes. Blocos de rede **não** coincidem obrigatoriamente com caracteres, linhas ou eventos.
4. `TextDecoder('utf-8', {fatal:true})` com `{stream:true}` preserva caracteres de vários bytes quando chegam divididos. Sem essa opção, caracteres como `ç` ou emojis podem ser corrompidos.
5. O parser acumula texto até a linha em branco que termina um evento, aceitando LF e CRLF. Comentários de heartbeat são ignorados. Múltiplas linhas `data:` são combinadas antes do parse JSON.
6. Cada evento é encaminhado para `AtlasStore.observe`. `token` acrescenta texto; `sources` substitui as evidências; `usage` atualiza medição; `status` atualiza a etapa; `done` substitui o resultado parcial pelo registro completo.
7. Eventos diferentes de `token` compõem a trilha visível. Eles são eventos da aplicação, sem exposição de cadeia de pensamento privada.
8. O reader é cancelado e liberado em `finally`. Buffers incompletos acima de 2 MiB são rejeitados. Um frame sem terminador no fim da conexão é descartado, em vez de ser inventado como evento completo.
9. Se a conexão cair ou encerrar antes do resultado, o cliente consulta `GET /runs/{id}` até 30 vezes com intervalo de um segundo e timeout por consulta. Ele **não** repete o POST criador. Depois do limite de observação, o botão **Atualizar execução** permite consultar novamente. Um trabalho assíncrono pode continuar no servidor.

O backend atual envia eventos persistidos desde o início de cada observação. O cliente limpa o buffer da visualização antes de reabrir o stream para não duplicar tokens. `done` e a reconciliação final por GET são a autoridade. Para uma futura implementação com `Last-Event-ID`, atualize ambos os lados do contrato e teste reentrega antes de mudar essa regra.

## Erros e concorrência

| Situação | Comportamento | Como verificar |
|---|---|---|
| API indisponível | Login mostra erro; sem dados substitutos | Pare a API e envie o formulário |
| 401 | Limpa sessão e pede novo login | Token inválido/expirado |
| 403 | Mostra erro de permissão | Execute ação com papel sem autorização |
| 409 | Mostra conflito; não repete automaticamente | Tente retomada de ação que já tem aprovação vinculada |
| 422 | Mostra detalhe de validação | Configure limites fora do contrato |
| 429 | Mostra quota/rate limit; não oculta falha | Atinja um limite em ambiente de teste |
| SSE interrompido | Reconcilia com GET; não duplica POST | Teste unitário de queda da conexão |
| Logout durante GET | Descarta resposta antiga | Teste de geração de sessão |
| Logout durante leitura de arquivo | Não envia arquivo na sessão seguinte | Teste de upload atrasado |
| Troca de tenant ou 401 com rascunho | Limpa pergunta, título e arquivo selecionado | Regressões de navegador nos dois frameworks |
| Seleção de execuções fora de ordem | A seleção mais recente permanece visível | GETs resolvidos em ordem invertida |
| Cancelamento durante polling | Aborta observação sem erro de rede fictício | AbortSignal controlado no teste |
| Documento com texto HTML | Exibe como texto, sem executar | Documento de teste contendo tags |

`epoch` é a geração da sessão, `selection` identifica a seleção da execução e `observation` é a geração do stream. Uma callback só atualiza o resultado selecionado se suas gerações ainda forem atuais. Cancelamento, retomada ou aprovação que terminem depois da seleção de outra execução não substituem a escolha nova. Um contador de operações pendentes impede que uma resposta antiga limpe prematuramente `busy`. `AbortController` reduz trabalho desnecessário, mas a verificação de geração continua necessária porque nem toda operação já concluída pode ser “desfeita” por abort.

As alterações de estado usam objetos novos; arrays de eventos são substituídos. O backend protege orçamento, autorização e idempotência mesmo que o usuário contorne botões desabilitados. Não use o estado `busy` como garantia de concorrência global.

## Acessibilidade e comportamento visual

O visual usa fontes do sistema, superfícies discretamente translúcidas, contraste entre texto e fundo, bordas leves e uma paleta azul neutra. Não há fontes externas, imagens remotas ou dependência de serviço pago para montar a interface. O tema claro/escuro funciona nos dois clientes.

Há skip link, labels associados a inputs, botões com nomes acessíveis, estados de erro com `role="alert"`, avisos com `role="status"`, foco visível e suporte a `prefers-reduced-motion`. A navegação transforma-se em uma faixa horizontal no mobile; cards e inspetor passam a uma coluna. Tabelas têm rolagem dentro do próprio contêiner. O botão de logout permanece disponível também no mobile.

O texto que chega token a token não é anunciado inteiro por um live region para evitar repetição constante em leitores de tela. Estados e falhas são anunciados; a resposta final permanece navegável como texto. Uma auditoria formal WCAG com usuários e tecnologias assistivas ainda é uma etapa separada dos testes de layout automatizados.

## Evidências e limites da validação

Os testes de transporte usam respostas sintéticas controladas para verificar fragmentação de bytes, parsing, headers e falhas — isso está explicitamente limitado ao transporte. A verificação E2E do projeto exercita a API real em modo determinístico. Isso comprova o fluxo cliente → API → persistência → streaming, não uma chamada a provedor externo.

Verificação em 20/10/2026: **15 testes React e 5 testes Angular passaram**, os dois builds de produção concluíram e `npm audit --omit=dev` reportou zero vulnerabilidades para dependências de produção. Isso não certifica ausência de vulnerabilidades.

A revisão adicional em Chromium passou para os seis painéis a 390 × 844 e desktop a 1440 × 900, incluindo tema escuro, foco do skip link, links de fontes reais, datas Unix, logout mobile e erro de API indisponível. Evidência: [`client-visual-qa.json`](evidence/client-visual-qa.json), capturas [React escuro](evidence/react-dark.png), [Angular escuro](evidence/angular-dark.png), [React mobile](evidence/react-mobile-dark.png), [Angular mobile](evidence/angular-mobile-dark.png).

Para reproduzir essa revisão, instale `npm --prefix tests/e2e ci`, mantenha API e os dois frontends ativos e execute o E2E principal para criar os documentos/execuções de incidente P1. Depois rode `npm --prefix apps/web-react run test:browser`. As variáveis `ATLAS_E2E_API`, `ATLAS_REACT_URL` e `ATLAS_ANGULAR_URL` permitem alterar endpoints. O script faz leituras e login, verifica erro em uma origem local indisponível e grava capturas/evidências; ele não simula respostas da API.

As duas regressões de navegador em [`tenant-state.spec.js`](../tests/e2e/tenant-state.spec.js) passaram: cada framework troca de tenant após logout explícito e após um 401 controlado, verificando que nenhum rascunho ou arquivo migra para a próxima sessão e que nenhuma escrita de documento/execução ocorre. Login e leituras usam a API real; somente a resposta 401 dessa regressão é injetada para testar a limpeza do cliente, não a autenticação do servidor.

Testes locais dos clientes: `apps/web-react/tests/api.test.mjs`, `state.test.mjs` e `apps/web-angular/tests/api.test.mjs`. Incluem paridade das cópias, ausência de bearer em URLs, descarte de resposta atrasada de tenant, seleção concorrente de execuções, cancelamento durante polling, origem de health e reconciliação sem repetição de efeitos. Os builds AOT/TypeScript verificam o código real de ambos os frameworks; não apenas HTML estático com um nome de framework.

São limites explícitos desta versão: sessão somente em memória; logout não revoga retroativamente o token no servidor; upload apenas UTF-8 `.txt`/`.md`; sem PDF/OCR no navegador; sem edição simultânea de conversa; observação com janela limitada; navegação interna sem URLs por tela; histórico limitado pelo endpoint; sem certificação formal de acessibilidade. As garantias de aprovação, política de retenção e custo dependem da implementação e do modo configurado no backend.

## Versões e fontes primárias

| Componente | Versão fixada |
|---|---|
| React / React DOM | 19.3.1 |
| Tipos React / React DOM | 19.3.0 |
| Vite | 8.3.4 |
| Plugin React para Vite | 6.1.2 |
| Angular core / common / compiler / forms / platform-browser | 21.2.25 |
| Angular CLI / build | 21.2.27 |
| Angular compiler-cli | 21.2.25 |
| TypeScript | 5.9.3 |
| RxJS | 7.8.2 |
| tslib | 2.8.1 |

Versões foram verificadas no registro npm e fixadas nos manifests e lockfiles em 20/10/2026. APIs e compatibilidade foram conferidas nas fontes oficiais:

- [React: Quick Start](https://react.dev/learn) — componentes, estado e eventos.
- [React: useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore) — assinatura do store externo.
- [Angular: compatibilidade de versões](https://angular.dev/reference/versions) — Node, TypeScript e RxJS.
- [Angular: signals](https://angular.dev/guide/signals) — signals, computed e effect.
- [Angular: bootstrapApplication](https://angular.dev/api/platform-browser/bootstrapApplication) — bootstrap de componente standalone.
- [Angular: builds](https://angular.dev/tools/cli/build) — builder `@angular/build:application`.
- [Vite: início e requisitos](https://vite.dev/guide/) — servidor e produção.
- [WHATWG: Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html) — formato, UTF-8 e parsing.
- [MDN: Readable streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams) — leitura incremental de respostas.

## Exercício e critério de domínio

**Exercício:** interrompa a conexão SSE após receber um token e garanta que uma ação não seja criada duas vezes. Registre separadamente quantos POSTs de criação, GETs de observação e operações persistidas ocorreram. Faça o mesmo teste no React e no Angular.

**Solução comentada:** injete uma falha no transporte de observação, preserve o `run_id`, consulte o estado persistido e não reenvie o POST. O teste `A dropped SSE connection reads the persisted run without repeating POST` demonstra essa regra na unidade. No E2E, confira também a contagem de tickets do backend, pois uma resposta visual idêntica não prova ausência de efeito duplicado.

**Entrevista:** por que um timeout não autoriza retry automático de uma escrita? Porque o servidor pode ter persistido a operação antes de a resposta se perder. Uma consulta por identidade de execução, um identificador de idempotência ou uma decisão explícita de retomada é necessária para distinguir ausência de resposta de ausência de efeito.

**Conclusão verificável:** você consegue localizar o componente, o evento de interface, o corpo HTTP, o vínculo da sessão, o evento SSE, o estado persistido e a evidência mostrada para uma mesma pergunta; consegue explicar o que muda entre React e Angular e o que deve permanecer idêntico no contrato.
