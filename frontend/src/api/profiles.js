import { API_BASE_URL } from '../utils/constants'

/**
 * Fetches the complete physiological profile for one victim including
 * personalized normal ranges. Used by VictimDetail to display
 * profile-specific context.
 **/
export async function fetchVictimProfile(victimId) {
  const response = await fetch(`${API_BASE_URL}/api/victims/${victimId}/profile`)
  if (!response.ok) throw new Error(response.status)
  return response.json()
}

/**
 * Fetches all victims from the new WBAN victims table.
 * Will replace fetchVictims() in migration phase M7.
 **/
export async function fetchAllVictimsNew() {
  const response = await fetch(`${API_BASE_URL}/api/victims-new`)
  if (!response.ok) throw new Error(response.status)
  return response.json()
}
