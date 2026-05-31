/**
 * Fetches the current list of all UAVs from the REST endpoint.
 * Used for the initial seed of the UAV Fleet page before WebSocket
 * uav_update messages take over.
 *
 * @returns {Promise<Array>} Resolves to an array of UAV objects.
 */
export async function fetchUAVs() {
  const res = await fetch('/api/uavs')
  if (!res.ok) throw new Error(`GET /api/uavs failed: ${res.status}`)
  return res.json()
}
