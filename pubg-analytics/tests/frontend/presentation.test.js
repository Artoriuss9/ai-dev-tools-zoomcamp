import assert from 'node:assert/strict';
import test from 'node:test';

import { escapeHtml, formatNumber, formatSeasonTitle } from '../../frontend/presentation.js';

test('formatNumber renders numeric values consistently', () => {
  assert.equal(formatNumber(2), '2');
  assert.equal(formatNumber(2.345), '2.35');
});

test('formatSeasonTitle displays only the season number', () => {
  assert.equal(formatSeasonTitle('division.bro.official.pc-2018-43'), 'Current season: 43');
  assert.equal(formatSeasonTitle('unexpected-season-id'), 'Current season');
});

test('escapeHtml encodes markup-sensitive characters', () => {
  assert.equal(escapeHtml(`<img src="'x'">`), '&lt;img src=&quot;&#39;x&#39;&quot;&gt;');
});
