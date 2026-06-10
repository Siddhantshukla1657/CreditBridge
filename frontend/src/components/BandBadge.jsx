const BAND_CONFIG = {
  'Prime':      { bg: '#00C853', text: '#0A0A0A', border: '#00C853' },
  'Near-prime': { bg: '#69F0AE', text: '#0A0A0A', border: '#69F0AE' },
  'Subprime':   { bg: '#FFD740', text: '#0A0A0A', border: '#FFD740' },
  'High risk':  { bg: '#FF6D00', text: '#F5F0E8', border: '#FF6D00' },
  'Decline':    { bg: '#D50000', text: '#F5F0E8', border: '#D50000' },
}

export default function BandBadge({ band }) {
  const cfg = BAND_CONFIG[band] || { bg: '#5A5A5A', text: '#F5F0E8', border: '#5A5A5A' }
  return (
    <span style={{
      display: 'inline-block',
      background: cfg.bg,
      color: cfg.text,
      border: `2px solid #0A0A0A`,
      boxShadow: '2px 2px 0 #0A0A0A',
      padding: '4px 12px',
      fontFamily: "'Space Grotesk', sans-serif",
      fontWeight: 700,
      fontSize: '12px',
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      borderRadius: 0,
    }}>
      {band || 'UNKNOWN'}
    </span>
  )
}
