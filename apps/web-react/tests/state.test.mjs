import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { AtlasStore } from '../src/state.ts';

test('Both independent distributions use the same transport and state contract', async () => {
  for (const file of ['api.ts', 'state.ts']) {
    const react = await readFile(
      new URL(`../src/${file}`, import.meta.url),
      'utf8',
    );
    const angular = await readFile(
      new URL(`../../web-angular/src/app/${file}`, import.meta.url),
      'utf8',
    );
    assert.equal(react.replaceAll("'./api.ts'", "'./api'"), angular);
  }
});
test('A tenant response arriving after logout cannot repopulate private state', async () => {
  const store = new AtlasStore('http://localhost:8000');
  const deferred = [];
  store.api.request = () => new Promise((resolve) => deferred.push(resolve));
  const pending = store.refresh();
  store.logout();
  deferred.forEach((resolve) => resolve([{ title: 'Other tenant secret' }]));
  await pending;
  assert.deepEqual(store.state.documents, []);
  assert.equal(store.state.session, null);
});
test('A dropped SSE connection reads the persisted run without repeating POST', async () => {
  const store = new AtlasStore('http://localhost:8000');
  const posts = [];
  store.api.post = async (path, payload) => {
    posts.push({ path, payload });
    return { id: 'run-1', status: 'queued' };
  };
  store.api.events = async () => {
    throw new Error('Network disconnected');
  };
  store.api.request = async (path) =>
    path === '/runs/run-1'
      ? {
          id: 'run-1',
          status: 'completed',
          question: 'Política?',
          strategy: 'rag',
          answer: '30 dias [1]',
          sources: [],
          events: [],
          conversation_id: 'conv-1',
        }
      : [];
  await store.send('Política?', 'rag');
  assert.equal(posts.length, 1);
  assert.deepEqual(posts[0].payload, {
    question: 'Política?',
    strategy: 'rag',
    memory_enabled: false,
  });
  assert.equal(store.state.run.status, 'completed');
  assert.equal(store.state.conversationId, null);
  assert.equal(store.state.observing, false);
});
test('Memory is opt-in and can be removed from following requests', async () => {
  const store = new AtlasStore('http://localhost:8000');
  assert.equal(store.state.memory, false);
  store.setMemory(true);
  store.patch({ conversationId: 'conv-1' });
  store.setMemory(false);
  assert.equal(store.state.conversationId, null);
});
test('An upload read begun in an old session is never sent into the next tenant', async () => {
  const store = new AtlasStore('http://localhost:8000');
  let finishRead;
  const file = {
    name: 'policy.md',
    size: 10,
    arrayBuffer: () =>
      new Promise((resolve) => {
        finishRead = resolve;
      }),
  };
  let writes = 0;
  store.api.post = async () => {
    writes++;
    return {};
  };
  const upload = store.upload(file, 'Private policy');
  store.logout();
  store.api.token = 'new-tenant-token';
  finishRead(new TextEncoder().encode('Old tenant data').buffer);
  await upload;
  assert.equal(writes, 0);
});

test('Latest run selection wins even when earlier HTTP responses arrive last', async () => {
  const store = new AtlasStore('http://localhost:8000');
  const deferred = {};
  store.api.request = (path) =>
    new Promise((resolve) => {
      deferred[path] = resolve;
    });
  const first = store.selectRun('first');
  const latest = store.selectRun('latest');
  deferred['/runs/latest']({
    id: 'latest',
    status: 'completed',
    answer: 'Latest',
    sources: [],
    events: [],
  });
  await latest;
  assert.equal(
    store.state.busy,
    true,
    'the earlier HTTP request is still pending',
  );
  deferred['/runs/first']({
    id: 'first',
    status: 'completed',
    answer: 'First',
    sources: [],
    events: [],
  });
  await first;
  assert.equal(store.state.run.id, 'latest');
  assert.equal(store.state.busy, false);
});

test('A late cancellation result cannot replace a newly selected run', async () => {
  const store = new AtlasStore('http://localhost:8000');
  store.patch({
    run: {
      id: 'first',
      status: 'running',
      answer: '',
      sources: [],
      events: [],
    },
  });
  let cancelResponse;
  store.api.post = () =>
    new Promise((resolve) => {
      cancelResponse = resolve;
    });
  store.refresh = async () => {};
  store.api.request = async () => ({
    id: 'latest',
    status: 'completed',
    answer: 'Latest',
    sources: [],
    events: [],
  });
  const cancellation = store.cancel();
  await store.selectRun('latest');
  cancelResponse({
    id: 'first',
    status: 'cancelled',
    answer: '',
    sources: [],
    events: [],
  });
  await cancellation;
  assert.equal(store.state.run.id, 'latest');
  assert.equal(store.state.run.status, 'completed');
});

test('Intentional cancellation during polling is not displayed as a network failure', async () => {
  const store = new AtlasStore('http://localhost:8000');
  let pollingStarted;
  const polling = new Promise((resolve) => {
    pollingStarted = resolve;
  });
  store.api.post = async (path) =>
    path.endsWith('/cancel')
      ? {
          id: 'run-1',
          status: 'cancelled',
          answer: '',
          sources: [],
          events: [],
        }
      : { id: 'run-1', status: 'queued' };
  store.api.events = async () => {};
  store.api.request = (path, options) =>
    path === '/runs/run-1'
      ? new Promise((resolve, reject) => {
          pollingStarted();
          options.signal.addEventListener('abort', () =>
            reject(new DOMException('Aborted observation', 'AbortError')),
          );
        })
      : Promise.resolve([]);
  const operation = store.send('Test cancellation', 'async');
  await polling;
  await store.cancel();
  await operation;
  assert.equal(store.state.run.status, 'cancelled');
  assert.equal(store.state.error, '');
  assert.equal(store.state.busy, false);
});

test('Health from a previous API origin cannot mislabel the current provider mode', async () => {
  const store = new AtlasStore('http://localhost:8000');
  let resolveHealth;
  store.api.request = () =>
    new Promise((resolve) => {
      resolveHealth = resolve;
    });
  const pending = store.health();
  store.api.base = 'http://localhost:8010';
  store.patch({ health: { status: 'ok', mode: 'ollama' } });
  resolveHealth({ status: 'ok', mode: 'deterministic' });
  await pending;
  assert.equal(store.state.health.mode, 'ollama');
});

test('A failed newer selection stops the prior observation without leaving a false streaming state', async () => {
  const store = new AtlasStore('http://localhost:8000');
  let streamStarted;
  const started = new Promise((resolve) => {
    streamStarted = resolve;
  });
  store.api.post = async () => ({ id: 'previous', status: 'queued' });
  store.api.events = (id, onEvent, signal) =>
    new Promise((resolve, reject) => {
      streamStarted();
      signal.addEventListener('abort', () =>
        reject(new DOMException('Selection changed', 'AbortError')),
      );
    });
  store.api.request = async () => {
    throw new Error('Selected run unavailable');
  };
  const sending = store.send('Previous task', 'async');
  await started;
  await store.selectRun('unavailable');
  await sending;
  assert.equal(store.state.observing, false);
  assert.equal(store.state.busy, false);
  assert.equal(store.state.error, 'Selected run unavailable');
});
