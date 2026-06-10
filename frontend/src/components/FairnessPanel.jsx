export default function FairnessPanel({ report }) {
  if (!report || !report.groups) {
    return (
      <div style={{ padding: '16px', fontFamily: "'DM Mono', monospace", fontSize: '13px', color: '#5A5A5A',
        border: '2.5px solid #0A0A0A', background: '#F5F0E8' }}>
        No fairness audit data available. Train the model to generate a report.
      </div>
    )
  }

  const metrics = [
    { key: 'demographic_parity_disparity', label: 'Dem. Parity' },
    { key: 'equal_opportunity_disparity', label: 'Equal Opp.' },
    { key: 'fpr_parity_disparity', label: 'FPR Parity' },
  ]

  const threshold = report.disparity_threshold || 0.10
  const groups = Object.entries(report.groups)

  const cellStyle = (value) => {
    if (value === undefined || value === null) return { bg: '#EDE7D9', text: '#5A5A5A', border: '#C0B9AC' }
    const pass = value >= (1 - threshold) && value <= (1 + threshold)
    return pass
      ? { bg: '#CCF5D9', text: '#005523', border: '#00C853' }
      : { bg: '#FFE0E0', text: '#D50000', border: '#D50000' }
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "'DM Mono', monospace" }}>
        <thead>
          <tr>
            <th style={{ padding: '8px 12px', background: '#0A0A0A', color: '#F5F0E8',
              fontFamily: "'Space Grotesk', sans-serif", fontSize: '11px', letterSpacing: '0.08em',
              textTransform: 'uppercase', textAlign: 'left', fontWeight: 700 }}>
              Group
            </th>
            <th style={{ padding: '8px 12px', background: '#0A0A0A', color: '#F5F0E8',
              fontFamily: "'Space Grotesk', sans-serif", fontSize: '11px', letterSpacing: '0.08em',
              textTransform: 'uppercase', textAlign: 'left', fontWeight: 700 }}>
              Attribute
            </th>
            {metrics.map(m => (
              <th key={m.key} style={{ padding: '8px 12px', background: '#0A0A0A',
                fontFamily: "'Space Grotesk', sans-serif", fontSize: '11px', letterSpacing: '0.08em',
                textTransform: 'uppercase', textAlign: 'center', fontWeight: 700, color: '#EDE7D9' }}>
                {m.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {groups.map(([groupName, attrs]) =>
            Object.entries(attrs).map(([attrVal, disparity], aIdx) => {
              return (
                <tr key={`${groupName}-${attrVal}`}>
                  {aIdx === 0 && (
                    <td rowSpan={Object.keys(attrs).length}
                      style={{ padding: '8px 12px', borderBottom: '1px solid #2A2A2A',
                        fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
                        fontSize: '12px', letterSpacing: '0.05em', textTransform: 'uppercase',
                        background: '#EDE7D9', verticalAlign: 'top' }}>
                      {groupName}
                    </td>
                  )}
                  <td style={{ padding: '8px 12px', borderBottom: '1px solid #2A2A2A',
                    fontSize: '12px', fontWeight: 500 }}>
                    {attrVal}
                  </td>
                  {metrics.map(m => {
                    const val = disparity[m.key]
                    const style = cellStyle(val)
                    return (
                      <td key={m.key} style={{ padding: '8px 12px', textAlign: 'center',
                        borderBottom: '1px solid #2A2A2A',
                        background: style.bg, color: style.text,
                        border: `1.5px solid ${style.border}`,
                        fontWeight: 700, fontSize: '12px' }}>
                        {val !== undefined ? val.toFixed(3) : '—'}
                      </td>
                    )
                  })}
                </tr>
              )
            })
          )}
        </tbody>
      </table>
      <div style={{ marginTop: '10px', fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A' }}>
        Threshold: ±{(threshold * 100).toFixed(0)}% from reference group (1.0 = parity)
        &nbsp;|&nbsp;
        <span style={{ color: '#005523' }}>■ Pass</span>
        &nbsp;
        <span style={{ color: '#D50000' }}>■ Fail</span>
      </div>
    </div>
  )
}
