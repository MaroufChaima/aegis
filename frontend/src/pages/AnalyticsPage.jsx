import { useCallback, useEffect, useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocketContext } from '../contexts/WebSocketContext'
import { card, errorBanner, muted, pageTitle } from '../utils/themeClasses'
import { REGIONS, REGION_KEYS } from '../utils/regions'
import { fetchAnalyticsSummary, fetchAnalyticsTimeseries } from '../api/analytics'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell,
} from 'recharts'

const PRIORITY_COLORS = { P1: '#ef4444', P2: '#f97316', P3: '#22c55e' }

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`${card} p-4`}>
      <p className={`text-xs ${muted} uppercase tracking-widest mb-1`}>{label}</p>
      <p className={`text-2xl font-bold ${accent ?? 'text-slate-900 dark:text-white'}`}>{value ?? '—'}</p>
      {sub && <p className={`text-xs ${muted} mt-1`}>{sub}</p>}
    </div>
  )
}

export default function AnalyticsPage() {
  const { isDark } = useTheme()
  const { region, setRegion } = useWebSocketContext()
  const [scope, setScope] = useState('global')
  const [summary, setSummary] = useState(null)
  const [timeseries, setTimeseries] = useState([])
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const reg = scope === 'regional' ? region : undefined
      const [sum, ts] = await Promise.all([
        fetchAnalyticsSummary(scope, reg),
        fetchAnalyticsTimeseries(),
      ])
      setSummary(sum)
      setTimeseries(ts.bins ?? [])
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [scope, region])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 30_000)
    return () => clearInterval(id)
  }, [refresh])

  const pieData = summary
    ? Object.entries(summary.victims_by_priority || {}).map(([name, value]) => ({ name, value }))
    : []

  const profileData = summary
    ? Object.entries(summary.users_by_profile || {}).map(([name, value]) => ({ name, value }))
    : []

  const chartGrid = isDark ? '#374151' : '#e2e8f0'
  const chartTick = isDark ? '#9ca3af' : '#64748b'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className={pageTitle}>Analytics</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setScope('global')}
            className={`px-3 py-1 rounded text-sm ${scope === 'global' ? 'bg-blue-600 text-white' : 'border border-slate-300 dark:border-gray-600'}`}
          >
            Global
          </button>
          <button
            type="button"
            onClick={() => setScope('regional')}
            className={`px-3 py-1 rounded text-sm ${scope === 'regional' ? 'bg-blue-600 text-white' : 'border border-slate-300 dark:border-gray-600'}`}
          >
            Regional
          </button>
          {scope === 'regional' && (
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="rounded border border-slate-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
            >
              {REGION_KEYS.map((k) => (
                <option key={k} value={k}>{REGIONS[k].label}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {error && <div className={errorBanner}>{error}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Total Users" value={summary?.total_users} />
        <StatCard label="Active Emergencies" value={summary?.active_emergencies} accent="text-red-600 dark:text-red-400" />
        <StatCard label="Active Alerts (60m)" value={summary?.active_alerts} />
        <StatCard label="Deaths" value={summary?.deaths ?? 0} />
        <StatCard label="Rescued Users" value={summary?.rescued_users ?? 0} accent="text-green-600 dark:text-green-400" />
        <StatCard label="UAVs Active" value={summary?.active_uavs} sub={`${summary?.uavs_standby ?? 0} standby`} />
        <StatCard label="UAVs Inactive" value={summary?.inactive_uavs} />
        <StatCard label="Rescue Teams" value={summary?.total_rescue_teams} />
        <StatCard label="Network Coverage" value={summary?.network_coverage_pct != null ? `${summary.network_coverage_pct}%` : null} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={`${card} p-5`}>
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Priority Distribution</h3>
          {pieData.every((d) => d.value === 0) ? (
            <p className={`${muted} text-sm text-center py-12`}>No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} dataKey="value" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {pieData.map((e) => (
                    <Cell key={e.name} fill={PRIORITY_COLORS[e.name] ?? '#6b7280'} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className={`${card} p-5`}>
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Users by Profile</h3>
          {profileData.length === 0 ? (
            <p className={`${muted} text-sm text-center py-12`}>No data</p>
          ) : (
            <div className="space-y-2">
              {profileData.map(({ name, value }) => (
                <div key={name} className="flex justify-between text-sm">
                  <span className="capitalize text-slate-700 dark:text-gray-300">{name}</span>
                  <span className="font-mono">{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {scope === 'global' && summary?.regional_comparisons?.length > 0 && (
        <div className={`${card} p-5`}>
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Regional Comparison</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {summary.regional_comparisons.map((r) => (
              <div key={r.region} className="rounded border border-slate-200 dark:border-gray-700 p-3">
                <p className="font-medium capitalize">{REGIONS[r.region]?.label ?? r.region}</p>
                <p className={muted}>Users: {r.user_count}</p>
                <p className="text-red-600 dark:text-red-400">Emergencies: {r.active_emergencies}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={`${card} p-5`}>
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Alert Frequency (60 min)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={timeseries}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartGrid} />
            <XAxis dataKey="timestamp" tickFormatter={(t) => t?.slice(11, 16)} tick={{ fill: chartTick, fontSize: 10 }} />
            <YAxis allowDecimals={false} tick={{ fill: chartTick, fontSize: 10 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#6366f1" name="All alerts" />
            <Bar dataKey="critical_count" fill="#ef4444" name="Critical" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
