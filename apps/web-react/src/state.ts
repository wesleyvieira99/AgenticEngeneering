import { AtlasApi, ApiError, active } from './api.ts';
import type {
  Approval,
  DocumentRecord,
  Health,
  Limits,
  Run,
  Session,
  Ticket,
  Usage,
} from './api.ts';
export type WorkspaceState = {
  session: Session | null;
  health: Health | null;
  documents: DocumentRecord[];
  runs: Run[];
  approvals: Approval[];
  tickets: Ticket[];
  usage: Usage | null;
  limits: Limits;
  run: Run | null;
  busy: boolean;
  observing: boolean;
  error: string;
  notice: string;
  conversationId: string | null;
  memory: boolean;
};
const initial = (): WorkspaceState => ({
  session: null,
  health: null,
  documents: [],
  runs: [],
  approvals: [],
  tickets: [],
  usage: null,
  limits: {},
  run: null,
  busy: false,
  observing: false,
  error: '',
  notice: '',
  conversationId: null,
  memory: false,
});
/** Both frameworks adapt this transport state; no rendering or secrets live here. */
export class AtlasStore {
  api: AtlasApi;
  state = initial();
  private listeners = new Set<() => void>();
  private epoch = 0;
  private stream: AbortController | null = null;
  private observation = 0;
  private selection = 0;
  private pending = 0;
  constructor(base: string) {
    this.api = new AtlasApi(base);
  }
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  snapshot = () => this.state;
  patch = (changes: Partial<WorkspaceState>) => {
    this.state = { ...this.state, ...changes };
    this.listeners.forEach((listener) => listener());
  };
  private report(error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      this.logout();
      this.patch({
        error: 'Sessão expirada ou credenciais inválidas. Entre novamente.',
      });
      return;
    }
    this.patch({
      error:
        error instanceof Error
          ? error.message
          : 'Não foi possível concluir a operação.',
    });
  }
  async health() {
    const epoch = this.epoch,
      base = this.api.base;
    try {
      const health = await this.api.request<Health>('/health');
      if (epoch === this.epoch && base === this.api.base)
        this.patch({ health });
    } catch {
      if (epoch === this.epoch && base === this.api.base)
        this.patch({ health: null });
    }
  }
  private beginSelection() {
    this.selection++;
    this.observation++;
    this.stream?.abort();
    this.patch({ observing: false });
    return this.selection;
  }
  private async perform(
    action: (epoch: number) => Promise<void>,
    relevant = () => true,
  ) {
    const epoch = this.epoch;
    this.pending++;
    this.patch({ busy: true, error: '', notice: '' });
    try {
      await action(epoch);
    } catch (error) {
      if (epoch === this.epoch && relevant()) this.report(error);
    } finally {
      if (epoch === this.epoch) {
        this.pending = Math.max(0, this.pending - 1);
        this.patch({ busy: this.pending > 0 });
      }
    }
  }
  async login(
    tenant: string,
    username: string,
    password: string,
    base = this.api.base,
  ) {
    return this.perform(async (epoch) => {
      const url = new URL(base);
      if (
        !['http:', 'https:'].includes(url.protocol) ||
        url.username ||
        url.password ||
        url.search ||
        url.hash
      )
        throw new Error(
          'Informe uma URL HTTP(S) da API, sem credenciais ou parâmetros.',
        );
      this.api.base = (url.origin + url.pathname).replace(/\/$/, '');
      const session = await this.api.post<Session>('/auth/login', {
        tenant,
        username,
        password,
      });
      if (epoch !== this.epoch) return;
      this.api.token = session.access_token;
      this.patch({ session });
      await this.refresh();
      await this.health();
    });
  }
  logout() {
    this.epoch++;
    this.selection++;
    this.pending = 0;
    this.observation++;
    this.stream?.abort();
    this.api.token = '';
    this.state = { ...initial(), health: this.state.health };
    this.listeners.forEach((listener) => listener());
  }
  async refresh() {
    const epoch = this.epoch;
    const [documents, runs, approvals, tickets, usage, limits] =
      await Promise.all([
        this.api.request<DocumentRecord[]>('/documents'),
        this.api.request<Run[]>('/runs'),
        this.api.request<Approval[]>('/approvals'),
        this.api.request<Ticket[]>('/tickets'),
        this.api.request<Usage>('/usage'),
        this.api.request<Limits>('/settings'),
      ]);
    if (epoch === this.epoch)
      this.patch({ documents, runs, approvals, tickets, usage, limits });
  }
  reload() {
    return this.perform(async (epoch) => {
      await this.refresh();
      if (epoch === this.epoch) this.patch({ notice: 'Workspace atualizado.' });
    });
  }
  setMemory(memory: boolean) {
    this.patch({
      memory,
      conversationId: memory ? this.state.conversationId : null,
    });
  }
  newConversation() {
    this.beginSelection();
    this.patch({
      run: null,
      conversationId: null,
      observing: false,
      error: '',
      notice: '',
    });
  }
  async send(question: string, strategy: string) {
    if (!question.trim() || active(this.state.run?.status)) return;
    const selection = this.beginSelection();
    return this.perform(
      async (epoch) => {
        const result = await this.api.post<{ id: string; status: string }>(
          '/runs',
          {
            question: question.trim(),
            strategy,
            memory_enabled: this.state.memory,
            ...(this.state.memory && this.state.conversationId
              ? { conversation_id: this.state.conversationId }
              : {}),
          },
        );
        if (epoch !== this.epoch || selection !== this.selection) return;
        this.patch({
          run: {
            ...result,
            question: question.trim(),
            strategy,
            answer: '',
            sources: [],
            events: [],
          },
        });
        await this.observe(result.id, epoch);
      },
      () => selection === this.selection,
    );
  }
  private async observe(id: string, epoch = this.epoch) {
    this.stream?.abort();
    const controller = new AbortController();
    this.stream = controller;
    const observation = ++this.observation;
    const current = () =>
      epoch === this.epoch &&
      observation === this.observation &&
      !controller.signal.aborted;
    this.patch({
      observing: true,
      run: this.state.run
        ? { ...this.state.run, answer: '', events: [] }
        : null,
    });
    try {
      try {
        await this.api.events(
          id,
          (event) => {
            if (!current() || !this.state.run) return;
            const run = { ...this.state.run };
            if (event.type === 'token')
              run.answer += (event.data as { text: string }).text;
            else if (event.type === 'sources')
              run.sources = event.data as Run['sources'];
            else if (event.type === 'usage') run.usage = event.data as Usage;
            else if (event.type === 'status')
              run.status =
                typeof event.data === 'string'
                  ? event.data
                  : (event.data as { status: string }).status;
            else if (event.type === 'done') {
              this.patch({
                run: event.data as Run,
                conversationId: this.state.memory
                  ? ((event.data as Run).conversation_id ?? null)
                  : null,
              });
              return;
            } else if (event.type === 'error')
              run.error = (event.data as { message: string }).message;
            if (event.type !== 'token')
              run.events = [...(run.events ?? []), event];
            this.patch({ run });
          },
          controller.signal,
        );
      } catch (error) {
        if (!current()) return;
        if (error instanceof ApiError && error.status === 401) throw error;
        this.patch({
          notice:
            'Fluxo interrompido. Consultando o estado persistido, sem repetir a operação.',
        });
      }
      // Reconciliation also covers streams that close before a terminal event.
      for (let attempt = 0; current() && attempt < 30; attempt++) {
        const run = await this.api.request<Run>(
          `/runs/${encodeURIComponent(id)}`,
          {
            signal: AbortSignal.any([
              controller.signal,
              AbortSignal.timeout(15_000),
            ]),
          },
        );
        if (!current()) return;
        this.patch({
          run,
          conversationId: this.state.memory
            ? (run.conversation_id ?? null)
            : null,
        });
        if (!active(run.status)) break;
        await new Promise<void>((resolve) => {
          const finish = () => {
            clearTimeout(timer);
            controller.signal.removeEventListener('abort', finish);
            resolve();
          };
          const timer = setTimeout(finish, 1000);
          controller.signal.addEventListener('abort', finish, { once: true });
        });
      }
      if (current()) {
        if (active(this.state.run?.status))
          this.patch({
            notice:
              'A execução continua no servidor. Use “Atualizar execução” para acompanhar.',
          });
        await this.refresh();
      }
    } catch (error) {
      // User cancellation or a newer selection intentionally invalidates this observation.
      if (current()) throw error;
    } finally {
      if (epoch === this.epoch && observation === this.observation)
        this.patch({ observing: false });
    }
  }
  selectRun(id: string) {
    const selection = this.beginSelection();
    return this.perform(
      async (epoch) => {
        const run = await this.api.request<Run>(
          `/runs/${encodeURIComponent(id)}`,
        );
        if (epoch !== this.epoch || selection !== this.selection) return;
        this.patch({
          run,
          observing: false,
          conversationId: this.state.memory
            ? (run.conversation_id ?? null)
            : null,
        });
        if (active(run.status)) await this.observe(id, epoch);
      },
      () => selection === this.selection,
    );
  }
  cancel() {
    const id = this.state.run?.id,
      selection = this.selection;
    if (!id) return;
    return this.perform(
      async (epoch) => {
        const run = await this.api.post<Run>(
          `/runs/${encodeURIComponent(id)}/cancel`,
        );
        if (epoch !== this.epoch) return;
        if (selection === this.selection && this.state.run?.id === id) {
          this.observation++;
          this.stream?.abort();
          this.patch({ run, observing: false });
        }
        await this.refresh();
      },
      () => selection === this.selection,
    );
  }
  resume() {
    const id = this.state.run?.id;
    if (!id) return;
    const selection = this.beginSelection();
    return this.perform(
      async (epoch) => {
        const run = await this.api.post<Run>(
          `/runs/${encodeURIComponent(id)}/resume`,
        );
        if (epoch !== this.epoch) return;
        if (selection !== this.selection) {
          await this.refresh();
          return;
        }
        this.patch({ run });
        await this.observe(id, epoch);
      },
      () => selection === this.selection,
    );
  }
  upload(file: File | null, title: string) {
    return this.perform(async (epoch) => {
      if (!file || !/\.(txt|md)$/i.test(file.name))
        throw new Error('Selecione um arquivo .txt ou .md em UTF-8.');
      if (file.size > 1024 * 1024)
        throw new Error('O documento deve ter no máximo 1 MiB.');
      const content = new TextDecoder('utf-8', { fatal: true }).decode(
        await file.arrayBuffer(),
      );
      if (epoch !== this.epoch) return;
      if (!content.trim()) throw new Error('O documento está vazio.');
      await this.api.post('/documents', {
        title: title.trim() || file.name,
        content,
      });
      if (epoch !== this.epoch) return;
      await this.refresh();
      if (epoch === this.epoch)
        this.patch({ notice: 'Documento recebido e indexado pela API.' });
    });
  }
  removeDocument(id: string) {
    return this.perform(async (epoch) => {
      await this.api.request(`/documents/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      if (epoch === this.epoch) {
        await this.refresh();
        if (epoch === this.epoch) this.patch({ notice: 'Documento excluído.' });
      }
    });
  }
  decide(id: string, decision: 'approve' | 'reject') {
    const selectedId = this.state.run?.id,
      selection = this.selection;
    return this.perform(async (epoch) => {
      await this.api.post(`/approvals/${encodeURIComponent(id)}/${decision}`);
      if (epoch !== this.epoch) return;
      await this.refresh();
      if (epoch !== this.epoch) return;
      if (selectedId && selection === this.selection) {
        const run = await this.api.request<Run>(
          `/runs/${encodeURIComponent(selectedId)}`,
        );
        if (epoch === this.epoch && selection === this.selection)
          this.patch({ run });
      }
      if (epoch === this.epoch)
        this.patch({
          notice:
            decision === 'approve'
              ? 'Ação aprovada. Confira o ticket e a auditoria.'
              : 'Ação rejeitada.',
        });
    });
  }
  forget() {
    const id = this.state.run?.conversation_id ?? this.state.conversationId;
    if (!id) return;
    const selection = this.selection;
    return this.perform(async (epoch) => {
      await this.api.request(`/conversations/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      if (epoch !== this.epoch || selection !== this.selection) return;
      this.patch({
        conversationId: null,
        memory: false,
        run: this.state.run
          ? { ...this.state.run, conversation_id: undefined }
          : null,
        notice:
          'Memória da conversa excluída. A auditoria da execução segue a retenção do servidor.',
      });
    });
  }
  saveLimits(limits: Limits) {
    return this.perform(async (epoch) => {
      const saved = await this.api.request<Limits>('/settings', {
        method: 'PUT',
        body: JSON.stringify(limits),
      });
      if (epoch === this.epoch) {
        this.patch({ limits: saved, notice: 'Limites atualizados pela API.' });
        await this.refresh();
      }
    });
  }
  dispose() {
    this.observation++;
    this.stream?.abort();
  }
}
