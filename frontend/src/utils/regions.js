export const REGIONS = {
  algiers:     { label: 'Algiers',     center: [36.7321, 3.0841],  zoom: 14 },
  setif:       { label: 'Setif',       center: [36.1911, 5.4137],  zoom: 13 },
  bejaia:      { label: 'Bejaia',      center: [36.7500, 5.0833],  zoom: 13 },
  jijel:       { label: 'Jijel',       center: [36.8206, 5.7667],  zoom: 13 },
  constantine: { label: 'Constantine', center: [36.3650, 6.6147],  zoom: 13 },
  oran:        { label: 'Oran',        center: [35.6969, -0.6331], zoom: 13 },
  batna:       { label: 'Batna',       center: [35.5559, 6.1742],  zoom: 13 },
}

export const REGION_KEYS = Object.keys(REGIONS)

export const DEFAULT_REGION = 'algiers'

export function getRegion(key) {
  return REGIONS[key] ?? REGIONS[DEFAULT_REGION]
}
