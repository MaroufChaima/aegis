import { useCallback, useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell, Tooltip as PieTooltip,
} from 'recharts'

// ── Colours ────────────────────────────────────────────────────────────────

const PRIORITY_PIE_COLORS = {
  P1: '#ef4444',   // red-500
  P2: '#f97316',   // orange-500
  P3: '#22c55e',   // green-500
}

// ── Helpers ─────────────────────────────────────────────────────────────────

async function apiFetch(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

/** Format a bin ISO timestamp to a short HH:MM label for the x-axis. */
function fmtBin(iso) {
  if (!iso) return ''
  return iso.slice(11, 16)   // "HH:MM"
}

// ── Sub-components ──────────────────────────────────────────────────────────

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-3xl font-bold ${accent ?? 'text-white'}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function SectionHeader({ title, subtitle }) {
  return (
    <div className="flex items-baseline justify-between mb-4">
      <h3 className="font-semibold text-white">{title}</h3>
      {subtitle && <span className="text-xs text-gray-500">{subtitle}</span>}
    </div>
  )
}

// Custom tooltip for BarChart
function BarTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

// Custom tooltip for PieChart
function PieTooltipContent({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs">
      <p style={{ color: PRIORITY_PIE_COLORS[name] }} className="font-bold">
        {name}: {value}
      </p>
    </div>
  )
}


// ── Main page ────────────────────────────────────────────────────────────────

/**
 * AnalyticsPage — live analytics dashboard.
 *
 * Fetches /api/analytics/summary and /api/analytics/timeseries on mount
 * and every 30 seconds thereafter.  Renders:
 *   - Four summary stat cards
 *   - BarChart: alert frequency per 5-minute bin (last 60 min)
 *   - Donut PieChart: victim distribution by priority (P1/P2/P3)
 *   - Horizontal bar breakdown: alerts by type
 */
export default function AnalyticsPage() {
  const [summary,    setSummary]    = useState(null)
  const [timeseries, setTimeseries] = useState([])
  const [error,      setError]      = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [sum, ts] = await Promise.all([
        apiFetch('/api/analytics/summary'),
        apiFetch('/api/analytics/timeseries'),
      ])
      setSummary(sum)
      setTimeseries(ts.bins ?? [])
      setError(null)
      setLastRefresh(new Date().toLocaleTimeString())
    } catch (err) {
      setError(`Analytics error: ${err.message}`)
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 30_000)
    return () => clearInterval(id)
  }, [refresh])

  // Derived pie data
  const pieData = summary
    ? Object.entries(summary.victims_by_priority).map(([name, value]) => ({ name, value }))
    : []
  const totalVictims = summary?.total_victims ?? 0

  // Alerts-by-type bar data (horizontal)
  const alertTypeData = summary
    ? Object.entries(summary.alerts_by_type ?? {})
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => ({ type: type.replace(/_/g, ' '), count }))
    : []

  return (
    <div className="space-y-8">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Analytics</h2>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-xs text-gray-500">Updated {lastRefresh}</span>
          )}
          <button
            onClick={refresh}
            className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded border border-gray-700 hover:border-gray-500 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-900/30 border border-red-700 px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* ── Summary stat cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Victims"
          value={summary?.total_victims}
          sub={`P1: ${summary?.victims_by_priority?.P1 ?? 0}  P2: ${summary?.victims_by_priority?.P2 ?? 0}  P3: ${summary?.victims_by_priority?.P3 ?? 0}`}
        />
        <StatCard
          label="Alerts (last 60 min)"
          value={summary?.total_alerts_last_hour}
          accent="text-red-400"
        />
        <StatCard
          label="Avg Heart Rate"
          value={summary?.avg_heart_rate != null ? `${summary.avg_heart_rate} bpm` : null}
        />
        <StatCard
          label="Network Coverage"
          value={summary?.network_coverage_pct != null ? `${summary.network_coverage_pct}%` : null}
          sub={`${summary?.uavs_online ?? 0} UAVs online`}
          accent={
            (summary?.network_coverage_pct ?? 100) >= 80
              ? 'text-green-400'
              : 'text-amber-400'
          }
        />
      </div>

      {/* ── Charts row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Bar chart — spans 2 columns */}
        <div className="lg:col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-6">
          <SectionHeader
            title="Alert Frequency"
            subtitle="5-minute bins · last 60 minutes"
          />
          {timeseries.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-16">No alert data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={timeseries} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={fmtBin}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<BarTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                <Legend
                  wrapperStyle={{ fontSize: 11, color: '#9ca3af', paddingTop: 8 }}
                  formatter={(v) => v === 'count' ? 'All alerts' : 'Critical'}
                />
                <Bar dataKey="count"          name="count"          fill="#6366f1" radius={[3,3,0,0]} />
                <Bar dataKey="critical_count" name="critical_count" fill="#ef4444" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Donut chart — 1 column */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <SectionHeader title="Priority Distribution" />
          {pieData.every((d) => d.value === 0) ? (
            <p className="text-gray-500 text-sm text-center py-16">No device data yet.</p>
          ) : (
            <>
              <div className="relative">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={88}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry) => (
                        <Cell key={entry.name} fill={PRIORITY_PIE_COLORS[entry.name] ?? '#6b7280'} />
                      ))}
                    </Pie>
                    <PieTooltip content={<PieTooltipContent />} />
                  </PieChart>
                </ResponsiveContainer>
                {/* Centre label — CSS overlay avoids Recharts viewBox prop issues */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-2xl font-bold text-white leading-none">{totalVictims}</span>
                  <span className="text-xs text-gray-400 mt-1">victims</span>
                </div>
              </div>
              {/* Legend */}
              <div className="flex justify-center gap-5 mt-2">
                {pieData.map((d) => (
                  <div key={d.name} className="flex items-center gap-1.5 text-xs">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ background: PRIORITY_PIE_COLORS[d.name] }}
                    />
                    <span className="text-gray-300">{d.name}</span>
                    <span className="text-gray-500">({d.value})</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Alerts by type breakdown ── */}
      {alertTypeData.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <SectionHeader title="Alerts by Type" subtitle="Last 60 minutes" />
          <div className="space-y-3">
            {alertTypeData.map(({ type, count }) => {
              const max   = alertTypeData[0].count
              const width = max > 0 ? Math.round((count / max) * 100) : 0
              return (
                <div key={type} className="flex items-center gap-3 text-sm">
                  <span className="w-40 shrink-0 text-gray-300 capitalize">{type}</span>
                  <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                  <span className="w-6 text-right text-gray-400 font-mono text-xs">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

    </div>
  )
}
