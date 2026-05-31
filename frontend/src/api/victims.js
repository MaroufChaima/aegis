/**
 * Fetches all registered devices with their current status and latest AI scores.
 * Used on initial page load to populate the victim table and map markers.
 *
 * Calls GET /api/victims — Vite proxies this to http://localhost:8000/api/victims.
 *
 * @returns {Promise<Array>} Array of victim objects as defined in API_FLOW.md
 * @throws {Error} if the network request fails or the server returns a non-OK status
 */
export async function fetchVictims() {
  const response = await fetch('/api/victims')
  if (!response.ok) {
    throw new Error(`GET /api/victims failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}
