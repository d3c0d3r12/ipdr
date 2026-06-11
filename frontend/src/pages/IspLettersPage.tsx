import { FormEvent, useEffect, useState } from 'react'
import { API_BASE, apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'
import { listTemplates, LetterTemplate } from '../lib/templates'

// These fields never change — hardcoded, not shown to user
const FIXED_FIELDS = {
  subject: 'Reg provide information in case',
  email_reference: '',
  body_description: 'It is to bring to your kind notice that a case FIR No. mentioned below has been registered at the above mentioned Police Station and the investigation of the said case has been entrusted to the undersigned. During the course of investigation, it has been found that the following IP addresses / phone numbers were used by the accused persons. Therefore, it is requested to provide the subscriber information / CDR / IP logs for the following IP addresses / phone numbers at the earliest so that further investigation can be carried out.',
}

type FormState = {
  fir_number: string
  fir_date: string
  letter_date: string
  police_station: string
  sections: string
  complainant: string
  officer_name: string
  officer_designation: string
  officer_location: string
  officer_contact: string
}

const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' })

const initialState: FormState = {
  fir_number: '',
  fir_date: '',
  letter_date: today,
  police_station: 'Cyber Police Station, Delhi',
  sections: '',
  complainant: '',
  officer_name: '',
  officer_designation: 'Investigating Officer',
  officer_location: 'Cyber Police Station, Delhi',
  officer_contact: '',
}

type DetectedIsp = { isp: string; count: number }

function LField({
  label, value, onChange, placeholder, required = true, mono = false, hint,
}: {
  label: string; value: string; onChange: (v: string) => void
  placeholder?: string; required?: boolean; mono?: boolean; hint?: string
}) {
  return (
    <div>
      <label>{label}{required && <span style={{ color: 'var(--red)', marginLeft: 3 }}>*</span>}</label>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        style={mono ? { fontFamily: 'JetBrains Mono, monospace' } : undefined}
      />
      {hint && <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>{hint}</div>}
    </div>
  )
}

function Spinner() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeDashoffset="10" />
    </svg>
  )
}

export default function IspLettersPage() {
  const { token } = useAuth()
  const [zipFile, setZipFile] = useState<File | null>(null)
  const [form, setForm] = useState<FormState>(initialState)
  const [templates, setTemplates] = useState<LetterTemplate[]>([])
  const [templateId, setTemplateId] = useState('')
  const [detectedIsps, setDetectedIsps] = useState<DetectedIsp[]>([])
  const [detecting, setDetecting] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const F = (key: keyof FormState) => (v: string) => setForm(f => ({ ...f, [key]: v }))

  useEffect(() => {
    listTemplates(token).then(r => {
      const list = r.data?.templates ?? []
      setTemplates(list)
      setTemplateId((list.find(t => t.name === 'IFSO Dwarka Default') || list[0])?.id ?? '')
    })
  }, [token])

  const detectIsps = async () => {
    if (!zipFile) return
    setDetecting(true)
    setError('')
    const fd = new FormData()
    fd.append('zip_file', zipFile)
    try {
      const result = await apiRequest<{ isps: DetectedIsp[] }>(
        '/api/detect-isps-from-zip',
        { method: 'POST', body: fd },
        token
      )
      setDetectedIsps(result.data?.isps ?? [])
      if ((result.data?.isps ?? []).length === 0) setError('No ISPs detected in this ZIP')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect ISPs')
    } finally {
      setDetecting(false)
    }
  }

  const generate = async (e: FormEvent) => {
    e.preventDefault()
    if (!zipFile) return
    setGenerating(true)
    setError('')
    setSuccess('')

    const fd = new FormData()
    fd.append('zip_file', zipFile)
    // Variable fields
    Object.entries(form).forEach(([k, v]) => fd.append(k, v))
    // Fixed fields — sent silently
    Object.entries(FIXED_FIELDS).forEach(([k, v]) => fd.append(k, v))
    if (templateId) fd.append('template_id', templateId)

    try {
      const response = await fetch(`${API_BASE}/api/generate-isp-letters`, {
        method: 'POST',
        body: fd,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        setError(data.detail || 'Failed to generate letters')
      } else {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `ISP_Letters_FIR_${form.fir_number.replace(/[/\\]/g, '-') || 'case'}.zip`
        a.click()
        window.URL.revokeObjectURL(url)
        setSuccess('ISP letters generated and downloaded successfully')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <section>
      {/* Header */}
      <div style={{ marginBottom: 22 }}>
        <h1>ISP Letters Generator</h1>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>
          Generate formal letters to ISPs requesting subscriber/CDR data for a FIR case
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16, alignItems: 'start' }}>
        {/* Main Form */}
        <form className="card" style={{ marginBottom: 0 }} onSubmit={generate}>

          {/* ZIP Upload */}
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
              <span style={{
                width: 24, height: 24, borderRadius: 6, background: 'rgba(0,229,255,0.1)',
                border: '1px solid rgba(0,229,255,0.2)', display: 'inline-flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 11, color: 'var(--cyan)', fontWeight: 900, flexShrink: 0,
              }}>1</span>
              Upload IP Data ZIP
            </h2>

            <div>
              <label>Step-6 Output ZIP <span style={{ color: 'var(--red)' }}>*</span></label>
              <input
                type="file"
                accept=".zip"
                onChange={e => {
                  const f = e.target.files?.[0] ?? null
                  setZipFile(f)
                  setDetectedIsps([])
                  setError('')
                  setSuccess('')
                }}
                required
              />
              <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                The ZIP file produced by the ISP Separation step
              </div>
            </div>

            {zipFile && (
              <div style={{ marginTop: 10 }}>
                <button
                  type="button"
                  className="btn"
                  onClick={detectIsps}
                  disabled={detecting}
                  style={{ fontSize: 12 }}
                >
                  {detecting ? <><Spinner /> Detecting ISPs...</> : (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
                        <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                      </svg>
                      Detect ISPs in ZIP
                    </span>
                  )}
                </button>

                {detectedIsps.length > 0 && (
                  <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {detectedIsps.map(isp => (
                      <span key={isp.isp} style={{
                        fontSize: 11, padding: '3px 10px', borderRadius: 4,
                        background: 'rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.25)',
                        color: 'var(--cyan)', fontFamily: 'JetBrains Mono, monospace',
                      }}>
                        {isp.isp} <span style={{ color: 'var(--muted)', fontSize: 10 }}>({isp.count})</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div style={{ height: 1, background: 'var(--border)', margin: '0 0 20px' }} />

          {/* Case Details */}
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
              <span style={{
                width: 24, height: 24, borderRadius: 6, background: 'rgba(155,89,255,0.1)',
                border: '1px solid rgba(155,89,255,0.2)', display: 'inline-flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 11, color: 'var(--purple)', fontWeight: 900, flexShrink: 0,
              }}>2</span>
              Case Details
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <LField label="FIR Number" value={form.fir_number} onChange={F('fir_number')}
                placeholder="e.g. 201/25" mono hint="Will appear on all generated letters" />
              <LField label="FIR Date" value={form.fir_date} onChange={F('fir_date')}
                placeholder="e.g. 15/03/2025" />
              <LField label="Letter Date" value={form.letter_date} onChange={F('letter_date')}
                placeholder="e.g. 23/03/2026" />
              <LField label="Police Station" value={form.police_station} onChange={F('police_station')}
                placeholder="e.g. Cyber Police Station, Delhi" />
              <div style={{ gridColumn: '1 / -1' }}>
                <LField label="IPC / IT Act Sections" value={form.sections} onChange={F('sections')}
                  placeholder="e.g. 420 IPC, 66C/66D IT Act" />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <LField label="Complainant Name" value={form.complainant} onChange={F('complainant')}
                  placeholder="Full name of complainant" required={false} />
              </div>
            </div>
          </div>

          <div style={{ height: 1, background: 'var(--border)', margin: '0 0 20px' }} />

          {/* Officer Details */}
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
              <span style={{
                width: 24, height: 24, borderRadius: 6, background: 'rgba(0,255,136,0.1)',
                border: '1px solid rgba(0,255,136,0.2)', display: 'inline-flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 11, color: 'var(--green)', fontWeight: 900, flexShrink: 0,
              }}>3</span>
              Officer Details
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <LField label="Officer Name" value={form.officer_name} onChange={F('officer_name')}
                  placeholder="Full name of investigating officer" />
              </div>
              <LField label="Designation" value={form.officer_designation} onChange={F('officer_designation')}
                placeholder="e.g. SI, Inspector" />
              <LField label="Contact Number" value={form.officer_contact} onChange={F('officer_contact')}
                placeholder="Mobile / office number" mono />
              <div style={{ gridColumn: '1 / -1' }}>
                <LField label="Office Location" value={form.officer_location} onChange={F('officer_location')}
                  placeholder="e.g. Cyber Police Station, New Delhi" />
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label>Letter template</label>
            <select value={templateId} onChange={e => setTemplateId(e.target.value)} style={{ width: '100%' }}>
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.name}{t.scope === 'system' ? ' (default)' : t.scope === 'shared' ? ' (shared)' : ''}
                </option>
              ))}
            </select>
          </div>

          {error && <div className="alert error" style={{ marginBottom: 12 }}>{error}</div>}
          {success && <div className="alert success" style={{ marginBottom: 12 }}>{success}</div>}

          <button
            className="btn btn-primary"
            disabled={generating || !zipFile}
            style={{ padding: '11px', fontSize: 13, letterSpacing: '0.5px' }}
          >
            {generating ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Spinner /> Generating Letters...
              </span>
            ) : (
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Generate ISP Letters ZIP
              </span>
            )}
          </button>
        </form>

        {/* Info Panel */}
        <div style={{ display: 'grid', gap: 12 }}>
          {/* What you get */}
          <div className="card" style={{ marginBottom: 0 }}>
            <h3 style={{ marginBottom: 12, color: 'var(--cyan)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              What you'll get
            </h3>
            <div style={{ display: 'grid', gap: 8 }}>
              {[
                'One letter per ISP detected',
                'All relevant IPs listed per letter',
                'Formal police letter format',
                'Ready to print & dispatch',
              ].map((t, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <span style={{ color: 'var(--green)', fontSize: 12, marginTop: 1, flexShrink: 0 }}>✓</span>
                  <span style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Hardcoded info */}
          <div className="card" style={{ marginBottom: 0, padding: '12px 14px' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 10 }}>
              Auto-filled in every letter
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              <div>
                <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 2 }}>Subject</div>
                <div style={{ fontSize: 11, color: 'var(--text)', fontStyle: 'italic' }}>
                  Reg provide information in case
                </div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 2 }}>Body</div>
                <div style={{ fontSize: 11, color: 'var(--text)', fontStyle: 'italic' }}>
                  Standard formal request paragraph
                </div>
              </div>
            </div>
            <div style={{
              marginTop: 10, padding: '8px 10px', borderRadius: 6,
              background: 'rgba(0,229,255,0.04)', border: '1px solid rgba(0,229,255,0.12)',
              fontSize: 11, color: 'var(--muted)',
            }}>
              These fields are standardised and don't need manual entry
            </div>
          </div>

          {/* Steps */}
          <div className="card" style={{ marginBottom: 0, padding: '12px 14px' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 10 }}>
              Steps
            </div>
            {[
              { n: '01', t: 'Upload the ISP ZIP file' },
              { n: '02', t: 'Detect ISPs (optional preview)' },
              { n: '03', t: 'Fill case & officer details' },
              { n: '04', t: 'Generate & download ZIP' },
              { n: '05', t: 'Print letters & dispatch' },
            ].map(s => (
              <div key={s.n} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{
                  fontFamily: 'Orbitron, monospace', fontSize: 9, fontWeight: 900,
                  color: 'var(--cyan)', flexShrink: 0, paddingTop: 2,
                }}>{s.n}</span>
                <span style={{ fontSize: 11, color: 'var(--muted)', lineHeight: 1.5 }}>{s.t}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @media print {
          .sidebar, .app-header, .btn, .alert { display: none !important; }
          .card { border: 1px solid #ccc !important; background: white !important; color: black !important; }
        }
      `}</style>
    </section>
  )
}
