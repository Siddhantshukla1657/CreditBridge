import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, Send, Lightbulb, Info } from 'lucide-react'
import { scoreApplicant, getModelCard } from '../lib/api'
import ScoreGauge from '../components/ScoreGauge'
import BandBadge from '../components/BandBadge'
import FactorCard from '../components/FactorCard'
import WaterfallChart from '../components/WaterfallChart'
import ForcePlotChart from '../components/ForcePlotChart'
import ModelCardModal from '../components/ModelCardModal'

const IMPROVEMENT_TIPS = {
  'Prime': [],
  'Near-prime': [
    { title: 'Pay Utility Bills Early', desc: 'Paying bills 3–5 days before due date consistently improves your payment score.' },
    { title: 'Increase UPI Usage', desc: 'Higher digital transaction volume demonstrates financial engagement to lenders.' },
  ],
  'Subprime': [
    { title: 'Eliminate Bill Lapses', desc: 'Any lapsed utility or mobile bill severely impacts your score. Set up auto-pay.' },
    { title: 'Reduce Failed Transactions', desc: 'Keep adequate balance to reduce UPI failure rates below 5%.' },
    { title: 'Regularize Income Deposits', desc: 'Consistent monthly salary deposits signal stable income to the model.' },
  ],
  'High risk': [
    { title: 'Restore Lapsed Connections', desc: 'Reconnect lapsed utility/mobile services immediately. Every month of lapse hurts.' },
    { title: 'Build Payment Streaks', desc: 'Start making on-time payments now. 3+ months of consistency begins to rebuild score.' },
    { title: 'Stabilize Cash Flow', desc: 'Reduce frequency and value of failed UPI transactions through better balance management.' },
    { title: 'File GST Regularly (MSMEs)', desc: 'Regular GST compliance is one of the highest-impact signals for business applicants.' },
  ],
  'Decline': [
    { title: 'Emergency Financial Counseling', desc: 'Consider engaging a financial counselor to create a payment recovery plan.' },
    { title: 'Focus on Basics', desc: 'Prioritize mobile and utility payments — even partial recovery over 6 months moves the score.' },
  ],
}

const DEFAULT_FORM = {
  gender: 'M', geography: 'urban', income_proxy: 'mid', is_msme: false,
  upi_count_monthly: 15, upi_failed_pct: 3, upi_avg_amount: 450,
  utility_streak: 8, utility_days_late_avg: -2, utility_lapses: 1,
  mobile_plan_value: 299, mobile_streak: 10, mobile_lapses: 0,
  gst_filing_months: 12, income_shock: false,
}

function buildPayload(form) {
  const count = Math.max(1, Math.round(form.upi_count_monthly))
  const failedCount = Math.round(count * (form.upi_failed_pct / 100))
  const upi_count = Array(12).fill(count)
  const upi_failed_count = Array(12).fill(failedCount)
  const upi_amount = Array(12).fill(parseFloat(form.upi_avg_amount) * count)
  const upi_merchant_count = Array(12).fill(Math.round(count * 0.55))
  const upi_night_count = Array(12).fill(Math.round(count * 0.12))
  const upi_income_deposits = Array(12).fill(1)

  const lapses = Math.min(12, Math.round(form.utility_lapses))
  const utility_status = Array(12).fill('on_time')
  for (let i = 0; i < lapses; i++) utility_status[i] = 'lapsed'
  const utility_days_late = Array(12).fill(parseFloat(form.utility_days_late_avg))

  const mobLapses = Math.min(12, Math.round(form.mobile_lapses))
  const mobile_recharge_status = Array(12).fill('on_time')
  for (let i = 0; i < mobLapses; i++) mobile_recharge_status[i] = 'lapsed'
  const mobile_plan_value = Array(12).fill(parseFloat(form.mobile_plan_value))

  const gstFiled = Math.min(12, Math.round(form.gst_filing_months))
  const gst_status = form.is_msme ? [...Array(gstFiled).fill('filed'), ...Array(12 - gstFiled).fill('unfiled')] : []
  const gst_turnover = form.is_msme ? Array(12).fill(150000) : []
  const gst_penalties = form.is_msme ? [...Array(gstFiled).fill(0), ...Array(12 - gstFiled).fill(1000)] : []

  return {
    gender: form.gender, geography: form.geography,
    income_proxy: form.income_proxy, is_msme: form.is_msme,
    upi_count, upi_failed_count, upi_amount, upi_merchant_count,
    upi_night_count, upi_income_deposits, utility_status, utility_days_late,
    mobile_recharge_status, mobile_plan_value, gst_status, gst_turnover, gst_penalties,
    income_shock_job_loss: form.income_shock, income_shock_health: false,
  }
}

function FormField({ label, children }) {
  return (
    <div>
      <label className="brutal-label">{label}</label>
      {children}
    </div>
  )
}

function SelectField({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} className="brutal-input"
      style={{ appearance: 'none', cursor: 'pointer' }}>
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  )
}

export default function ApplicantView() {
  const navigate = useNavigate()
  const [form, setForm] = useState(DEFAULT_FORM)
  const [showCard, setShowCard] = useState(false)
  const { data: cardData } = useQuery({ queryKey: ['model-card'], queryFn: getModelCard, retry: false })

  const set = (key) => (val) => setForm(f => ({ ...f, [key]: val }))
  const setNum = (key) => (e) => setForm(f => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))

  const mutation = useMutation({ mutationFn: () => scoreApplicant(buildPayload(form)) })
  const result = mutation.data
  const tips = IMPROVEMENT_TIPS[result?.band] || []

  return (
    <div style={{ height: '100vh', background: '#F5F0E8', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button onClick={() => navigate('/')} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '12px' }}>
            <ArrowLeft size={14} /> BACK
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src="/logo.svg" alt="CreditBridge Logo" style={{ height: '24px', width: 'auto' }} />
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '16px', letterSpacing: '0.04em' }}>
              CHECK YOUR SCORE
            </div>
          </div>
        </div>
        <button onClick={() => setShowCard(true)} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>
          <Info size={14} /> MODEL INFO
        </button>
      </nav>

      <div style={{ flex: 1, overflow: 'hidden', width: '100%' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 24px 40px', height: '100%', boxSizing: 'border-box' }}>
          <div style={{ display: 'grid', gridTemplateColumns: result ? 'minmax(0, 1fr) 420px' : '1fr', gap: '40px', alignItems: 'stretch', height: '100%', overflow: 'hidden' }}>

            {/* Input Form */}
            <div style={{ overflowY: result ? 'hidden' : 'auto', height: '100%', paddingRight: '8px' }}>
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
              letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A5A5A', marginBottom: '20px',
              borderBottom: '2px solid #0A0A0A', paddingBottom: '12px'
            }}>
              Step 1 — Enter Your Financial Signals
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>

              <FormField label="Gender">
                <SelectField value={form.gender} onChange={set('gender')}
                  options={[['M', 'Male'], ['F', 'Female']]} />
              </FormField>

              <FormField label="Geography">
                <SelectField value={form.geography} onChange={set('geography')}
                  options={[['urban', 'Urban'], ['semi-urban', 'Semi-Urban'], ['rural', 'Rural']]} />
              </FormField>

              <FormField label="Income Level">
                <SelectField value={form.income_proxy} onChange={set('income_proxy')}
                  options={[['high', 'High (₹50k+/mo)'], ['mid', 'Mid (₹15–50k/mo)'], ['low', 'Low (<₹15k/mo)']]} />
              </FormField>

              <FormField label="Business / MSME">
                <SelectField value={form.is_msme ? 'yes' : 'no'}
                  onChange={v => setForm(f => ({ ...f, is_msme: v === 'yes' }))}
                  options={[['no', 'No'], ['yes', 'Yes (MSME)']]} />
              </FormField>

              <FormField label="UPI Txns / Month">
                <input type="number" className="brutal-input" value={form.upi_count_monthly}
                  onChange={setNum('upi_count_monthly')} min={0} max={200} />
              </FormField>

              <FormField label="UPI Failed Rate (%)">
                <input type="number" className="brutal-input" value={form.upi_failed_pct}
                  onChange={setNum('upi_failed_pct')} min={0} max={100} step={0.5} />
              </FormField>

              <FormField label="Avg UPI Txn Value (₹)">
                <input type="number" className="brutal-input" value={form.upi_avg_amount}
                  onChange={setNum('upi_avg_amount')} min={0} />
              </FormField>

              <FormField label="Utility On-Time Streak (mo)">
                <input type="number" className="brutal-input" value={form.utility_streak}
                  onChange={setNum('utility_streak')} min={0} max={12} />
              </FormField>

              <FormField label="Utility Lapses (12mo)">
                <input type="number" className="brutal-input" value={form.utility_lapses}
                  onChange={setNum('utility_lapses')} min={0} max={12} />
              </FormField>

              <FormField label="Avg Days Late on Bill">
                <input type="number" className="brutal-input" value={form.utility_days_late_avg}
                  onChange={setNum('utility_days_late_avg')} step={1} />
              </FormField>

              <FormField label="Mobile Plan Value (₹/mo)">
                <input type="number" className="brutal-input" value={form.mobile_plan_value}
                  onChange={setNum('mobile_plan_value')} min={0} />
              </FormField>

              <FormField label="Mobile Lapses (12mo)">
                <input type="number" className="brutal-input" value={form.mobile_lapses}
                  onChange={setNum('mobile_lapses')} min={0} max={12} />
              </FormField>

              {form.is_msme && (
                <FormField label="GST Filed Months (12mo)">
                  <input type="number" className="brutal-input" value={form.gst_filing_months}
                    onChange={setNum('gst_filing_months')} min={0} max={12} />
                </FormField>
              )}

              <FormField label="Income Shock (Job Loss)">
                <SelectField value={form.income_shock ? 'yes' : 'no'}
                  onChange={v => setForm(f => ({ ...f, income_shock: v === 'yes' }))}
                  options={[['no', 'No'], ['yes', 'Yes']]} />
              </FormField>
            </div>

            <button onClick={() => mutation.mutate()} className="btn-primary"
              disabled={mutation.isPending}
              style={{ fontSize: '14px', padding: '14px 32px', opacity: mutation.isPending ? 0.7 : 1 }}>
              <Send size={16} />
              {mutation.isPending ? 'SCORING...' : 'CHECK SCORE →'}
            </button>

            {mutation.isError && (
              <div style={{
                marginTop: '16px', padding: '14px', background: '#FFE0E0',
                border: '2px solid #D50000', fontFamily: "'DM Mono', monospace", fontSize: '13px', color: '#D50000'
              }}>
                ⚠ Could not reach API. Is the FastAPI server running on port 8000?
                <br />Start it with: <code>uvicorn api.main:app --reload</code>
              </div>
            )}
          </div>

          {/* Results Panel */}
          {result && (
            <div className="animate-slide-right" style={{ height: '100%', overflowY: 'auto', paddingRight: '4px' }}>
              {/* Score Box */}
              <div style={{
                background: '#F5F0E8', border: '2.5px solid #0A0A0A',
                boxShadow: '6px 6px 0 #0066FF', padding: '28px', textAlign: 'center', marginBottom: '24px'
              }}>
                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '11px',
                  letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A5A5A', marginBottom: '16px'
                }}>
                  YOUR SCORE
                </div>
                <ScoreGauge score={result.score} band={result.band} />
                <div style={{
                  marginTop: '12px', display: 'flex', justifyContent: 'center', gap: '16px',
                  alignItems: 'center', flexWrap: 'wrap'
                }}>
                  <BandBadge band={result.band} />
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A' }}>
                    Confidence: {(result.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                {result.fairness_flags?.length > 0 && (
                  <div style={{
                    marginTop: '12px', padding: '8px', background: '#FFE0CC',
                    border: '1.5px solid #FF6D00', fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#FF6D00'
                  }}>
                    ⚠ {result.fairness_flags[0]}
                  </div>
                )}
              </div>

              {/* Top Factors */}
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
                letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '12px', color: '#5A5A5A'
              }}>
                What's Driving Your Score
              </div>
              {result.top_factors.map((f, i) => <FactorCard key={i} factor={f} index={i} />)}

              {/* Improvement Tips */}
              {tips.length > 0 && (
                <>
                  <div style={{
                    fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
                    letterSpacing: '0.08em', textTransform: 'uppercase', margin: '24px 0 12px', color: '#5A5A5A',
                    display: 'flex', alignItems: 'center', gap: '6px'
                  }}>
                    <Lightbulb size={14} color="#0066FF" /> HOW TO IMPROVE
                  </div>
                  {tips.map((tip, i) => (
                    <div key={i} style={{
                      border: '2px solid #0A0A0A', background: '#EDE7D9',
                      boxShadow: '3px 3px 0 #0A0A0A', padding: '14px', marginBottom: '10px'
                    }}
                      className={`animate-slide-up stagger-${i + 1}`}>
                      <div style={{
                        fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
                        color: '#0066FF', marginBottom: '4px'
                      }}>{tip.title}</div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#5A5A5A', lineHeight: 1.6 }}>
                        {tip.desc}
                      </div>
                    </div>
                  ))}
                </>
              )}

              {/* SHAP Waterfall */}
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
                letterSpacing: '0.08em', textTransform: 'uppercase', margin: '24px 0 12px', color: '#5A5A5A'
              }}>
                SHAP Waterfall
              </div>
              <div style={{ background: '#F5F0E8', border: '2.5px solid #0A0A0A', padding: '16px 8px 16px 4px', overflowX: 'auto' }}>
                <WaterfallChart data={result.waterfall_data} />
              </div>

              {/* SHAP Force Plot */}
              {result.force_plot_data && (
                <>
                  <div style={{
                    fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px',
                    letterSpacing: '0.08em', textTransform: 'uppercase', margin: '24px 0 12px', color: '#5A5A5A'
                  }}>
                    SHAP Force Plot
                  </div>
                  <div style={{ border: '2.5px solid #0A0A0A', background: '#F5F0E8', padding: '16px' }}>
                    <ForcePlotChart data={result.force_plot_data} />
                  </div>
                </>
              )}

              <div style={{ marginTop: '12px', textAlign: 'center' }}>
                <button onClick={() => setShowCard(true)} className="btn-secondary" style={{ fontSize: '12px', padding: '8px 16px' }}>
                  VIEW MODEL CARD
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>

    {showCard && <ModelCardModal card={cardData} onClose={() => setShowCard(false)} />}
  </div>
  )
}
