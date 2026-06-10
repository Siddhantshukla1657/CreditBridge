import { useEffect, useRef } from 'react'

const BAND_COLORS = {
  'Prime': '#00C853',
  'Near-prime': '#69F0AE',
  'Subprime': '#FFD740',
  'High risk': '#FF6D00',
  'Decline': '#D50000',
}

export default function ScoreGauge({ score = 0, band = '' }) {
  const arcRef = useRef(null)

  const MIN = 300, MAX = 900
  const clampedScore = Math.max(MIN, Math.min(MAX, score))
  const fraction = (clampedScore - MIN) / (MAX - MIN)

  // SVG geometry: center at (120, 100), radius 75, sweep 270° (starts at 135°)
  const cx = 120, cy = 100, r = 75
  const startAngle = 135
  const totalAngle = 270

  const polarToCartesian = (angle) => {
    const rad = (angle - 90) * Math.PI / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }

  const describeArc = (frac) => {
    const endAngle = startAngle + frac * totalAngle
    const start = polarToCartesian(startAngle)
    const end = polarToCartesian(endAngle)
    const largeArc = frac * totalAngle > 180 ? 1 : 0
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
  }

  const trackEnd = polarToCartesian(startAngle + totalAngle)
  const trackStart = polarToCartesian(startAngle)
  const trackPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 1 1 ${trackEnd.x} ${trackEnd.y}`

  const bandColor = BAND_COLORS[band] || '#5A5A5A'

  // Animate fill arc
  useEffect(() => {
    if (!arcRef.current) return
    const el = arcRef.current
    const length = el.getTotalLength()
    const target = length * fraction
    el.style.strokeDasharray = length
    el.style.strokeDashoffset = length
    requestAnimationFrame(() => {
      el.style.transition = 'stroke-dashoffset 600ms ease-out'
      el.style.strokeDashoffset = length - target
    })
  }, [fraction])

  // Compute label positions shifted radially outward to avoid overlap
  const polarToCartesianRadius = (angle, radius) => {
    const rad = (angle - 90) * Math.PI / 180
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) }
  }
  const labelStart = polarToCartesianRadius(startAngle, r + 26)
  const labelEnd = polarToCartesianRadius(startAngle + totalAngle, r + 26)

  return (
    <div style={{ textAlign: 'center', userSelect: 'none' }}>
      <svg width="100%" viewBox="0 0 240 210" style={{ display: 'block' }}>
        {/* Track */}
        <path d={trackPath} fill="none" stroke="#EDE7D9" strokeWidth="14" strokeLinecap="round"
          style={{ filter: 'drop-shadow(0 0 0 #0A0A0A)' }} />
        {/* Track border */}
        <path d={trackPath} fill="none" stroke="#0A0A0A" strokeWidth="16" strokeLinecap="round" opacity="0.15" />
        {/* Fill arc */}
        {score > 0 && (
          <path ref={arcRef} d={describeArc(fraction)} fill="none"
            stroke={bandColor} strokeWidth="14" strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 4px ${bandColor}44)` }} />
        )}
        {/* Score number */}
        <text x={cx} y={cy - 10} textAnchor="middle" dominantBaseline="middle"
          style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '42px', fill: '#0A0A0A' }}
          className="animate-count-up">
          {score > 0 ? clampedScore : '—'}
        </text>
        {/* Band label */}
        <text x={cx} y={cy + 22} textAnchor="middle"
          style={{
            fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
            fill: bandColor, letterSpacing: '0.08em', textTransform: 'uppercase'
          }}>
          {band || 'NO SCORE'}
        </text>
        {/* Min label — anchored to arc start point */}
        <text
          x={labelStart.x}
          y={labelStart.y}
          textAnchor="middle"
          dominantBaseline="middle"
          style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', fill: '#5A5A5A' }}
        >300</text>
        {/* Max label — anchored to arc end point */}
        <text
          x={labelEnd.x}
          y={labelEnd.y}
          textAnchor="middle"
          dominantBaseline="middle"
          style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', fill: '#5A5A5A' }}
        >900</text>
      </svg>
      <p style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A', marginTop: '4px' }}>
        Based on 18 alternative data signals
      </p>
    </div>
  )
}
