// Run in an isolated Node container: Windows reserves the unchanged upstream port 8000.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';

const nonce = randomUUID();
const upstream = createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'application/json' });
  response.end(JSON.stringify({ fixture: nonce, path: request.url }));
});
await new Promise((resolve, reject) => {
  upstream.once('error', reject);
  upstream.listen(8000, resolve);
});
const vite = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '15173', '--strictPort'], { stdio: 'inherit' });
try {
  const deadline = Date.now() + 60000;
  while (true) {
    try { await fetch('http://127.0.0.1:15173'); break; }
    catch (error) {
      if (Date.now() > deadline || vite.exitCode !== null) throw error;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  const results = [];
  for (const prefix of ['auth', 'query', 'documents', 'tenant', 'search', 'labels', 'roles', 'groups', 'system', 'analytics', 'llm-config', 'users']) {
    const path = `/${prefix}?smoke=1`;
    const response = await fetch(`http://127.0.0.1:15173${path}`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { fixture: nonce, path });
    results.push({ path, status: response.status, upstream_json: true });
  }
  for (const prefix of ['health', 'docs']) {
    const response = await fetch(`http://127.0.0.1:15173/${prefix}`);
    assert.match(response.headers.get('content-type'), /text\/html/);
    results.push({ path: `/${prefix}`, status: response.status, intentional_spa: true });
  }
  const record = { node: process.version, upstream: 'local JSON fixture; not the Zenith application', results };
  writeFileSync('/evidence/vite-smoke.json', JSON.stringify(record, null, 2));
  console.log(JSON.stringify(record));
} finally {
  vite.kill('SIGTERM');
  await new Promise(resolve => upstream.close(resolve));
}
