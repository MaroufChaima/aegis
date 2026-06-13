const BASE = '/api/rescue-teams'

export async function fetchRescueTeams(region) {
  const url = region ? `${BASE}?region=${encodeURIComponent(region)}` : BASE
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GET ${url} → ${res.status}`)
  return res.json()
}

export async function fetchRescueTeam(teamId) {
  const res = await fetch(`${BASE}/${teamId}`)
  if (!res.ok) throw new Error(`GET ${BASE}/${teamId} → ${res.status}`)
  return res.json()
}

export async function fetchRescuer(rescuerId) {
  const res = await fetch(`${BASE}/rescuer/${rescuerId}`)
  if (!res.ok) throw new Error(`GET ${BASE}/rescuer/${rescuerId} → ${res.status}`)
  return res.json()
}
