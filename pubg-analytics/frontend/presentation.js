export function formatNumber(value) {
  return Number(value).toFixed(2).replace(/\.00$/, '');
}

export function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[ch]));
}
