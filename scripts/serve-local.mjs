#!/usr/bin/env node
// Serves a built client and its API on one loopback origin, including SSE.
import http from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: {
  client: { type: 'string', default: 'angular' },
  port: { type: 'string', default: '5180' },
  api: { type: 'string', default: 'http://127.0.0.1:8000' },
} });
if (!['angular', 'react'].includes(values.client)) throw new Error('--client must be angular or react');
const port = Number(values.port);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid --port');
const api = new URL(values.api);
if (api.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(api.hostname)
  || api.username || api.password || api.pathname !== '/' || api.search || api.hash) {
  throw new Error('--api must be a local HTTP origin, without credentials or a path');
}
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'apps',
  `web-${values.client}`, 'dist', ...(values.client === 'angular' ? ['browser'] : []));
await stat(resolve(root, 'index.html')).catch(() => {
  throw new Error(`Build the client first: npm --prefix apps/web-${values.client} run build`);
});
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
const server = http.createServer(async (req, res) => {
  if (values.client === 'angular' && req.url === '/config.js' && ['GET', 'HEAD'].includes(req.method)) {
    res.writeHead(200, { 'Content-Type': 'text/javascript; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(req.method === 'HEAD' ? undefined : 'window.ATLAS_API_URL = window.location.origin;\n');
    return;
  }
  if (req.url === '/api' || req.url.startsWith('/api/')) {
    const upstream = http.request(new URL(req.url, api), {
      method: req.method, headers: { ...req.headers, host: api.host },
    }, (reply) => {
      res.writeHead(reply.statusCode ?? 502, reply.headers);
      reply.pipe(res);
      reply.on('error', () => res.destroy());
    });
    upstream.on('error', () => {
      if (!res.headersSent) res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: 'Local Atlas API unavailable' }));
    });
    res.on('close', () => upstream.destroy());
    req.pipe(upstream);
    return;
  }
  if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405); res.end(); return; }
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let file = resolve(root, `.${pathname}`);
    if (file !== root && !file.startsWith(root + sep)) { res.writeHead(403); res.end(); return; }
    let info = await stat(file).catch(() => null);
    if (info?.isDirectory()) { file = resolve(file, 'index.html'); info = await stat(file).catch(() => null); }
    if (!info?.isFile() && !extname(pathname)) {
      file = resolve(root, 'index.html'); info = await stat(file);
    }
    if (!info?.isFile()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': types[extname(file)] ?? 'application/octet-stream',
      'Content-Length': info.size, 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store' });
    if (req.method === 'HEAD') res.end();
    else createReadStream(file).on('error', () => res.destroy()).pipe(res);
  } catch { if (!res.headersSent) res.writeHead(400); res.end(); }
});
server.listen(port, '127.0.0.1', () => {
  console.log(`Atlas ${values.client}: http://127.0.0.1:${port}`);
  console.log(`Use http://127.0.0.1:${port} as the API address in the login form.`);
});
