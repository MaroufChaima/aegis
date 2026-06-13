/** User vs Victim display label based on emergency_status. */

export function getDisplayLabel(user) {
  const status = user?.emergency_status
  if (status === 'victim' || status === 'deceased') return 'Victim'
  return 'User'
}

export function isVictimStatus(user) {
  return user?.emergency_status === 'victim' || user?.emergency_status === 'deceased'
}
