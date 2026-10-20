import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
bootstrapApplication(AppComponent).catch((error) =>
  console.error('Falha ao iniciar Atlas', error),
);
