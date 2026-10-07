import assert from 'node:assert/strict';
import test from 'node:test';

import { analyzePlayer } from '../../frontend/api.js';

test('analyzePlayer sends the nickname using the API contract', async () => {
  let request;
  const expected = { player: { nickname: 'TestPlayer' }, matches: [] };
  const result = await analyzePlayer('TestPlayer', async (url, options) => {
    request = { url, options };
    return { ok: true, json: async () => expected };
  });

  assert.equal(request.url, '/analyze');
  assert.equal(request.options.method, 'POST');
  assert.equal(request.options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(request.options.body), { nickname: 'TestPlayer' });
  assert.equal(result, expected);
});

test('analyzePlayer surfaces structured API errors', async () => {
  await assert.rejects(
    analyzePlayer('missing', async () => ({
      ok: false,
      json: async () => ({ error: { message: 'Player not found' } })
    })),
    { message: 'Player not found' }
  );
});

test('analyzePlayer reports a non-JSON server response', async () => {
  await assert.rejects(
    analyzePlayer('TestPlayer', async () => ({
      ok: true,
      json: async () => { throw new SyntaxError('invalid JSON'); }
    })),
    { message: 'Server returned an invalid response.' }
  );
});
