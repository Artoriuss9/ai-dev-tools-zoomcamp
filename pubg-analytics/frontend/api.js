export async function analyzePlayer(nickname, fetchImpl = globalThis.fetch) {
  const response = await fetchImpl('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nickname })
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('Server returned an invalid response.');
  }

  if (!response.ok) {
    throw new Error(data?.error?.message || 'Analysis failed.');
  }
  return data;
}
