import { useCallback, useEffect, useState } from 'react'

const SCENARIOS = [
  {
    name: 'sos_wave',
    label: 'SOS Wave',
    description: '3 random devices raise SOS simultaneously.',
    color: 'red',
  },
  {
    name: 'mass_casualty',
    label: 'Mass Casualty Event',
    description: '5 devices drop to immediately critical vitals.',
    color: 'red',
  },
  {
    name: 'uav_failure',
    label: 'UAV Failure',
    description: 'One UAV loses power and goes offline.',
    color: 'amber',
  },
  {
    name: 'gradual_deterioration',
    label: 'Gradual Deterioration',
    description: "One device's HR climbs steadily toward cardiac arrest (~2.5 min).",
    color: 'amber',
  },
  {
    name: 'network_partition',
    label: 'Network Partition',
    description: 'One UAV relay zone loses LoRa connectivity for ~2 minutes.',
    color: 'blue',
  },
]

const COLOR_CLASSES = {
  red:   { btn: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',   badge: 'bg-red-500/20 text-red-400 border-red-500/30' },
  amber: { btn: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500', badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  blue:  { btn: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500', badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
}

async function apiFetch(path, method = 'GET', body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(path, opts)
  if (!res.ok) throw new Error(`${method} ${path} → ${res.status}`)
  return res.json()
}

/**
 * SimulationPage — Simulation Control Panel.
 *
 * Polls GET /api/simulation/status every 5 seconds to keep the running
 * indicator in sync.  Pause, Resume, and Scenario buttons call the
 * corresponding POST endpoints immediately.
 */
export default function SimulationPage() {
  const [running,         setRunning]         = useState(true)
  const [pendingScenario, setPendingScenario] = useState(null)
  const [busy,            setBusy]            = useState(false)
  const [lastAction,      setLastAction]      = useState(null)
  const [error,           setError]           = useState(null)

  const refreshStatus = useCallback(async () => {
    try {
      const state = await apiFetch('/api/simulation/status')
      setRunning(state.running ?? true)
      setPendingScenario(state.scenario ?? null)
      setError(null)
    } catch (err) {
      setError('Cannot reach backend — is uvicorn running?')
    }
  }, [])

  // Poll status every 5 s
  useEffect(() => {
    refreshStatus()
    const id = setInterval(refreshStatus, 5000)
    return () => clearInterval(id)
  }, [refreshStatus])

  async function handlePause() {
    setBusy(true)
    try {
      await apiFetch('/api/simulation/pause', 'POST')
      setRunning(false)
      setLastAction('Simulator paused.')
    } catch {
      setLastAction('Pause failed — check backend logs.')
    } finally {
      setBusy(false)
    }
  }

  async function handleResume() {
    setBusy(true)
    try {
      await apiFetch('/api/simulation/resume', 'POST')
      setRunning(true)
      setLastAction('Simulator resumed.')
    } catch {
      setLastAction('Resume failed — check backend logs.')
    } finally {
      setBusy(false)
    }
  }

  async function handleScenario(name) {
    setBusy(true)
    try {
      await apiFetch('/api/simulation/scenario', 'POST', { name })
      setPendingScenario(name)
      setLastAction(`Scenario "${name}" queued — will apply on next tick.`)
    } catch {
      setLastAction('Scenario trigger failed — check backend logs.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-8">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Simulation Control</h2>
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              running ? 'bg-green-400' : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className={`text-sm font-semibold ${running ? 'text-green-400' : 'text-amber-400'}`}>
            {running ? 'Running' : 'Paused'}
          </span>
        </div>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="rounded-lg bg-red-900/30 border border-red-700 px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* ── Status + Pause / Resume ── */}
      <section className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-widest">
          Simulator Control
        </h3>

        {pendingScenario && (
          <p className="text-xs text-amber-400">
            Pending scenario: <span className="font-mono font-bold">{pendingScenario}</span> (awaiting next tick)
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={handlePause}
            disabled={busy || !running}
            className="px-5 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:opacity-40
                       disabled:cursor-not-allowed text-white text-sm font-semibold
                       transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            ⏸ Pause
          </button>
          <button
            onClick={handleResume}
            disabled={busy || running}
            className="px-5 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-40
                       disabled:cursor-not-allowed text-white text-sm font-semibold
                       transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            ▶ Resume
          </button>
        </div>

        {lastAction && (
          <p className="text-xs text-gray-400 italic">{lastAction}</p>
        )}
      </section>

      {/* ── Scenario Triggers ── */}
      <section className="bg-gray-800 border border-gray-700 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-widest">
            Emergency Scenarios
          </h3>
          <span className="text-xs text-gray-500">
            Applied on the simulator's next tick (~{15}s delay)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SCENARIOS.map((sc) => {
            const cls = COLOR_CLASSES[sc.color]
            return (
              <div
                key={sc.name}
                className="bg-gray-900 border border-gray-700 rounded-lg p-4 flex flex-col gap-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-white text-sm">{sc.label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{sc.description}</p>
                  </div>
                  {pendingScenario === sc.name && (
                    <span className={`shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full border ${cls.badge}`}>
                      Queued
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleScenario(sc.name)}
                  disabled={busy || !running}
                  className={`w-full py-1.5 rounded-lg text-white text-xs font-bold
                              transition-colors focus:outline-none focus:ring-2
                              disabled:opacity-40 disabled:cursor-not-allowed
                              ${cls.btn}`}
                >
                  Trigger
                </button>
              </div>
            )
          })}
        </div>
      </section>

    </div>
  )
}
