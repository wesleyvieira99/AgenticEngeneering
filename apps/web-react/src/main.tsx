import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { AtlasStore } from './state';
import './styles.css';
const store = new AtlasStore(
  import.meta.env.VITE_API_URL || 'http://localhost:8000',
);
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App store={store} />
  </StrictMode>,
);
