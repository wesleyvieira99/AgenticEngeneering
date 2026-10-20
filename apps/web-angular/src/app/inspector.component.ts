import { Component, input } from '@angular/core';
import { IconComponent } from './icon.component';
import { money, number } from './api';
import type { Run } from './api';
@Component({
  selector: 'atlas-inspector',
  standalone: true,
  imports: [IconComponent],
  template: `<aside class="inspector">
    <section class="surface inspector-section" aria-label="Fontes recuperadas">
      <div class="section-label">
        <atlas-icon name="file" />
        <h2>Fontes recuperadas</h2>
        <span class="count">{{ run()?.sources?.length ?? 0 }}</span>
      </div>
      @if (run()?.sources?.length) {
        @for (source of run()!.sources; track $index; let index = $index) {
          <details
            class="source"
            [id]="'source-' + (index + 1)"
            [open]="index === 0"
          >
            <summary>
              <span class="citation">{{ index + 1 }}</span
              ><span>{{ source.title }}</span>
            </summary>
            <p>{{ source.text }}</p>
            <small>
              @if (run()?.strategy === 'cag') {
                Contexto em cache · sem score RRF
              } @else {
                Ranking RRF: {{ source.score.toFixed(5) }} · não é probabilidade
              }
              <br /><code>{{ source.id }}</code></small
            >
          </details>
        }
      } @else {
        <p class="muted compact">
          As evidências recuperadas aparecem aqui após sua pergunta.
        </p>
      }
    </section>
    <section class="surface inspector-section">
      <div class="section-label">
        <atlas-icon name="clock" />
        <h2>Trilha da execução</h2>
      </div>
      <p class="muted compact">Eventos verificáveis da aplicação.</p>
      @if (run()?.events?.length) {
        <ol class="timeline">
          @for (event of run()!.events; track $index) {
            @if (event.type !== 'token') {
              <li>
                <span class="timeline-dot"></span>
                <details>
                  <summary>{{ event.type }}</summary>
                  <pre>{{ json(event.data) }}</pre>
                </details>
              </li>
            }
          }
        </ol>
      } @else {
        <div class="flow-empty">
          <span>Receber</span><span>Recuperar</span><span>Responder</span>
        </div>
      }
      <small class="muted"
        >Esta trilha não expõe raciocínio interno do modelo.</small
      >
    </section>
    @if (run(); as item) {
      <section class="surface inspector-section">
        <div class="section-label">
          <atlas-icon name="chart" />
          <h2>Nesta execução</h2>
        </div>
        <dl class="key-values">
          <div>
            <dt>Tokens de entrada</dt>
            <dd>{{ number(item.usage?.input_tokens) }}</dd>
          </div>
          <div>
            <dt>Tokens de saída</dt>
            <dd>{{ number(item.usage?.output_tokens) }}</dd>
          </div>
          <div>
            <dt>Custo registrado</dt>
            <dd>{{ money(item.usage?.cost_usd) }}</dd>
          </div>
          <div>
            <dt>Latência</dt>
            <dd>
              {{
                item.latency_ms == null ? '—' : number(item.latency_ms) + ' ms'
              }}
            </dd>
          </div>
          <div>
            <dt>Modelo</dt>
            <dd>{{ item.usage?.model ?? '—' }}</dd>
          </div>
        </dl>
      </section>
    }
  </aside>`,
})
export class InspectorComponent {
  run = input<Run | null>(null);
  number = number;
  money = money;
  json = (value: unknown) => JSON.stringify(value, null, 2);
}
