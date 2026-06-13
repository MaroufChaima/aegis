import { useState } from 'react'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { useWebSocketContext } from './contexts/WebSocketContext'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import OverviewPage from './pages/OverviewPage'
import UAVFleetPage from './pages/UAVFleetPage'
import SimulationPage from './pages/SimulationPage'
import AnalyticsPage from './pages/AnalyticsPage'
import RescueTeamsPage from './pages/RescueTeamsPage'
import { header, shell, tabActive, tabInactive } from './utils/themeClasses'

const TABS = [
  { id: 'overview',   label: 'Overview' },
  { id: 'uavs',       label: 'UAV Fleet' },
  { id: 'analytics',  label: 'Analytics' },
  { id: 'rescue',     label: 'Rescue Teams' },
  { id: 'simulation', label: 'Simulation' },
]

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium
                 border border-slate-200 text-slate-600 hover:bg-slate-100
                 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
      aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
      title={theme === 'light' ? 'Dark mode' : 'Light mode'}
    >
      {theme === 'light' ? (
        <>
          <span aria-hidden>🌙</span>
          <span>Dark</span>
        </>
      ) : (
        <>
          <span aria-hidden>☀️</span>
          <span>Light</span>
        </>
      )}
    </button>
  )
}

function StatusPill() {
  const { connectionStatus } = useWebSocketContext()
  const live = connectionStatus === 'connected'

  return (
    <div className="flex items-center gap-1.5 text-xs font-medium">
      <span
        className={`w-2 h-2 rounded-full ${
          live ? 'bg-green-500 dark:bg-green-400' : 'bg-red-500 animate-pulse'
        }`}
      />
      <span className={live ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}>
        {live ? 'Live' : 'Reconnecting'}
      </span>
    </div>
  )
}

function NavBar({ activeTab, onTabChange }) {
  return (
    <header className={`${header} px-6 py-3 flex items-center justify-between shadow-sm`}>
      <div className="flex items-center gap-6">
        <span className="text-slate-900 dark:text-white font-bold text-lg tracking-widest">
          AEGIS
        </span>
        <nav className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                activeTab === tab.id ? tabActive : tabInactive
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <StatusPill />
      </div>
    </header>
  )
}

function AppShell() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className={shell}>
      <NavBar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview'   && <OverviewPage />}
        {activeTab === 'uavs'       && <UAVFleetPage />}
        {activeTab === 'analytics'  && <AnalyticsPage />}
        {activeTab === 'rescue'     && <RescueTeamsPage />}
        {activeTab === 'simulation' && <SimulationPage />}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <WebSocketProvider>
        <AppShell />
      </WebSocketProvider>
    </ThemeProvider>
  )
}
