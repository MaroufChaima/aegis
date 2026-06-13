export async function fetchAnalyticsSummary(scope = 'global', region) {
  const params = new URLSearchParams({ scope })
  if (scope === 'regional' && region) params.set('region', region)
  const res = await fetch(`/api/analytics/summary?${params}`)
  if (!res.ok) throw new Error(`GET /api/analytics/summary failed: ${res.status}`)
  return res.json()
}

export async function fetchAnalyticsTimeseries() {
  const res = await fetch('/api/analytics/timeseries')
  if (!res.ok) throw new Error(`GET /api/analytics/timeseries failed: ${res.status}`)
  return res.json()
}
