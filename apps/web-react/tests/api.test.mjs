import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ApiError,
  AtlasApi,
  assertResponse,
  consumeSSE,
  createSSEParser,
} from '../src/api.ts';

test('SSE decodes fragmented UTF-8 and CRLF without losing accents', async () => {
  const bytes = new TextEncoder().encode(
    'event: token\r\ndata: {"text":"ação 🧭"}\r\n\r\nevent: done\ndata: {"status":"completed"}\n\n',
  );
  const response = new Response(
    new ReadableStream({
      start(controller) {
        for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
        controller.close();
      },
    }),
    { headers: { 'Content-Type': 'text/event-stream' } },
  );
  const events = [];
  await consumeSSE(response, (event) => events.push(event));
  assert.deepEqual(events, [
    { type: 'token', data: { text: 'ação 🧭' } },
    { type: 'done', data: { status: 'completed' } },
  ]);
});
test('SSE ignores heartbeats, handles multiline JSON, discards unfinished frame', () => {
  const events = [],
    parse = createSSEParser((event) => events.push(event));
  parse(
    ': heartbeat\n\nid: 7\nevent: sources\ndata: [\ndata: {"id":"document-1"}\ndata: ]\n\n',
  );
  parse('event: token\ndata: {"text":"not complete"}');
  assert.deepEqual(events, [{ type: 'sources', data: [{ id: 'document-1' }] }]);
});
test('Malformed data fails explicitly instead of inventing a response', () => {
  assert.throws(
    () => createSSEParser(() => {})('event: token\ndata: {broken}\n\n'),
    SyntaxError,
  );
  assert.throws(
    () => createSSEParser(() => {})('x'.repeat(2 * 1024 * 1024 + 1)),
    /2 MiB/,
  );
});
test('HTTP error surfaces API status and FastAPI detail, never HTML', async () => {
  await assert.rejects(
    () =>
      assertResponse(
        new Response('{"detail":"Quota exceeded"}', { status: 429 }),
      ),
    (error) =>
      error instanceof ApiError &&
      error.status === 429 &&
      error.message.includes('Quota exceeded'),
  );
  await assert.rejects(
    () =>
      assertResponse(
        new Response('<script>bad()</script>', {
          status: 502,
          statusText: 'Bad gateway',
        }),
      ),
    /502: Bad gateway/,
  );
  await assert.rejects(
    () =>
      consumeSSE(
        new Response('{}', { headers: { 'Content-Type': 'application/json' } }),
        () => {},
      ),
    /stream SSE/,
  );
});
test('Bearer travels in Authorization, never query string; server origin configurable', async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    return new Response('{}', {
      headers: { 'Content-Type': 'application/json' },
    });
  };
  try {
    const api = new AtlasApi('http://127.0.0.1:8010/');
    api.token = 'test-session';
    await api.post('/runs', {
      question: 'Olá',
      strategy: 'rag',
      memory_enabled: false,
    });
    assert.equal(calls[0].url, 'http://127.0.0.1:8010/api/runs');
    assert.equal(calls[0].init.headers.Authorization, 'Bearer test-session');
    assert.equal(JSON.parse(calls[0].init.body).memory_enabled, false);
    assert.equal(calls[0].url.includes('test-session'), false);
    assert.ok(calls[0].init.signal instanceof AbortSignal);
  } finally {
    globalThis.fetch = original;
  }
});
