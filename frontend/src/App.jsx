import { useEffect, useState } from 'react'
import ZoneMap from './components/map/ZoneMap'
import { fetchVictims } from './api/victims'

export default function App() {
  const [victims, setVictims] = useState([])

  useEffect(() => {
    fetchVictims()
      .then(setVictims)
      .catch((err) => console.error('Failed to load victims:', err))
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-xl font-bold mb-4">AEGIS — Zone Map</h1>
      <div className="h-[600px] rounded-lg overflow-hidden">
        <ZoneMap victims={victims} />
      </div>
      <p className="mt-2 text-gray-400 text-sm">{victims.length} device(s) loaded</p>
    </div>
  )
}
