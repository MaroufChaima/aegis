import OverviewPage from './pages/OverviewPage'

function NavBar() {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center">
      <span className="text-white font-bold text-lg tracking-widest">AEGIS</span>
    </header>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <NavBar />
      <main className="max-w-7xl mx-auto px-4 py-6">
        <OverviewPage />
      </main>
    </div>
  )
}
