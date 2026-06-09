import React from 'react'

/**
 * Displays a badge indicating that a sensor value was estimated rather than
 * directly measured. Shows the confidence percentage. The tilde prefix (~)
 * follows scientific convention for estimated values. Returns null when the
 * value is directly measured so no badge appears.
 **/
export default function ImputationBadge({ method, confidence }) {
  if (!method) return null

  if (method === 'unresolvable') {
    return (
      <span
        className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 ml-1"
        title="Sensor failed — no value available"
      >
        ⚠ NO DATA
      </span>
    )
  }

  const pct = Math.round((confidence || 0) * 100)

  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 ml-1"
      title={`Estimated value (${method}). Confidence: ${pct}%`}
    >
      ~{pct}%
    </span>
  )
}
