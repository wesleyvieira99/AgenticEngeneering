import { Component, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AtlasService } from './atlas.service';
import { IconComponent } from './icon.component';
import { InspectorComponent } from './inspector.component';
import {
  active,
  money,
  navigation,
  number,
  settingLabels,
  statusLabel,
  strategies,
} from './api';
import type { Limits } from './api';
@Component({
  selector: 'atlas-app',
  standalone: true,
  imports: [FormsModule, IconComponent, InspectorComponent],
  templateUrl: './app.component.html',
})
export class AppComponent {
  readonly atlas = inject(AtlasService);
  readonly store = this.atlas.store;
  readonly state = this.atlas.state;
  readonly run = computed(() => this.state().run);
  readonly pending = computed(
    () =>
      this.state().approvals.filter((item) => item.status === 'pending').length,
  );
  readonly page = signal('workspace');
  readonly selected = computed(() =>
    navigation.find((item) => item.id === this.page()),
  );
  readonly dark = signal(this.readTheme());
  base = this.store.api.base;
  tenant = 'acme';
  username = 'admin';
  password = '';
  question = '';
  strategy = 'rag';
  documentTitle = '';
  documentFile: File | null = null;
  draftLimits: Limits = {};
  navigation = navigation;
  strategies = strategies;
  settingLabels = settingLabels;
  active = active;
  money = money;
  number = number;
  statusLabel = statusLabel;
  json = (value: unknown) => JSON.stringify(value, null, 2);
  date = (value: string | number) =>
    new Date(typeof value === 'number' ? value * 1000 : value).toLocaleString(
      'pt-BR',
      { dateStyle: 'short', timeStyle: 'short' },
    );
  constructor() {
    let previousSession: string | null = null;
    effect(() => {
      const session = this.state().session?.access_token ?? null;
      if (session !== previousSession) {
        this.question = '';
        this.strategy = 'rag';
        this.documentTitle = '';
        this.documentFile = null;
        this.password = '';
        this.page.set('workspace');
        previousSession = session;
      }
    });
    let previous: Limits | null = null;
    effect(() => {
      const limits = this.state().limits;
      if (limits !== previous) {
        this.draftLimits = { ...limits };
        previous = limits;
      }
    });
    effect(() => {
      const theme = this.dark() ? 'dark' : 'light';
      document.documentElement.dataset['theme'] = theme;
      try {
        localStorage.setItem('atlas-theme', theme);
      } catch {
        /* Storage is optional. */
      }
    });
    void this.store.health();
  }
  private readTheme() {
    try {
      return localStorage.getItem('atlas-theme') === 'dark';
    } catch {
      return false;
    }
  }
  toggleTheme() {
    this.dark.update((value) => !value);
  }
  login() {
    void this.store.login(this.tenant, this.username, this.password, this.base);
  }
  logout() {
    this.store.logout();
    this.password = '';
    this.question = '';
    this.page.set('workspace');
  }
  send() {
    void this.store.send(this.question, this.strategy);
  }
  strategyName(id: string) {
    return strategies.find((item) => item.id === id)?.name ?? id;
  }
  strategyDetail() {
    return strategies.find((item) => item.id === this.strategy)?.detail;
  }
  fileChanged(event: Event) {
    this.documentFile = (event.target as HTMLInputElement).files?.[0] ?? null;
  }
  upload() {
    void this.store.upload(this.documentFile, this.documentTitle);
  }
  removeDocument(id: string, title: string) {
    if (confirm(`Excluir “${title}” da base?`))
      void this.store.removeDocument(id);
  }
  forget() {
    if (
      confirm(
        'Excluir a memória desta conversa? A auditoria permanece sujeita à retenção do servidor.',
      )
    )
      void this.store.forget();
  }
  selectRun(id: string) {
    this.page.set('workspace');
    void this.store.selectRun(id);
  }
  limitEntries() {
    return Object.entries(this.draftLimits);
  }
  savedLimits() {
    return Object.entries(this.state().limits);
  }
  saveLimits() {
    void this.store.saveLimits(this.draftLimits);
  }
  answerParts(answer: string) {
    return answer.split(/(\[[^\[\]\n]+\])/g);
  }
  sourceNumber(part: string) {
    const citation = /^\[([^\[\]\n]+)\]$/.exec(part)?.[1];
    const sources = this.run()?.sources;
    const index = sources?.findIndex((source) => source.id === citation) ?? -1;
    return index >= 0
      ? index + 1
      : /^\d+$/.test(citation ?? '') && sources?.[Number(citation) - 1]
        ? Number(citation)
        : null;
  }
}
