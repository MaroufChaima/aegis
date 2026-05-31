import { useState } from 'react'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { useWebSocketContext } from './contexts/WebSocketContext'
import OverviewPage from './pages/OverviewPage'
import UAVFleetPage from './pages/UAVFleetPage'
import SimulationPage from './pages/SimulationPage'
import AnalyticsPage from './pages/AnalyticsPage'

const TABS = [
  { id: 'overview',   label: 'Overview' },
  { id: 'uavs',       label: 'UAV Fleet' },
  { id: 'analytics',  label: 'Analytics' },
  { id: 'simulation', label: 'Simulation' },
]

function StatusPill() {
  const { connectionStatus } = useWebSocketContext()
  const live = connectionStatus === 'connected'

  return (
    <div className="flex items-center gap-1.5 text-xs font-medium">
      <span
        className={`w-2 h-2 rounded-full ${
          live ? 'bg-green-400' : 'bg-red-500 animate-pulse'
        }`}
      />
      <span className={live ? 'text-green-400' : 'text-red-400'}>
        {live ? 'Live' : 'Reconnecting'}
      </span>
    </div>
  )
}

function NavBar({ activeTab, onTabChange }) {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <span className="text-white font-bold text-lg tracking-widest">AEGIS</span>
        <nav className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <StatusPill />
    </header>
  )
}

function AppShell() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <NavBar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview'   && <OverviewPage />}
        {activeTab === 'uavs'       && <UAVFleetPage />}
        {activeTab === 'analytics'  && <AnalyticsPage />}
        {activeTab === 'simulation' && <SimulationPage />}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <WebSocketProvider>
      <AppShell />
    </WebSocketProvider>
  )
}
