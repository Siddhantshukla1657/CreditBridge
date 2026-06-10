import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, GitBranch, FileText, Zap, Wifi, Smartphone, Building2, Star, TrendingUp, ShieldCheck, Users } from 'lucide-react'
import { getModelCard } from '../lib/api'
import ModelCardModal from '../components/ModelCardModal'

const SIGNALS = [
  { icon: Wifi, label: 'UPI', desc: '7 signals' },
  { icon: Zap, label: 'UTILITY', desc: '4 signals' },
  { icon: Smartphone, label: 'MOBILE', desc: '4 signals' },
  { icon: Building2, label: 'GST', desc: '3 signals' },
]

const STATS = [
  { icon: Users, value: '190M', label: 'Unbanked Indians', sub: 'invisible to CIBIL' },
  { icon: TrendingUp, value: '0.924', label: 'AUC Score', sub: 'model accuracy' },
  { icon: ShieldCheck, value: '100%', label: 'RBI Compliant', sub: 'AA-framework' },
]

export default function Landing() {
  const navigate = useNavigate()
  const [showCard, setShowCard] = useState(false)
  const { data: cardData } = useQuery({ queryKey: ['model-card'], queryFn: getModelCard, retry: false })

  return (
    <div style={{ minHeight: '100vh', background: '#F5F0E8' }}>
      <nav className="navbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src="/logo.svg" alt="CreditBridge Logo" style={{ height: '36px', width: 'auto' }} />
          <div style={{
            fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '18px',
            letterSpacing: '0.02em', color: '#0A0A0A'
          }}>
            CREDIT<span style={{ color: '#0066FF' }}>BRIDGE</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <a href="https://github.com/Siddhantshukla1657/CreditBridge" target="_blank" rel="noreferrer"
            style={{
              display: 'flex', alignItems: 'center', gap: '6px', fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700, fontSize: '13px', color: '#0A0A0A', textDecoration: 'none',
              letterSpacing: '0.04em'
            }}>
            <GitBranch size={16} /> GITHUB ↗
          </a>
          <button onClick={() => setShowCard(true)} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>
            <FileText size={14} /> API DOCS
          </button>
        </div>
      </nav>

      {/* ── Hero: two-column full-width ── */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 40px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0',
          minHeight: 'calc(100vh - 60px)',
          alignItems: 'stretch',
        }}>

          {/* Left column */}
          <div style={{
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
            padding: '80px 60px 80px 0', borderRight: '2.5px solid #0A0A0A'
          }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px',
              border: '2px solid #0A0A0A', background: '#CCE0FF', marginBottom: '36px',
              fontFamily: "'DM Mono', monospace", fontSize: '12px', letterSpacing: '0.06em',
              alignSelf: 'flex-start'
            }}>
              <Star size={12} fill="#0066FF" color="#0066FF" />
              RBI AA-Framework Compliant · SHAP Explainable · Aequitas Fairness Audited
            </div>

            <h1 style={{
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
              fontSize: 'clamp(36px, 4.5vw, 68px)',
              lineHeight: 1.05, color: '#0A0A0A', marginBottom: '28px', letterSpacing: '-0.02em'
            }}>
              ALTERNATIVE<br />
              CREDIT SCORING<br />
              FOR THE{' '}
              <span style={{
                color: '#0066FF', textDecoration: 'underline',
                textDecorationThickness: '4px', textUnderlineOffset: '6px'
              }}>UNBANKED.</span>
            </h1>

            <p style={{
              fontFamily: "'DM Mono', monospace", fontSize: '15px', color: '#2A2A2A',
              lineHeight: 1.75, marginBottom: '52px', maxWidth: '480px'
            }}>
              190M Indians. No credit history. Financially active. Invisible to CIBIL.
              CreditBridge scores them using UPI, utility, mobile &amp; GST signals — with
              plain-language SHAP explanations and demographic fairness audits.
            </p>

            {/* CTA Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <button onClick={() => navigate('/lender')}
                style={{
                  background: '#0A0A0A', color: '#F5F0E8', border: '2.5px solid #0A0A0A',
                  boxShadow: '6px 6px 0 #0066FF', padding: '28px 24px', textAlign: 'left',
                  cursor: 'pointer', transition: 'all 80ms linear', display: 'block'
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translate(-3px,-3px)'; e.currentTarget.style.boxShadow = '9px 9px 0 #0066FF' }}
                onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = '6px 6px 0 #0066FF' }}>
                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '18px',
                  marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                }}>
                  LENDER VIEW <ArrowRight size={18} />
                </div>
                <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#C0B9AC' }}>
                  Review applicants · Drill into scores · Inspect fairness flags
                </div>
              </button>

              <button onClick={() => navigate('/applicant')}
                style={{
                  background: '#0066FF', color: '#F5F0E8', border: '2.5px solid #0A0A0A',
                  boxShadow: '6px 6px 0 #0A0A0A', padding: '28px 24px', textAlign: 'left',
                  cursor: 'pointer', transition: 'all 80ms linear', display: 'block'
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translate(-3px,-3px)'; e.currentTarget.style.boxShadow = '9px 9px 0 #0A0A0A' }}
                onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = '6px 6px 0 #0A0A0A' }}>
                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '18px',
                  marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                }}>
                  CHECK MY SCORE <ArrowRight size={18} />
                </div>
                <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '12px', color: '#CCE0FF' }}>
                  Enter your signals · Get scored · Understand your profile
                </div>
              </button>
            </div>
          </div>

          {/* Right column — visual panel */}
          <div style={{
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
            padding: '80px 0 80px 60px', gap: '24px'
          }}>

            {/* Score card mock */}
            <div style={{
              border: '2.5px solid #0A0A0A', background: '#EDE7D9',
              boxShadow: '8px 8px 0 #0A0A0A', padding: '32px'
            }}>
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
                fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase',
                color: '#5A5A5A', marginBottom: '20px'
              }}>Sample Credit Profile</div>

              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '16px', marginBottom: '24px' }}>
                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
                  fontSize: '72px', lineHeight: 1, color: '#0066FF'
                }}>742</div>
                <div style={{ paddingBottom: '8px' }}>
                  <div style={{
                    fontFamily: "'DM Mono', monospace", fontSize: '11px',
                    color: '#5A5A5A', marginBottom: '4px'
                  }}>OUT OF 900</div>
                  <div style={{
                    display: 'inline-block', background: '#00C853', color: '#fff',
                    fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
                    fontSize: '11px', letterSpacing: '0.08em', padding: '3px 10px',
                    border: '2px solid #0A0A0A'
                  }}>NEAR-PRIME</div>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: '24px' }}>
                <div style={{ height: '12px', background: '#C8C0B0', border: '2px solid #0A0A0A', position: 'relative' }}>
                  <div style={{
                    position: 'absolute', left: 0, top: 0, bottom: 0,
                    width: '68%',
                    background: 'linear-gradient(90deg, #0066FF 0%, #00C853 100%)',
                    transition: 'width 1s ease'
                  }} />
                  <div style={{
                    position: 'absolute', top: '-6px', left: '68%',
                    width: '3px', height: '24px', background: '#0A0A0A'
                  }} />
                </div>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#5A5A5A', marginTop: '4px'
                }}>
                  <span>300</span><span>900</span>
                </div>
              </div>

              {/* Signal breakdown */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[
                  { label: 'UPI Activity', val: 92, color: '#0066FF' },
                  { label: 'Utility Bills', val: 78, color: '#00C853' },
                  { label: 'Mobile Data', val: 65, color: '#FFD740' },
                  { label: 'GST Filing', val: 88, color: '#0066FF' },
                ].map(s => (
                  <div key={s.label} style={{
                    padding: '10px 12px', background: '#F5F0E8',
                    border: '1.5px solid #0A0A0A'
                  }}>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#5A5A5A', marginBottom: '4px' }}>
                      {s.label}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '4px', background: '#C8C0B0' }}>
                        <div style={{ width: `${s.val}%`, height: '100%', background: s.color }} />
                      </div>
                      <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '12px' }}>
                        {s.val}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats strip */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              {STATS.map(st => (
                <div key={st.label} style={{
                  padding: '20px 16px', border: '2.5px solid #0A0A0A',
                  background: '#F5F0E8', boxShadow: '4px 4px 0 #0A0A0A',
                  textAlign: 'center'
                }}>
                  <st.icon size={20} color="#0066FF" style={{ marginBottom: '8px' }} />
                  <div style={{
                    fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700,
                    fontSize: '22px', color: '#0066FF', lineHeight: 1
                  }}>{st.value}</div>
                  <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '11px', color: '#0A0A0A', marginTop: '4px' }}>
                    {st.label}
                  </div>
                  <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '10px', color: '#5A5A5A', marginTop: '2px' }}>
                    {st.sub}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── How It Works ── */}
      <div style={{ borderTop: '2.5px solid #0A0A0A', background: '#EDE7D9' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '56px 40px' }}>
          <div style={{
            fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
            letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A5A5A', marginBottom: '28px'
          }}>
            How It Works
          </div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            {SIGNALS.map((s, i) => (
              <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 24px',
                  border: '2.5px solid #0A0A0A', boxShadow: '3px 3px 0 #0A0A0A', background: '#F5F0E8'
                }}>
                  <s.icon size={18} color="#0066FF" />
                  <div>
                    <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px' }}>{s.label}</div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A' }}>{s.desc}</div>
                  </div>
                </div>
                {i < SIGNALS.length - 1 && (
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '20px', color: '#5A5A5A' }}>→</span>
                )}
              </div>
            ))}
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: '20px', color: '#5A5A5A' }}>→</span>
            <div style={{
              padding: '14px 24px', background: '#0066FF', color: '#F5F0E8',
              border: '2.5px solid #0A0A0A', boxShadow: '3px 3px 0 #0A0A0A'
            }}>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px' }}>SCORE</div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#CCE0FF' }}>300–900</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Model Card Snapshot ── */}
      {cardData && cardData.performance_metrics && (
        <div style={{ borderTop: '2.5px solid #0A0A0A' }}>
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '56px 40px' }}>
            <div style={{
              padding: '32px', border: '2.5px solid #0A0A0A',
              background: '#EDE7D9', boxShadow: '4px 4px 0 #0A0A0A'
            }}>
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: '13px',
                letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A5A5A', marginBottom: '20px'
              }}>
                Model Card Snapshot
              </div>
              <div style={{ display: 'flex', gap: '48px', flexWrap: 'wrap', marginBottom: '20px' }}>
                {[
                  ['AUC', cardData.performance_metrics.AUC, '≥ 0.88'],
                  ['KS Stat', cardData.performance_metrics.KS_Statistic, '≥ 0.40'],
                  ['ECE', cardData.performance_metrics.Expected_Calibration_Error_ECE, '≤ 0.04'],
                  ['Version', cardData.model_version, '—'],
                ].map(([label, val, target]) => (
                  <div key={label}>
                    <div style={{
                      fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A',
                      textTransform: 'uppercase', letterSpacing: '0.06em'
                    }}>{label}</div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 500, fontSize: '24px', color: '#0066FF' }}>
                      {typeof val === 'number' ? val.toFixed(3) : (val || '—')}
                    </div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: '11px', color: '#5A5A5A' }}>
                      target {target}
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={() => setShowCard(true)} className="btn-secondary"
                style={{ padding: '8px 16px', fontSize: '12px' }}>
                VIEW FULL MODEL CARD
              </button>
            </div>
          </div>
        </div>
      )}

      {showCard && <ModelCardModal card={cardData} onClose={() => setShowCard(false)} />}
    </div>
  )
}
