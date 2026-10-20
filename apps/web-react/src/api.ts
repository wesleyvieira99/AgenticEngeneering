/** Public HTTP contract. Never put model-provider credentials in this module. */
export type Session = { access_token: string; tenant: string; role: string };
export type DocumentRecord = {
  id: string;
  title: string;
  version: number;
  created_at: string | number;
};
export type Source = { id: string; title: string; text: string; score: number };
export type AuditEvent = { type: string; data: unknown };
export type Usage = {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  model?: string;
  runs?: number;
  successful_runs?: number;
  reserved_tokens?: number;
  reserved_cost_usd?: number;
  active_runs?: number;
  cost_per_success_usd?: number | null;
  limits?: Limits;
};
export type Limits = Record<string, number>;
export type Run = {
  id: string;
  status: string;
  question: string;
  strategy: string;
  answer: string;
  sources: Source[];
  events: AuditEvent[];
  usage?: Usage;
  latency_ms?: number;
  conversation_id?: string;
  approval_id?: string;
  error?: string;
};
export type Approval = {
  id: string;
  run_id: string;
  action: string;
  arguments: Record<string, unknown>;
  status: string;
};
export type Ticket = {
  id: string;
  title: string;
  status: string;
  created_at: string | number;
};
export type Health = { status: string; mode: string };
export type StreamEvent = { type: string; data: unknown };
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}
export async function assertResponse(response: Response): Promise<void> {
  if (response.ok) return;
  let detail: unknown;
  try {
    detail = (await response.json()).detail;
  } catch {
    /* An upstream proxy may return HTML. */
  }
  const message =
    typeof detail === 'string'
      ? detail
      : detail
        ? JSON.stringify(detail)
        : response.statusText;
  throw new ApiError(
    `${response.status}: ${message || 'Falha na API'}`,
    response.status,
  );
}
/** Handles UTF-8 chunks at the reader, and LF/CRLF + multiline data here. */
export function createSSEParser(onEvent: (event: StreamEvent) => void) {
  let pending = '';
  return (chunk: string) => {
    pending += chunk;
    let separator: RegExpExecArray | null;
    while ((separator = /\r?\n\r?\n/.exec(pending))) {
      const frame = pending.slice(0, separator.index);
      pending = pending.slice(separator.index + separator[0].length);
      let type = 'message';
      const lines: string[] = [];
      for (const line of frame.split(/\r?\n/)) {
        if (line.startsWith('event:')) type = line.slice(6).trim();
        if (line.startsWith('data:'))
          lines.push(line.slice(5).replace(/^ /, ''));
      }
      if (lines.length) onEvent({ type, data: JSON.parse(lines.join('\n')) });
    }
    if (pending.length > 2 * 1024 * 1024)
      throw new Error('Evento excedeu o limite de 2 MiB.');
  };
}
export async function consumeSSE(
  response: Response,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  await assertResponse(response);
  if (!response.headers.get('content-type')?.includes('text/event-stream'))
    throw new Error('A API não retornou um stream SSE.');
  if (!response.body)
    throw new Error('Streaming indisponível neste navegador.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  const parse = createSSEParser(onEvent);
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        parse(decoder.decode());
        break;
      }
      parse(decoder.decode(value, { stream: true }));
    }
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
export class AtlasApi {
  base: string;
  token = '';
  constructor(base: string) {
    this.base = base.replace(/\/$/, '');
  }
  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.base}/api${path}`, {
      ...init,
      signal: init.signal ?? AbortSignal.timeout(15_000),
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
        ...init.headers,
      },
    });
    await assertResponse(response);
    return response.status === 204
      ? (undefined as T)
      : (response.json() as Promise<T>);
  }
  async events(
    id: string,
    onEvent: (event: StreamEvent) => void,
    signal: AbortSignal,
  ): Promise<void> {
    const response = await fetch(
      `${this.base}/api/runs/${encodeURIComponent(id)}/events`,
      {
        headers: {
          Accept: 'text/event-stream',
          Authorization: `Bearer ${this.token}`,
        },
        signal,
      },
    );
    await consumeSSE(response, onEvent);
  }
  post<T>(path: string, body: unknown = {}): Promise<T> {
    return this.request(path, { method: 'POST', body: JSON.stringify(body) });
  }
}
export const strategies = [
  {
    id: 'baseline',
    name: 'Baseline',
    detail: 'Resposta determinística, sem LLM.',
  },
  {
    id: 'direct',
    name: 'LLM direto',
    detail: 'Uma chamada, com saída estruturada.',
  },
  { id: 'rag', name: 'RAG', detail: 'Recuperação explícita de evidências.' },
  { id: 'cag', name: 'CAG', detail: 'Contexto de documentos em cache.' },
  {
    id: 'agent',
    name: 'Agente',
    detail: 'Ferramentas com permissões e limites.',
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    detail: 'Workflow com estado e checkpoints.',
  },
  {
    id: 'multiagent',
    name: 'Multiagente',
    detail: 'Supervisor e especialistas.',
  },
  {
    id: 'async',
    name: 'Assíncrono',
    detail: 'Fila persistente; exige um worker ativo.',
  },
];
export const navigation = [
  { id: 'workspace', title: 'Workspace', icon: 'spark' },
  { id: 'documents', title: 'Documentos', icon: 'file' },
  { id: 'approvals', title: 'Aprovações', icon: 'shield' },
  { id: 'history', title: 'Histórico', icon: 'clock' },
  { id: 'usage', title: 'Consumo', icon: 'chart' },
  { id: 'settings', title: 'Configurações', icon: 'settings' },
];
export const active = (status?: string) =>
  status === 'queued' || status === 'running';
export const statusLabel = (status?: string) =>
  ({
    queued: 'Na fila',
    running: 'Em execução',
    awaiting_approval: 'Aguarda aprovação',
    completed: 'Concluída',
    failed: 'Falhou',
    cancelled: 'Cancelada',
    pending: 'Pendente',
    approved: 'Aprovada',
    rejected: 'Rejeitada',
    open: 'Aberto',
  })[status ?? ''] ??
  status ??
  'Pronto';
export const money = (value?: number | null) =>
  value == null
    ? '—'
    : new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 6,
      }).format(value);
export const number = (value?: number) =>
  value == null ? '—' : new Intl.NumberFormat('pt-BR').format(value);
export const settingLabels: Partial<Record<string, string>> = {
  tenant_tokens: 'Tokens por organização',
  tenant_cost_usd: 'Orçamento da organização (USD)',
  max_tokens: 'Tokens por execução',
  max_output_tokens: 'Tokens de saída',
  max_calls: 'Chamadas de modelo',
  max_tools: 'Chamadas de ferramentas',
  max_steps: 'Passos por execução',
  timeout_seconds: 'Tempo limite (segundos)',
  concurrency: 'Execuções concorrentes',
};
