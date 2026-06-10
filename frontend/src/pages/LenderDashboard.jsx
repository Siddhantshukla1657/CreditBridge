import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileText, AlertTriangle, ChevronRight } from 'lucide-react'
import { getModelCard } from '../lib/api'
import BandBadge from '../components/BandBadge'
import ScoreGauge from '../components/ScoreGauge'
import FactorCard from '../components/FactorCard'
import WaterfallChart from '../components/WaterfallChart'
import ModelCardModal from '../components/ModelCardModal'

// Mock applicant data for Lender View demo
const MOCK_APPLICANTS = [
  {
    applicant_id: 'IND-2026-000142', score: 782, band: 'Prime', default_probability: 0.048, confidence: 0.90,
    top_factors: [
      { feature: 'utility_streak_length', label: 'Utility Payment On-Time Streak', points: 28, text: 'Utility Payment On-Time Streak (+28 pts): Long streak of on-time utility payments.' },
      { feature: 'upi_consistency_score', label: 'UPI Cash Flow Consistency', points: 22, text: 'UPI Cash Flow Consistency (+22 pts): Consistent UPI patterns.' },
      { feature: 'mobile_recharge_streak', label: 'Mobile Recharge Consistency', points: 15, text: 'Mobile Recharge Consistency (+15 pts): Timely mobile recharges.' },
    ],
    waterfall_data: [
      { name: 'Base Value', value: -1.2, start: 0, end: -1.2, is_total: true },
      { name: 'utility_streak_length', value: -0.8, start: -1.2, end: -2.0, is_total: false },
      { name: 'upi_consistency_score', value: -0.6, start: -2.0, end: -2.6, is_total: false },
      { name: 'mobile_recharge_streak', value: -0.4, start: -2.6, end: -3.0, is_total: false },
      { name: 'Final Prediction', value: -3.0, start: 0, end: -3.0, is_total: true },
    ],
    fairness_flags: [], gender: 'M', geography: 'urban', income_proxy: 'high'
  },
  {
    applicant_id: 'IND-2026-001847', score: 634, band: 'Subprime', default_probability: 0.177, confidence: 0.65,
    top_factors: [
      { feature: 'utility_lapse_count_12m', label: 'Utility Bill Lapses (12m)', points: -31, text: 'Utility Bill Lapses (12m) (-31 pts): Lapsed utility bills indicate risk.' },
      { feature: 'upi_failed_rate', label: 'UPI Transaction Success Rate', points: -18, text: 'UPI Transaction Success Rate (-18 pts): High transaction failure rate.' },
      { feature: 'mobile_recharge_streak', label: 'Mobile Recharge Consistency', points: 12, text: 'Mobile Recharge Consistency (+12 pts): Timely recharges.' },
    ],
    waterfall_data: [
      { name: 'Base Value', value: -1.2, start: 0, end: -1.2, is_total: true },
      { name: 'utility_lapse_count_12m', value: 0.9, start: -1.2, end: -0.3, is_total: false },
      { name: 'upi_failed_rate', value: 0.5, start: -0.3, end: 0.2, is_total: false },
      { name: 'mobile_recharge_streak', value: -0.35, start: 0.2, end: -0.15, is_total: false },
      { name: 'Final Prediction', value: -0.15, start: 0, end: -0.15, is_total: true },
    ],
    fairness_flags: [], gender: 'F', geography: 'semi-urban', income_proxy: 'mid'
  },
  {
    applicant_id: 'IND-2026-003291', score: 451, band: 'High risk', default_probability: 0.408, confidence: 0.72,
    top_factors: [
      { feature: 'utility_lapse_count_12m', label: 'Utility Bill Lapses (12m)', points: -42, text: 'Utility Bill Lapses (12m) (-42 pts): Multiple lapses detected.' },
      { feature: 'mobile_lapse_count', label: 'Mobile Connectivity Lapses', points: -25, text: 'Mobile Connectivity Lapses (-25 pts): Frequent disconnections.' },
      { feature: 'upi_income_regularity', label: 'Income Deposit Consistency', points: -19, text: 'Income Deposit Consistency (-19 pts): Irregular income pattern.' },
    ],
    waterfall_data: [
      { name: 'Base Value', value: -1.2, start: 0, end: -1.2, is_total: true },
      { name: 'utility_lapse_count_12m', value: 1.2, start: -1.2, end: 0.0, is_total: false },
      { name: 'mobile_lapse_count', value: 0.7, start: 0.0, end: 0.7, is_total: false },
      { name: 'upi_income_regularity', value: 0.55, start: 0.7, end: 1.25, is_total: false },
      { name: 'Final Prediction', value: 1.25, start: 0, end: 1.25, is_total: true },
    ],
    fairness_flags: ['Model-level Demographic Parity disparity warning for geography=\'rural\'.'],
    gender: 'M', geography: 'rural', income_proxy: 'low'
  },
  {
    applicant_id: 'IND-2026-004581', score: 819, band: 'Prime', default_probability: 0.030, confidence: 0.94,
    top_factors: [
      { feature: 'gst_filing_regularity', label: 'GST Filing Regularity', points: 35, text: 'GST Filing Regularity (+35 pts): Perfect GST compliance.' },
      { feature: 'upi_txn_count_6m', label: 'UPI Transaction Volume', points: 20, text: 'UPI Transaction Volume (+20 pts): Frequent digital transactions.' },
      { feature: 'utility_streak_length', label: 'Utility Payment On-Time Streak', points: 18, text: 'Utility Payment On-Time Streak (+18 pts): Consistent payments.' },
    ],
    waterfall_data: [
      { name: 'Base Value', value: -1.2, start: 0, end: -1.2, is_total: true },
      { name: 'gst_filing_regularity', value: -1.0, start: -1.2, end: -2.2, is_total: false },
      { name: 'upi_txn_count_6m', value: -0.6, start: -2.2, end: -2.8, is_total: false },
      { name: 'utility_streak_length', value: -0.5, start: -2.8, end: -3.3, is_total: false },
      { name: 'Final Prediction', value: -3.3, start: 0, end: -3.3, is_total: true },
    ],
    fairness_flags: [], gender: 'F', geography: 'urban', income_proxy: 'high', is_msme: true
  },
  {
    applicant_id: 'IND-2026-005823', score: 698, band: 'Near-prime', default_probability: 0.102, confidence: 0.78,
    top_factors: [
      { feature: 'upi_consistency_score', label: 'UPI Cash Flow Consistency', points: 19, text: 'UPI Cash Flow Consistency (+19 pts): Consistent UPI patterns.' },
      { feature: 'utility_days_before_due_avg', label: 'Average Utility Payment Delay', points: -14, text: 'Average Utility Payment Delay (-14 pts): Some late payments.' },
      { feature: 'mobile_plan_trend', label: 'Mobile Plan Spend Trend', points: 11, text: 'Mobile Plan Spend Trend (+11 pts): Stable mobile spend.' },
    ],
    waterfall_data: [
      { name: 'Base Value', value: -1.2, start: 0, end: -1.2, is_total: true },
      { name: 'upi_consistency_score', value: -0.55, start: -1.2, end: -1.75, is_total: false },
      { name: 'utility_days_before_due_avg', value: 0.40, start: -1.75, end: -1.35, is_total: false },
      { name: 'mobile_plan_trend', value: -0.32, start: -1.35, end: -1.67, is_total: false },
      { name: 'Final Prediction', value: -1.67, start: 0, end: -1.67, is_total: true },
    ],
    fairness_flags: [], gender: 'M', geography: 'semi-urban', income_proxy: 'mid'
  },
]

const BAND_OPTIONS = ['All', 'Prime', 'Near-prime', 'Subprime', 'High risk', 'Decline']

export default function LenderDashboard() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const [bandFilter, setBandFilter] = useState('All')
  const [flagsOnly, setFlagsOnly] = useState(false)
  const [showCard, setShowCard] = useState(false)
  const { data: cardData } = useQuery({ queryKey: ['model-card'], queryFn: getModelCard, retry: false })

  const filtered = MOCK_APPLICANTS.filter(a => {
    if (bandFilter !== 'All' && a.band !== bandFilter) return false
    if (flagsOnly && a.fairness_flags.length === 0) return false
    return true
  })

  const selectedData = selected !== null ? MOCK_APPLICANTS[selected] : null

  return (
    <div style={{ height: '100vh', background: '#F5F0E8', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button onClick={() => navigate('/')} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '12px', gap: '6px' }}>
            <ArrowLeft size={14} /> BACK
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src="/logo.svg" alt="CreditBridge Logo" style={{ height: '24px', width: 'auto' }} />
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '16px', letterSpacing: '0.04em' }}>
              LENDER VIEW
            </div>
          </div>
        </div>
        <button onClick={() => setShowCard(true)} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>
          <FileText size={14} /> MODEL CARD
        </button>
      </nav>

      {/* Filters */}
      <div style={{
        borderBottom: '2px solid #0A0A0A', padding: '14px 24px', background: '#EDE7D9',
        display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', flexShrink: 0
      }}>
        <span style={{
          fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
          letterSpacing: '0.06em', textTransform: 'uppercase', color: '#5A5A5A'
        }}>Filters:</span>
        {BAND_OPTIONS.map(b => (
          <button key={b} onClick={() => setBandFilter(b)}
            style={{
              padding: '6px 14px', fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
              fontSize: '12px', letterSpacing: '0.04em', textTransform: 'uppercase', cursor: 'pointer',
              background: bandFilter === b ? '#0A0A0A' : '#F5F0E8',
              color: bandFilter === b ? '#F5F0E8' : '#0A0A0A',
              border: '2px solid #0A0A0A',
              boxShadow: bandFilter === b ? 'none' : '2px 2px 0 #0A0A0A',
              transition: 'all 80ms linear'
            }}>
            {b}
          </button>
        ))}
        <label style={{
          display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer',
          fontFamily: "'DM Mono', monospace", fontSize: '13px', userSelect: 'none'
        }}>
          <input type="checkbox" checked={flagsOnly} onChange={e => setFlagsOnly(e.target.checked)}
            style={{ width: '16px', height: '16px', accentColor: '#0066FF' }} />
          FLAGS ONLY
        </label>
      </div>

      {/* Main Layout — fills remaining height, both panels fixed */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: selectedData ? 'minmax(0, 1fr) 460px' : '1fr',
        gap: '0',
        overflow: 'hidden',
        transition: 'grid-template-columns 200ms ease-out',
        minHeight: 0
      }}>

        {/* Left Frame — table, locked when detail open */}
        <div style={{
          overflow: selectedData ? 'hidden' : 'auto',
          padding: '24px',
          height: '100%',
          boxSizing: 'border-box'
        }}>
          <div style={{ border: '2.5px solid #0A0A0A', boxShadow: '6px 6px 0 #0A0A0A', overflow: 'hidden' }}>
            <table className="brutal-table" style={{ minWidth: '600px' }}>
              <thead>
                <tr>
                  <th>APPLICANT ID</th>
                  <th>SCORE</th>
                  <th>BAND</th>
                  <th>DEFAULT PROB</th>
                  <th>FLAGS</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((a) => {
                  const origIdx = MOCK_APPLICANTS.indexOf(a)
                  const isSelected = selected === origIdx
                  return (
                    <tr key={a.applicant_id} className={isSelected ? 'selected' : ''}
                      onClick={() => setSelected(isSelected ? null : origIdx)}>
                      <td style={{ fontWeight: 500 }}>{a.applicant_id}</td>
                      <td style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '15px', color: '#0066FF' }}>
                        {a.score}
                      </td>
                      <td><BandBadge band={a.band} /></td>
                      <td style={{ color: a.default_probability > 0.20 ? '#D50000' : '#0A0A0A' }}>
                        {(a.default_probability * 100).toFixed(1)}%
                      </td>
                      <td>
                        {a.fairness_flags.length > 0
                          ? <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#FF6D00' }}>
                            <AlertTriangle size={14} /> {a.fairness_flags.length}
                          </span>
                          : <span style={{ color: '#00C853' }}>✓ Clear</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <ChevronRight size={16} color={isSelected ? '#0066FF' : '#5A5A5A'}
                          style={{ transform: isSelected ? 'rotate(90deg)' : '', transition: 'transform 200ms' }} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div style={{
                padding: '40px', textAlign: 'center', fontFamily: "'DM Mono', monospace",
                fontSize: '14px', color: '#5A5A5A'
              }}>
                No applicants match current filters.
              </div>
            )}
          </div>
          <div style={{ marginTop: '12px', fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A' }}>
            Showing {filtered.length} of {MOCK_APPLICANTS.length} applicants (mock data)
          </div>
        </div>

        {/* Right Frame — detail panel, always scrollable */}
        {selectedData && (
          <div style={{
            borderLeft: '2.5px solid #0A0A0A',
            background: '#EDE7D9',
            overflowY: 'auto',
            height: '100%',
            boxSizing: 'border-box',
            padding: '24px'
          }} className="animate-slide-right">
            {/* Header */}
            <div style={{
              fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A',
              marginBottom: '4px', letterSpacing: '0.06em'
            }}>APPLICANT</div>
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '16px',
              marginBottom: '20px', wordBreak: 'break-all'
            }}>{selectedData.applicant_id}</div>

            {/* Score + Band */}
            <div style={{
              background: '#F5F0E8', border: '2.5px solid #0A0A0A', boxShadow: '4px 4px 0 #0A0A0A',
              padding: '20px', textAlign: 'center', marginBottom: '20px'
            }}>
              <ScoreGauge score={selectedData.score} band={selectedData.band} />
              <div style={{ marginTop: '12px' }}>
                <BandBadge band={selectedData.band} />
              </div>
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'center', gap: '24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A' }}>DEFAULT PROB</div>
                  <div style={{
                    fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '16px',
                    color: selectedData.default_probability > 0.20 ? '#D50000' : '#00C853'
                  }}>
                    {(selectedData.default_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A' }}>CONFIDENCE</div>
                  <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '16px' }}>
                    {(selectedData.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Demographics */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
              {[['Gender', selectedData.gender], ['Geography', selectedData.geography], ['Income', selectedData.income_proxy]].map(([k, v]) => (
                <div key={k} style={{
                  padding: '6px 12px', border: '1.5px solid #0A0A0A', background: '#F5F0E8',
                  fontFamily: "'DM Mono', monospace", fontSize: '11px'
                }}>
                  <span style={{ color: '#5A5A5A' }}>{k}: </span><span style={{ fontWeight: 500 }}>{v}</span>
                </div>
              ))}
            </div>

            {/* Top Factors */}
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
              letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '12px', color: '#5A5A5A'
            }}>
              Top Factors
            </div>
            {selectedData.top_factors.map((f, i) => <FactorCard key={i} factor={f} index={i} />)}

            {/* SHAP Waterfall */}
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
              letterSpacing: '0.08em', textTransform: 'uppercase', margin: '20px 0 12px', color: '#5A5A5A'
            }}>
              SHAP Breakdown
            </div>
            <div style={{ background: '#F5F0E8', border: '2.5px solid #0A0A0A', padding: '16px 8px 16px 4px', overflowX: 'auto' }}>
              <WaterfallChart data={selectedData.waterfall_data} />
            </div>

            {/* Fairness flags */}
            {selectedData.fairness_flags.length > 0 && (
              <>
                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
                  letterSpacing: '0.08em', textTransform: 'uppercase', margin: '20px 0 12px', color: '#D50000'
                }}>
                  ⚠ Fairness Flags
                </div>
                {selectedData.fairness_flags.map((flag, i) => (
                  <div key={i} style={{
                    padding: '12px', background: '#FFE0E0', border: '1.5px solid #D50000',
                    fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#D50000', marginBottom: '8px'
                  }}>
                    {flag}
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>

      {showCard && <ModelCardModal card={cardData} onClose={() => setShowCard(false)} />}
    </div>
  )
}
