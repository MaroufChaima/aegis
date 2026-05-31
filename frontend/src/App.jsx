import { useEffect, useState } from 'react'
import ZoneMap from './components/map/ZoneMap'
import VictimTable from './components/victims/VictimTable'
import { fetchVictims } from './api/victims'

export default function App() {
  const [victims, setVictims] = useState([])

  useEffect(() => {
    fetchVictims()
      .then(setVictims)
      .catch((err) => console.error('Failed to load victims:', err))
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 space-y-6">
      <h1 className="text-xl font-bold">AEGIS — Zone Map</h1>
      <div className="h-[500px] rounded-lg overflow-hidden">
        <ZoneMap victims={victims} />
      </div>
      <VictimTable victims={victims} />
      <p className="text-gray-400 text-sm">{victims.length} device(s) loaded</p>
    </div>
  )
}
