import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine, ResponsiveContainer } from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]
  const isRisk = d.value > 0
  return (
    <div style={{ background: '#F5F0E8', border: '2px solid #0A0A0A', padding: '8px 12px',
      fontFamily: "'DM Mono', monospace", fontSize: '12px', boxShadow: '3px 3px 0 #0A0A0A' }}>
      <div style={{ fontWeight: 500, textTransform: 'capitalize' }}>{d.payload.name}</div>
      <div style={{ color: isRisk ? '#D50000' : '#00C853', fontWeight: 500 }}>
        SHAP: {d.value > 0 ? '+' : ''}{d.value}
      </div>
      <div style={{ color: '#5A5A5A', fontSize: '11px' }}>
        {isRisk ? '↑ Increases default risk' : '↓ Reduces default risk (positive)'}
      </div>
    </div>
  )
}

export default function WaterfallChart({ data = [] }) {
  if (!data.length) return (
    <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#5A5A5A', fontFamily: "'DM Mono', monospace", fontSize: '13px' }}>
      No waterfall data
    </div>
  )

  // Filter out totals for display, show only feature bars
  const filtered = data.filter(d => !d.is_total)

  const chartData = filtered.map(d => ({
    name: d.name
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .toLowerCase(),
    value: parseFloat(d.value.toFixed(3)),
    // Negative SHAP = reduces default risk = GOOD = green
    // Positive SHAP = increases default risk = BAD = red
    fill: d.value <= 0 ? '#00C853' : '#D50000',
  }))

  // Sort by absolute value so largest bars are on top
  chartData.sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  // Compute a nice left margin based on longest label
  const maxLabelLen = Math.max(...chartData.map(d => d.name.length))
  const yAxisWidth = Math.min(180, Math.max(120, maxLabelLen * 7))

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 40)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 4, right: 48, left: 0, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="4 4" stroke="#C0B9AC" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontFamily: "'DM Mono', monospace", fontSize: 11, fill: '#5A5A5A' }}
          axisLine={{ stroke: '#0A0A0A', strokeWidth: 2 }}
          tickLine={false}
          tickFormatter={v => v.toFixed(2)}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={yAxisWidth}
          tick={{ fontFamily: "'DM Mono', monospace", fontSize: 11, fill: '#0A0A0A' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => v.length > 22 ? v.slice(0, 21) + '…' : v}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,102,255,0.08)' }} />
        <ReferenceLine x={0} stroke="#0A0A0A" strokeWidth={2} />
        <Bar dataKey="value" radius={0} strokeWidth={1.5}>
          {chartData.map((entry, idx) => (
            <Cell key={idx} fill={entry.fill} stroke="#0A0A0A" strokeWidth={1.5} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
