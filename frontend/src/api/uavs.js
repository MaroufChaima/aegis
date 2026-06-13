export async function fetchUAVs(region) {
  const url = region ? `/api/uavs?region=${encodeURIComponent(region)}` : '/api/uavs'
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`)
  return res.json()
}
