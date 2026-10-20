import { DestroyRef, Injectable, inject, signal } from '@angular/core';
import { AtlasStore } from './state';
declare global {
  interface Window {
    ATLAS_API_URL?: string;
  }
}
@Injectable({ providedIn: 'root' })
export class AtlasService {
  readonly store = new AtlasStore(
    window.ATLAS_API_URL || 'http://localhost:8000',
  );
  readonly state = signal(this.store.state);
  constructor() {
    const unsubscribe = this.store.subscribe(() =>
      this.state.set(this.store.state),
    );
    inject(DestroyRef).onDestroy(() => {
      unsubscribe();
      this.store.dispose();
    });
  }
}
