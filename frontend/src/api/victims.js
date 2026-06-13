export async function fetchVictims(region) {
  const url = region ? `/api/victims?region=${encodeURIComponent(region)}` : '/api/victims'
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status}`)
  }
  return response.json()
}
