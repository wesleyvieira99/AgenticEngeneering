import { useEffect, useState, useSyncExternalStore } from 'react';
import type { FormEvent, ReactNode } from 'react';
import {
  active,
  money,
  navigation,
  number,
  settingLabels,
  statusLabel,
  strategies,
} from './api';
import type { Limits, Run } from './api';
import { AtlasStore } from './state';
import type { WorkspaceState } from './state';

const icons: Record<string, string> = {
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M8 13h8 M8 17h5',
  shield: 'M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7z m-5 9 3 3 6-6',
  clock: 'M12 8v5l3 2 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
  chart: 'M4 3v17h17 M8 15v-4 M13 15V7 M18 15v-6',
  settings: 'M4 7h16 M4 17h16 M8 4v6 M16 14v6',
  arrow: 'M5 12h14 m-6-6 6 6-6 6',
  up: 'M12 19V5 m-6 6 6-6 6 6',
  plus: 'M12 5v14 M5 12h14',
  sun: 'M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l1.5 1.5 M17.5 17.5 1.5 1.5 M5 19l1.5-1.5 M17.5 6.5 1.5-1.5 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  logout: 'M9 5H4v14h5 M10 12h11 m-4-4 4 4-4 4',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 3 M18 18a8 8 0 0 1-13-3',
  upload: 'M12 16V3 m-5 5 5-5 5 5 M4 15v6h16v-6',
  check: 'm5 12 4 4L19 6',
};
export function Icon({
  name,
  className = '',
}: {
  name: string;
  className?: string;
}) {
  return (
    <svg
      className={`icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={icons[name] ?? icons.spark} />
    </svg>
  );
}
const Brand = () => (
  <div className="brand">
    <span className="brand-mark">
      <Icon name="spark" />
    </span>
    <span>
      atlas<span className="brand-period">.</span>
    </span>
  </div>
);
const formatDate = (value: string | number) =>
  new Date(typeof value === 'number' ? value * 1000 : value).toLocaleString(
    'pt-BR',
    { dateStyle: 'short', timeStyle: 'short' },
  );
function Empty({
  icon,
  title,
  children,
}: {
  icon: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name={icon} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: ReactNode;
  detail: string;
}) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
function Login({ store, state }: { store: AtlasStore; state: WorkspaceState }) {
  const [tenant, setTenant] = useState('acme'),
    [username, setUsername] = useState('admin'),
    [password, setPassword] = useState(''),
    [base, setBase] = useState(store.api.base);
  return (
    <main id="main" className="login-page">
      <header>
        <Brand />
        <span className="framework-tag">React client</span>
      </header>
      <div className="login-grid">
        <section className="login-story">
          <div className="eyebrow">
            <span className="live-dot" /> KNOWLEDGE & OPERATIONS
          </div>
          <h1>
            Conhecimento.
            <br />
            Com direção.
          </h1>
          <p>
            Da primeira pergunta à próxima ação.
            <br />
            Um workspace para explorar evidências
            <br className="desktop-only" /> e operar com confiança.
          </p>
          <div className="login-features">
            <span>
              <Icon name="file" /> Respostas com fontes
            </span>
            <span>
              <Icon name="shield" /> Você aprova as ações
            </span>
            <span>
              <Icon name="chart" /> Consumo transparente
            </span>
          </div>
          <div className="login-footer">
            ATLAS ENGINEERING <span>Conheça. Experimente. Construa.</span>
          </div>
        </section>
        <section className="login-card surface">
          <div className="eyebrow">SEU WORKSPACE</div>
          <h2>Bem-vindo ao Atlas</h2>
          <p>Entre na sua organização para começar.</p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void store.login(tenant, username, password, base);
            }}
          >
            <label>
              Endereço da API
              <input
                type="url"
                value={base}
                onChange={(event) => setBase(event.target.value)}
                required
              />
            </label>
            <label>
              Organização
              <select
                aria-label="Organização"
                value={tenant}
                onChange={(event) => setTenant(event.target.value)}
              >
                <option value="acme">Acme</option>
                <option value="orbit">Orbit</option>
              </select>
            </label>
            <label>
              Usuário
              <input
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Sua senha de acesso"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            {state.error && (
              <p className="alert error" role="alert">
                {state.error}
              </p>
            )}
            <button
              className="primary wide"
              disabled={state.busy}
              type="submit"
            >
              {state.busy ? 'Conectando…' : 'Entrar no workspace'}
              <Icon name="arrow" />
            </button>
          </form>
          <div className="dev-note">
            <Icon name="shield" />
            <p>
              Ambiente de desenvolvimento.
              <br />
              Senha local padrão: <code>atlas-local-only</code>.<br />
              Use a senha configurada no servidor.
            </p>
          </div>
          <div className="api-address">
            <span className={`live-dot ${state.health ? '' : 'offline'}`} />
            {state.health
              ? `API conectada · ${state.health.mode}`
              : 'API aguardando conexão'}
            <code>{store.api.base}</code>
          </div>
        </section>
      </div>
    </main>
  );
}
function Sources({ run }: { run: Run | null }) {
  return (
    <section
      className="surface inspector-section"
      aria-label="Fontes recuperadas"
    >
      <div className="section-label">
        <Icon name="file" />
        <h2>Fontes recuperadas</h2>
        <span className="count">{run?.sources?.length ?? 0}</span>
      </div>
      {run?.sources?.length ? (
        run.sources.map((source, index) => (
          <details
            className="source"
            key={`${source.id}-${index}`}
            id={`source-${index + 1}`}
            open={index === 0}
          >
            <summary>
              <span className="citation">{index + 1}</span>
              <span>{source.title}</span>
            </summary>
            <p>{source.text}</p>
            <small>
              {run?.strategy === 'cag'
                ? 'Contexto em cache · sem score RRF'
                : `Ranking RRF: ${source.score.toFixed(5)} · não é probabilidade`}
              <br />
              <code>{source.id}</code>
            </small>
          </details>
        ))
      ) : (
        <p className="muted compact">
          As evidências recuperadas aparecem aqui após sua pergunta.
        </p>
      )}
    </section>
  );
}
function Inspector({ run }: { run: Run | null }) {
  return (
    <aside className="inspector">
      <Sources run={run} />
      <section className="surface inspector-section">
        <div className="section-label">
          <Icon name="clock" />
          <h2>Trilha da execução</h2>
        </div>
        <p className="muted compact">Eventos verificáveis da aplicação.</p>
        {run?.events?.length ? (
          <ol className="timeline">
            {run.events
              .filter((event) => event.type !== 'token')
              .map((event, index) => (
                <li key={index}>
                  <span className="timeline-dot" />
                  <details>
                    <summary>{event.type}</summary>
                    <pre>{JSON.stringify(event.data, null, 2)}</pre>
                  </details>
                </li>
              ))}
          </ol>
        ) : (
          <div className="flow-empty">
            <span>Receber</span>
            <span>Recuperar</span>
            <span>Responder</span>
          </div>
        )}
        <small className="muted">
          Esta trilha não expõe raciocínio interno do modelo.
        </small>
      </section>
      {run && (
        <section className="surface inspector-section">
          <div className="section-label">
            <Icon name="chart" />
            <h2>Nesta execução</h2>
          </div>
          <dl className="key-values">
            <div>
              <dt>Tokens de entrada</dt>
              <dd>{number(run.usage?.input_tokens)}</dd>
            </div>
            <div>
              <dt>Tokens de saída</dt>
              <dd>{number(run.usage?.output_tokens)}</dd>
            </div>
            <div>
              <dt>Custo registrado</dt>
              <dd>{money(run.usage?.cost_usd)}</dd>
            </div>
            <div>
              <dt>Latência</dt>
              <dd>
                {run.latency_ms == null ? '—' : `${number(run.latency_ms)} ms`}
              </dd>
            </div>
            <div>
              <dt>Modelo</dt>
              <dd>{run.usage?.model ?? '—'}</dd>
            </div>
          </dl>
        </section>
      )}
    </aside>
  );
}
function Answer({ run }: { run: Run }) {
  return (
    <div className="answer-text">
      {run.answer.split(/(\[[^\[\]\n]+\])/g).map((part, index) => {
        const citation = /^\[([^\[\]\n]+)\]$/.exec(part)?.[1];
        const sourceIndex =
          run.sources?.findIndex((source) => source.id === citation) ?? -1;
        const number =
          sourceIndex >= 0
            ? sourceIndex + 1
            : /^\d+$/.test(citation ?? '') &&
                run.sources?.[Number(citation) - 1]
              ? Number(citation)
              : null;
        return number ? (
          <a
            key={index}
            href={`#source-${number}`}
            aria-label={`Fonte ${number}`}
          >
            [{number}]
          </a>
        ) : (
          part
        );
      })}
    </div>
  );
}
function Workspace({
  store,
  state,
  question,
  setQuestion,
  strategy,
  setStrategy,
  navigate,
}: {
  store: AtlasStore;
  state: WorkspaceState;
  question: string;
  setQuestion: (value: string) => void;
  strategy: string;
  setStrategy: (value: string) => void;
  navigate: (value: string) => void;
}) {
  const run = state.run,
    running = active(run?.status);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SEU CONHECIMENTO, EM MOVIMENTO</div>
          <h1>Pergunte. Verifique. Execute.</h1>
          <p>Explore sua base e transforme evidências em próximas ações.</p>
        </div>
        <button
          className="secondary"
          disabled={running || state.busy}
          onClick={() => store.newConversation()}
        >
          <Icon name="plus" />
          Nova conversa
        </button>
      </div>
      <div className="workspace-grid">
        <section className="conversation">
          <div className="surface chat-panel">
            {run ? (
              <>
                <div className="run-meta">
                  <span className={`status ${run.status}`}>
                    <span className="live-dot" />
                    {statusLabel(run.status)}
                  </span>
                  <span>
                    {strategies.find((item) => item.id === run.strategy)
                      ?.name ?? run.strategy}
                  </span>
                </div>
                <div className="question-block">
                  <span className="avatar user-avatar">V</span>
                  <div>
                    <span className="speaker">Você</span>
                    <p>{run.question}</p>
                  </div>
                </div>
                <div className="answer-block">
                  <span className="avatar atlas-avatar">
                    <Icon name="spark" />
                  </span>
                  <div>
                    <span className="speaker">
                      Atlas{' '}
                      <span className="subtle">/ resposta fundamentada</span>
                    </span>
                    {run.answer ? (
                      <Answer run={run} />
                    ) : (
                      <p className="muted" role="status">
                        {running
                          ? 'Construindo a resposta…'
                          : 'A execução não produziu uma resposta.'}
                      </p>
                    )}
                    {run.error && <p className="alert error">{run.error}</p>}
                    {run.status === 'awaiting_approval' && (
                      <button
                        className="secondary"
                        onClick={() => navigate('approvals')}
                      >
                        <Icon name="shield" />
                        Revisar ação pendente
                      </button>
                    )}
                  </div>
                </div>
                <div className="run-actions">
                  <code>run · {run.id.slice(0, 12)}</code>
                  {running && (
                    <button
                      className="danger-quiet"
                      onClick={() => void store.cancel()}
                    >
                      Cancelar execução
                    </button>
                  )}
                  {['failed', 'cancelled'].includes(run.status) && (
                    <button
                      className="secondary"
                      onClick={() => void store.resume()}
                      disabled={state.busy}
                    >
                      Retomar execução
                    </button>
                  )}
                  {!state.observing && (
                    <button
                      className="quiet"
                      onClick={() => void store.selectRun(run.id)}
                      disabled={state.busy}
                    >
                      <Icon name="refresh" />
                      Atualizar execução
                    </button>
                  )}
                </div>
              </>
            ) : (
              <div className="welcome-chat">
                <div className="orb">
                  <Icon name="spark" />
                </div>
                <div className="eyebrow">COM CONTEXTO, VAMOS ALÉM</div>
                <h2>O que vamos descobrir?</h2>
                <p>
                  Pergunte sobre os documentos da sua organização.
                  <br />
                  As fontes acompanham cada resposta recuperada.
                </p>
                <div className="suggestions">
                  <button
                    onClick={() =>
                      setQuestion('Qual é a política de reembolso?')
                    }
                  >
                    <Icon name="file" />
                    <span>
                      Explorar uma política
                      <small>Busque evidências nos documentos</small>
                    </span>
                    <Icon name="arrow" />
                  </button>
                  <button
                    onClick={() => {
                      setQuestion('/ticket Revisar política de reembolso');
                      setStrategy('agent');
                    }}
                  >
                    <Icon name="shield" />
                    <span>
                      Preparar uma ação
                      <small>Crie um ticket com sua aprovação</small>
                    </span>
                    <Icon name="arrow" />
                  </button>
                </div>
              </div>
            )}
          </div>
          <form
            className="surface composer"
            onSubmit={(event) => {
              event.preventDefault();
              void store.send(question, strategy);
            }}
          >
            <label className="sr-only" htmlFor="question">
              Pergunta
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Pergunte sobre seus documentos ou prepare uma ação…"
              rows={3}
              maxLength={4000}
              required
            />
            <div className="composer-bottom">
              <label className="strategy-control">
                <Icon name="spark" />
                <span className="sr-only">Estratégia</span>
                <select
                  aria-label="Estratégia"
                  value={strategy}
                  onChange={(event) => setStrategy(event.target.value)}
                >
                  {strategies.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="primary send"
                type="submit"
                disabled={state.busy || running || !question.trim()}
              >
                <span>Enviar pergunta</span>
                <Icon name="up" />
              </button>
            </div>
            <p className="strategy-help">
              {strategies.find((item) => item.id === strategy)?.detail}
            </p>
          </form>
          <div className="memory-controls">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={state.memory}
                onChange={(event) => store.setMemory(event.target.checked)}
              />
              Usar memória desta conversa
            </label>
            {run?.conversation_id && (
              <button
                className="quiet danger-quiet"
                disabled={state.busy || running}
                onClick={() => {
                  if (
                    confirm(
                      'Excluir a memória desta conversa? A auditoria permanece sujeita à retenção do servidor.',
                    )
                  )
                    void store.forget();
                }}
              >
                Excluir memória
              </button>
            )}
          </div>
          <p className="fineprint">
            A memória é opcional. Sem consentimento, o histórico não entra no
            contexto. Use <code>/tickets</code> para consultar tickets.
          </p>
        </section>
        <Inspector run={run} />
      </div>
    </>
  );
}
function Documents({
  store,
  state,
}: {
  store: AtlasStore;
  state: WorkspaceState;
}) {
  const [file, setFile] = useState<File | null>(null),
    [title, setTitle] = useState('');
  return (
    <>
      <PageHeading
        eyebrow="BASE DE CONHECIMENTO"
        title="Contexto começa aqui."
        description="Documentos da sua organização, versionados e recuperáveis."
      />
      <div className="content-columns">
        <section className="surface panel">
          <div className="section-label">
            <Icon name="file" />
            <h2>Seus documentos</h2>
            <span className="count">{state.documents.length}</span>
          </div>
          {state.documents.length ? (
            <div className="record-list">
              {state.documents.map((document) => (
                <article className="record" key={document.id}>
                  <span className="record-icon">
                    <Icon name="file" />
                  </span>
                  <div>
                    <h3>{document.title}</h3>
                    <p>
                      Versão {document.version} ·{' '}
                      {formatDate(document.created_at)}
                    </p>
                    <code>{document.id.slice(0, 12)}</code>
                  </div>
                  <button
                    className="quiet danger-quiet"
                    aria-label={`Excluir ${document.title}`}
                    disabled={state.busy}
                    onClick={() => {
                      if (confirm(`Excluir “${document.title}” da base?`))
                        void store.removeDocument(document.id);
                    }}
                  >
                    Excluir
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <Empty icon="file" title="Sua base está pronta para começar">
              Envie seu primeiro documento para fazer perguntas com evidências.
            </Empty>
          )}
        </section>
        <form
          className="surface panel upload-panel"
          onSubmit={(event) => {
            event.preventDefault();
            void store.upload(file, title);
          }}
        >
          <span className="large-icon">
            <Icon name="upload" />
          </span>
          <h2>Adicionar conhecimento</h2>
          <p>Texto simples ou Markdown em UTF-8. Até 1 MiB por arquivo.</p>
          <label>
            Título do documento
            <input
              placeholder="Ex.: Política de reembolso"
              value={title}
              maxLength={200}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>
          <label className="upload-target">
            Arquivo do documento
            <input
              type="file"
              accept=".txt,.md,text/plain,text/markdown"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
            />
          </label>
          <button className="primary wide" disabled={state.busy || !file}>
            Enviar documento
            <Icon name="upload" />
          </button>
          <small>
            O backend valida, divide e indexa o conteúdo. Documentos são dados,
            nunca instruções de autorização.
          </small>
        </form>
      </div>
    </>
  );
}
function PageHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </div>
  );
}
function Approvals({
  store,
  state,
}: {
  store: AtlasStore;
  state: WorkspaceState;
}) {
  return (
    <>
      <PageHeading
        eyebrow="VOCÊ NO CONTROLE"
        title="Ações com responsabilidade."
        description="Confira a operação e seus argumentos antes de autorizar."
      />
      <div className="content-columns">
        <section className="surface panel">
          <div className="section-label">
            <Icon name="shield" />
            <h2>Aprovações</h2>
          </div>
          {state.approvals.length ? (
            state.approvals.map((approval) => (
              <article className="approval-card" key={approval.id}>
                <div className="approval-head">
                  <h3>{approval.action}</h3>
                  <span className={`status ${approval.status}`}>
                    {statusLabel(approval.status)}
                  </span>
                </div>
                <pre>{JSON.stringify(approval.arguments, null, 2)}</pre>
                <small>
                  Execução {approval.run_id.slice(0, 12)} · ação vinculada no
                  servidor
                </small>
                {approval.status === 'pending' && (
                  <div className="button-row">
                    <button
                      className="primary"
                      disabled={state.busy}
                      onClick={() => void store.decide(approval.id, 'approve')}
                    >
                      <Icon name="check" />
                      Aprovar ação
                    </button>
                    <button
                      className="secondary"
                      disabled={state.busy}
                      onClick={() => void store.decide(approval.id, 'reject')}
                    >
                      Rejeitar ação
                    </button>
                  </div>
                )}
              </article>
            ))
          ) : (
            <Empty icon="shield" title="Nenhuma ação para revisar">
              No workspace, use “/ticket título” com a estratégia Agente para
              preparar uma operação local.
            </Empty>
          )}
        </section>
        <section className="surface panel">
          <div className="section-label">
            <Icon name="file" />
            <h2>Tickets persistidos</h2>
            <span className="count">{state.tickets.length}</span>
          </div>
          {state.tickets.length ? (
            state.tickets.map((ticket) => (
              <article className="ticket" key={ticket.id}>
                <h3>{ticket.title}</h3>
                <span className="status">{statusLabel(ticket.status)}</span>
                <p>{formatDate(ticket.created_at)}</p>
                <code>{ticket.id}</code>
              </article>
            ))
          ) : (
            <p className="muted">
              Os tickets criados após aprovação aparecem aqui.
            </p>
          )}
        </section>
      </div>
    </>
  );
}
function History({
  store,
  state,
  navigate,
}: {
  store: AtlasStore;
  state: WorkspaceState;
  navigate: (page: string) => void;
}) {
  return (
    <>
      <PageHeading
        eyebrow="HISTÓRICO AUDITÁVEL"
        title="Cada execução conta."
        description="Reabra respostas, compare estratégias e inspecione o que aconteceu."
      />
      <section className="surface panel">
        {state.runs.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Pergunta</th>
                  <th>Estratégia</th>
                  <th>Estado</th>
                  <th>Tokens</th>
                  <th>Custo (USD)</th>
                  <th>Latência</th>
                  <th>Abrir</th>
                </tr>
              </thead>
              <tbody>
                {state.runs.map((run) => (
                  <tr key={run.id}>
                    <td>
                      <strong>{run.question}</strong>
                      <code>{run.id.slice(0, 12)}</code>
                    </td>
                    <td>{run.strategy}</td>
                    <td>
                      <span className={`status ${run.status}`}>
                        {statusLabel(run.status)}
                      </span>
                    </td>
                    <td>
                      {run.usage
                        ? number(
                            run.usage.input_tokens + run.usage.output_tokens,
                          )
                        : '—'}
                    </td>
                    <td>{money(run.usage?.cost_usd)}</td>
                    <td>
                      {run.latency_ms == null
                        ? '—'
                        : `${number(run.latency_ms)} ms`}
                    </td>
                    <td>
                      <button
                        className="quiet"
                        aria-label={`Abrir execução ${run.id}`}
                        onClick={() => {
                          navigate('workspace');
                          void store.selectRun(run.id);
                        }}
                      >
                        <Icon name="arrow" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty icon="clock" title="Sua jornada começa com uma pergunta">
            As execuções da organização serão listadas aqui.
          </Empty>
        )}
      </section>
    </>
  );
}
function UsageView({ state }: { state: WorkspaceState }) {
  return (
    <>
      <PageHeading
        eyebrow="AI FINOPS"
        title="Consumo sob controle."
        description="Consumo registrado pela API, atribuído à organização atual."
      />
      <div className="stats-grid">
        <Stat
          label="Tokens de entrada"
          value={number(state.usage?.input_tokens)}
          detail="Contexto enviado ao modelo"
        />
        <Stat
          label="Tokens de saída"
          value={number(state.usage?.output_tokens)}
          detail="Conteúdo gerado"
        />
        <Stat
          label="Custo registrado"
          value={money(state.usage?.cost_usd)}
          detail="USD · estimativa do gateway"
        />
        <Stat
          label="Execuções"
          value={number(state.usage?.runs)}
          detail="Registro persistido do tenant"
        />
        <Stat
          label="Conclusões operacionais"
          value={number(state.usage?.successful_runs)}
          detail="Execuções concluídas pela API"
        />
        <Stat
          label="Custo por tarefa concluída"
          value={money(state.usage?.cost_per_success_usd)}
          detail="Custo total ÷ conclusões"
        />
      </div>
      <section className="surface panel">
        <h2>Leia o consumo no contexto.</h2>
        <p>
          O custo por tarefa concluída inclui os custos de falhas no total. “—”
          indica nenhuma conclusão ou métrica indisponível. Conclusão
          operacional não mede a qualidade da resposta.
        </p>
        <p>
          O modo determinístico valida a engenharia, mas não comprova inferência
          de um provedor real. Um custo de zero pode representar esse modo.
        </p>
        <div className="mode-banner">
          <Icon name="chart" />
          <div>
            <strong>
              Modo informado pela API: {state.health?.mode ?? 'indisponível'}
            </strong>
            <p>
              Preços, limites e contabilidade são aplicados no servidor. Compare
              estes registros com a cobrança do provedor.
            </p>
          </div>
        </div>
        <h3>Reservas e operações em andamento</h3>
        <p>
          Reservas bloqueiam novas admissões enquanto uma chamada está em
          andamento ou seu consumo é ambíguo. Não são cobrança confirmada.
        </p>
        <dl className="limit-list" aria-label="Reservas do tenant">
          <div>
            <dt>Execuções ativas</dt>
            <dd>{number(state.usage?.active_runs)}</dd>
          </div>
          <div>
            <dt>Tokens reservados</dt>
            <dd>{number(state.usage?.reserved_tokens)}</dd>
          </div>
          <div>
            <dt>Custo reservado</dt>
            <dd>{money(state.usage?.reserved_cost_usd)}</dd>
          </div>
        </dl>
        <h3>Limites configurados</h3>
        <dl className="limit-list">
          {Object.entries(state.limits).map(([key, value]) => (
            <div key={key}>
              <dt>{settingLabels[key] ?? key}</dt>
              <dd>{key.includes('usd') ? money(value) : number(value)}</dd>
            </div>
          ))}
        </dl>
      </section>
    </>
  );
}
function Settings({
  store,
  state,
}: {
  store: AtlasStore;
  state: WorkspaceState;
}) {
  const [limits, setLimits] = useState<Limits>(state.limits);
  useEffect(() => setLimits(state.limits), [state.limits]);
  return (
    <>
      <PageHeading
        eyebrow="GOVERNANÇA DO WORKSPACE"
        title="Limites explícitos."
        description="A API é a autoridade para orçamento, chamadas e concorrência."
      />
      <form
        className="surface panel"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          void store.saveLimits(limits);
        }}
      >
        <div className="settings-grid">
          {Object.entries(limits).map(([key, value]) => (
            <label key={key}>
              {settingLabels[key] ?? key}
              <input
                type="number"
                min="0"
                step={key.includes('usd') ? '0.001' : '1'}
                value={value}
                disabled={state.session?.role !== 'admin'}
                onChange={(event) =>
                  setLimits({ ...limits, [key]: Number(event.target.value) })
                }
                required
              />
              <code>{key}</code>
            </label>
          ))}
        </div>
        <div className="button-row">
          <button
            className="primary"
            disabled={
              state.busy ||
              state.session?.role !== 'admin' ||
              !Object.keys(limits).length
            }
          >
            Salvar limites
          </button>
          <small>
            Somente administradores. Validação e aplicação ocorrem no servidor.
          </small>
        </div>
      </form>
    </>
  );
}
export default function App({ store }: { store: AtlasStore }) {
  const state = useSyncExternalStore(store.subscribe, store.snapshot);
  const [page, setPage] = useState('workspace'),
    [question, setQuestion] = useState(''),
    [strategy, setStrategy] = useState('rag');
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem('atlas-theme') === 'dark';
    } catch {
      return false;
    }
  });
  useEffect(() => {
    void store.health();
    return () => store.dispose();
  }, [store]);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    try {
      localStorage.setItem('atlas-theme', dark ? 'dark' : 'light');
    } catch {
      /* Theme remains functional without storage. */
    }
  }, [dark]);
  useEffect(() => {
    setQuestion('');
    setStrategy('rag');
    setPage('workspace');
  }, [state.session?.access_token]);
  if (!state.session)
    return (
      <>
        <a href="#main" className="skip-link">
          Pular para o conteúdo
        </a>
        <Login store={store} state={state} />
        <button
          className="theme-login quiet"
          aria-label="Alternar tema"
          onClick={() => setDark(!dark)}
        >
          <Icon name="sun" />
        </button>
      </>
    );
  const selected = navigation.find((item) => item.id === page),
    pending = state.approvals.filter(
      (item) => item.status === 'pending',
    ).length;
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Pular para o conteúdo
      </a>
      <aside className="sidebar">
        <Brand />
        <div className="tenant-switch">
          <span className="tenant-avatar">
            {state.session.tenant.slice(0, 1).toUpperCase()}
          </span>
          <div>
            <strong>{state.session.tenant}</strong>
            <small>Workspace da organização</small>
          </div>
          <span className="tenant-dot" />
        </div>
        <div className="nav-label">PLATAFORMA</div>
        <nav aria-label="Navegação principal">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? 'selected' : ''}
              aria-current={page === item.id ? 'page' : undefined}
              onClick={() => setPage(item.id)}
            >
              <Icon name={item.icon} />
              <span>{item.title}</span>
              {item.id === 'approvals' && pending > 0 && (
                <span className="nav-count">{pending}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Icon name="shield" />
          <strong>Confiança verificável.</strong>
          <p>Fontes, permissões e consumo acompanham cada execução.</p>
        </div>
        <div className="sidebar-footer">
          <span className="framework-tag">React client</span>
          <button
            className="quiet"
            aria-label="Sair do workspace"
            onClick={() => {
              store.logout();
              setQuestion('');
              setPage('workspace');
            }}
          >
            <Icon name="logout" />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span>
            <strong>{selected?.title}</strong>
          </div>
          <div className="top-actions">
            <span className="connection">
              <span className={`live-dot ${state.health ? '' : 'offline'}`} />
              {state.health?.mode ?? 'API indisponível'}
            </span>
            <button
              className="quiet"
              aria-label="Atualizar workspace"
              disabled={state.busy}
              onClick={() => void store.reload()}
            >
              <Icon name="refresh" />
            </button>
            <button
              className="quiet"
              aria-label="Alternar tema"
              onClick={() => setDark(!dark)}
            >
              <Icon name="sun" />
            </button>
            <button
              className="quiet mobile-logout"
              aria-label="Sair do workspace"
              onClick={() => {
                store.logout();
                setQuestion('');
                setPage('workspace');
              }}
            >
              <Icon name="logout" />
            </button>
            <span className="profile">
              {state.session.role.slice(0, 1).toUpperCase()}
            </span>
          </div>
        </header>
        <main id="main" className="main-content">
          {state.error && (
            <div className="alert error" role="alert">
              {state.error}
            </div>
          )}
          {state.notice && (
            <div className="alert notice" role="status">
              {state.notice}
            </div>
          )}
          {page === 'workspace' && (
            <Workspace
              store={store}
              state={state}
              question={question}
              setQuestion={setQuestion}
              strategy={strategy}
              setStrategy={setStrategy}
              navigate={setPage}
            />
          )}{' '}
          {page === 'documents' && <Documents store={store} state={state} />}{' '}
          {page === 'approvals' && <Approvals store={store} state={state} />}{' '}
          {page === 'history' && (
            <History store={store} state={state} navigate={setPage} />
          )}{' '}
          {page === 'usage' && <UsageView state={state} />}{' '}
          {page === 'settings' && <Settings store={store} state={state} />}
          <footer className="content-footer">
            <span>
              ATLAS <span className="muted">/ Knowledge & Operations</span>
            </span>
            <span>Contexto. Evidência. Controle.</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
