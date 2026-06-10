export default function FactorCard({ factor, index = 0 }) {
  const isPositive = factor.points > 0
  const barColor = isPositive ? '#00C853' : '#D50000'
  const chipBg = isPositive ? '#CCE0FF' : '#FFE0CC'
  const chipBorder = isPositive ? '#0066FF' : '#D50000'
  const chipText = isPositive ? '#0047B3' : '#D50000'

  return (
    <div
      className={`animate-slide-up stagger-${index + 1}`}
      style={{
        display: 'flex',
        alignItems: 'stretch',
        background: '#F5F0E8',
        border: '2.5px solid #0A0A0A',
        boxShadow: '4px 4px 0 #0A0A0A',
        marginBottom: '10px',
        overflow: 'hidden',
      }}
    >
      {/* Direction bar */}
      <div style={{ width: '4px', background: barColor, flexShrink: 0 }} />

      {/* Content */}
      <div style={{ flex: 1, padding: '14px 16px' }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '13px', color: '#0A0A0A', marginBottom: '4px' }}>
          {factor.label}
        </div>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A' }}>
          {factor.text.split('):')[1]?.trim() || factor.text}
        </div>
      </div>

      {/* SHAP chip */}
      <div style={{ display: 'flex', alignItems: 'center', paddingRight: '14px' }}>
        <span style={{
          background: chipBg,
          border: `1.5px solid ${chipBorder}`,
          color: chipText,
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 700,
          fontSize: '12px',
          padding: '4px 10px',
          whiteSpace: 'nowrap',
        }}>
          {factor.points > 0 ? `+${factor.points}` : factor.points} pts
        </span>
      </div>
    </div>
  )
}
