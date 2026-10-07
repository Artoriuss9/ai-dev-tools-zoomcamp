import assert from 'node:assert/strict';
import test from 'node:test';

import { escapeHtml, formatNumber } from '../../frontend/presentation.js';

test('formatNumber renders numeric values consistently', () => {
  assert.equal(formatNumber(2), '2');
  assert.equal(formatNumber(2.345), '2.35');
});

test('escapeHtml encodes markup-sensitive characters', () => {
  assert.equal(escapeHtml(`<img src="'x'">`), '&lt;img src=&quot;&#39;x&#39;&quot;&gt;');
});
