import { X, Cpu, TrendingUp, Shield } from 'lucide-react'

const MetricRow = ({ label, value, target, unit = '' }) => {
  const numVal = parseFloat(value)
  const numTarget = parseFloat(target)
  const pass = !isNaN(numVal) && !isNaN(numTarget) ? numVal >= numTarget : null
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '10px 0', borderBottom: '1px dashed #C0B9AC' }}>
      <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '13px', color: '#5A5A5A' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '15px', color: '#0A0A0A' }}>
          {value !== undefined && value !== null ? `${parseFloat(value).toFixed(4)}${unit}` : '—'}
        </span>
        {pass !== null && (
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '11px',
            padding: '2px 8px', background: pass ? '#CCF5D9' : '#FFE0E0',
            color: pass ? '#005523' : '#D50000', border: `1.5px solid ${pass ? '#00C853' : '#D50000'}` }}>
            {pass ? 'PASS' : 'FAIL'}
          </span>
        )}
      </div>
    </div>
  )
}

export default function ModelCardModal({ card, onClose }) {
  if (!card) return null

  const metrics = card.performance_metrics || {}
  const fairness = card.fairness_audit || {}

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(10,10,10,0.6)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}
      onClick={onClose}>
      <div style={{ background: '#F5F0E8', border: '2.5px solid #0A0A0A', boxShadow: '8px 8px 0 #0A0A0A',
        maxWidth: '560px', width: '100%', maxHeight: '90vh', overflow: 'auto' }}
        onClick={e => e.stopPropagation()}
        className="animate-slide-up">
        {/* Header */}
        <div style={{ background: '#0A0A0A', padding: '20px 24px', display: 'flex',
          justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '18px',
              color: '#F5F0E8', letterSpacing: '0.02em' }}>MODEL CARD</div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A', marginTop: '4px' }}>
              {card.model_version || 'v1.0.0'} — {card.framework || 'XGBoost + Platt'}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: '#F5F0E8', padding: '4px' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px' }}>
          {/* Model info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Cpu size={16} color="#0066FF" />
            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
              letterSpacing: '0.06em', textTransform: 'uppercase', color: '#0066FF' }}>
              {card.model_name || 'Alternative Credit Scoring Model'}
            </span>
          </div>

          {/* Performance Metrics */}
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
            letterSpacing: '0.08em', textTransform: 'uppercase', color: '#5A5A5A', marginBottom: '12px',
            display: 'flex', alignItems: 'center', gap: '6px' }}>
            <TrendingUp size={14} />
            PERFORMANCE METRICS
          </div>
          <MetricRow label="AUC (ROC)" value={metrics.AUC} target={0.88} />
          <MetricRow label="KS Statistic" value={metrics.KS_Statistic} target={0.40} />
          <MetricRow label="ECE (Calibration)" value={metrics.Expected_Calibration_Error_ECE} target={null} />
          <MetricRow label="Brier Score" value={metrics.Brier_Score} target={null} />

          {/* Fairness */}
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
            letterSpacing: '0.08em', textTransform: 'uppercase', color: '#5A5A5A', marginTop: '24px',
            marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Shield size={14} />
            FAIRNESS AUDIT
          </div>
          <div style={{ padding: '12px', background: fairness.passed === false ? '#FFE0E0' : '#CCF5D9',
            border: `2px solid ${fairness.passed === false ? '#D50000' : '#00C853'}` }}>
            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
              color: fairness.passed === false ? '#D50000' : '#005523' }}>
              {fairness.passed === false
                ? `⚠ ${(fairness.violations || []).length} FAIRNESS VIOLATION(S) DETECTED`
                : fairness.passed === true
                ? '✓ ALL FAIRNESS CHECKS PASSED'
                : 'AUDIT NOT RUN'}
            </span>
            {fairness.disparity_threshold && (
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px',
                color: '#5A5A5A', marginTop: '6px' }}>
                Threshold: ±{(fairness.disparity_threshold * 100).toFixed(0)}% disparity across gender, geography, income
              </div>
            )}
          </div>
          {/* Violation Details */}
          {fairness.passed === false && (fairness.violations || []).length > 0 && (
            <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {(fairness.violations || []).map((v, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 10px', background: '#F5F0E8', border: '1.5px solid #D50000',
                  borderLeft: '4px solid #D50000'
                }}>
                  <div>
                    <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '11px',
                      letterSpacing: '0.05em', color: '#D50000', textTransform: 'uppercase' }}>
                      {v.metric}
                    </div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A', marginTop: '2px' }}>
                      {v.group} = <strong style={{ color: '#0A0A0A' }}>{v.attribute}</strong>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '13px', color: '#D50000' }}>
                      {v.value !== undefined ? v.value.toFixed(3) : '—'}
                    </div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#5A5A5A' }}>
                      disparity ratio
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
