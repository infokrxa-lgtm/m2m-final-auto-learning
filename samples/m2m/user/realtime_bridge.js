const KRXA_API = 'http://127.0.0.1:8787/api/input-flow';
async function krxaRealtimeRun(payload) {
  const res = await fetch(KRXA_API, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('KRXA realtime engine error: ' + res.status);
  return await res.json();
}
