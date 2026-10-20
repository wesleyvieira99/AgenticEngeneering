import { Component, input } from '@angular/core';
@Component({
  selector: 'atlas-icon',
  standalone: true,
  template: `<svg
    class="icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path [attr.d]="paths[name()] || paths['spark']" />
  </svg>`,
})
export class IconComponent {
  name = input('spark');
  paths: Record<string, string> = {
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
}
