import { WebSocketProvider } from './contexts/WebSocketContext'
import { useWebSocketContext } from './contexts/WebSocketContext'
import OverviewPage from './pages/OverviewPage'

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

function NavBar() {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
      <span className="text-white font-bold text-lg tracking-widest">AEGIS</span>
      <StatusPill />
    </header>
  )
}

export default function App() {
  return (
    <WebSocketProvider>
      <div className="min-h-screen bg-gray-900 text-white">
        <NavBar />
        <main className="max-w-7xl mx-auto px-4 py-6">
          <OverviewPage />
        </main>
      </div>
    </WebSocketProvider>
  )
}
