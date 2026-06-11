import { useEffect, useState } from 'react'
import { apiRequest, API_BASE } from '../lib/api'
import { useAuth } from '../lib/auth'
import { listTemplates, LetterTemplate } from '../lib/templates'

type IspEntry = { isp: string; count: number }
type CaseEntry = {
  fir_number: string
  case_title?: string
  run_dir: string
  total_isps: number
  total_records: number
  unique_ips: number
  isps: IspEntry[]
  last_generated_at?: string | null
}

type LetterForm = {
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

const FIXED_FIELDS = {
  subject: 'Reg provide information in case',
  email_reference: '',
  body_description:
    'It is to bring to your kind notice that a case has been registered in this police station. In the investigation of the said case, the IP addresses mentioned in the attachment are required to be verified. You are requested to provide the subscriber/user details along with CDR/IP logs for the mentioned IP addresses at the earliest to facilitate the investigation.',
}

function fmtDate(d?: string | null) {
  if (!d) return null
  const dt = new Date(d)
  return Number.isNaN(dt.getTime()) ? null : dt.toLocaleString()
}

export default function IspLettersCatalogPage() {
  const { token } = useAuth()
  const [cases, setCases] = useState<CaseEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [busy, setBusy] = useState<string | null>(null) // `${fir}:ALL` or `${fir}:${isp}`
  const [formOpen, setFormOpen] = useState(false)
  const [templates, setTemplates] = useState<LetterTemplate[]>([])
  const [templateId, setTemplateId] = useState('')

  const [form, setForm] = useState<LetterForm>({
    fir_date: 'N/A',
    letter_date: new Date().toLocaleDateString('en-IN'),
    police_station: 'Special Cell',
    sections: 'N/A',
    complainant: 'N/A',
    officer_name: 'Inspector',
    officer_designation: 'IFSO, Special Cell',
    officer_location: 'Sec. 16C, Dwarka, New Delhi',
    officer_contact: 'N/A',
  })

  const load = async () => {
    setLoading(true)
    setError('')
    const res = await apiRequest<{ cases: CaseEntry[] }>('/api/process/ipdr/letters/catalog', {}, token)
    if (res.success && res.data) setCases(res.data.cases || [])
    else setError(res.error || 'Failed to load ISP letters')
    setLoading(false)
  }

  useEffect(() => { load() }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    listTemplates(token).then(r => {
      const list = r.data?.templates ?? []
      setTemplates(list)
      setTemplateId((list.find(t => t.name === 'IFSO Dwarka Default') || list[0])?.id ?? '')
    })
  }, [token])

  const setField = (k: keyof LetterForm, v: string) => setForm(p => ({ ...p, [k]: v }))

  const payloadFor = (fir: string) => {
    const fd = new FormData()
    fd.append('fir_number', fir)
    Object.entries({ ...form, ...FIXED_FIELDS }).forEach(([k, v]) => fd.append(k, String(v)))
    if (templateId) fd.append('template_id', templateId)
    return fd
  }

  const download = (blob: Blob, name: string) => {
    const url = URL.createObjectURL(blob)
    Object.assign(document.createElement('a'), { href: url, download: name }).click()
    URL.revokeObjectURL(url)
  }

  const downloadAll = async (c: CaseEntry) => {
    setError(''); setMsg(''); setBusy(`${c.fir_number}:ALL`)
    try {
      const res = await fetch(`${API_BASE}/api/process/ipdr/letters?run_dir=${encodeURIComponent(c.run_dir)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: payloadFor(c.fir_number) })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail || 'Failed to generate letters'); return }
      download(await res.blob(), `ISP_Letters_${c.fir_number.replace(/\//g, '-')}.zip`)
      setMsg(`All ISP letters for FIR ${c.fir_number} downloaded ✓`)
      load()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setBusy(null) }
  }

  const downloadOne = async (c: CaseEntry, isp: string) => {
    setError(''); setMsg(''); setBusy(`${c.fir_number}:${isp}`)
    try {
      const res = await fetch(
        `${API_BASE}/api/process/ipdr/letter?run_dir=${encodeURIComponent(c.run_dir)}&isp=${encodeURIComponent(isp)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: payloadFor(c.fir_number) })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail || 'Failed'); return }
      download(await res.blob(), `${isp.replace(/[\\/]/g, '_')}_Letter_${c.fir_number.replace(/\//g, '-')}.docx`)
      setMsg(`Letter for ${isp} (FIR ${c.fir_number}) downloaded ✓`)
      load()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setBusy(null) }
  }

  return (
    <section>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1>ISP Letters</h1>
          <p className="muted">Generate &amp; print ISP request letters for any processed case.</p>
        </div>
        <button className="btn btn-ghost" onClick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
      </div>

      {/* Shared letter details */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => setFormOpen(o => !o)}>
          <h2 style={{ margin: 0 }}>Letter Details (officer / case)</h2>
          <span className="muted" style={{ fontSize: 12 }}>{formOpen ? 'Hide ▲' : 'Edit ▼'}</span>
        </div>
        {formOpen && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10, marginTop: 12 }}>
            {([
              ['officer_name', 'Officer Name'],
              ['officer_designation', 'Officer Designation'],
              ['officer_location', 'Officer Location'],
              ['officer_contact', 'Officer Contact'],
              ['police_station', 'Police Station'],
              ['sections', 'Sections'],
              ['complainant', 'Complainant'],
              ['fir_date', 'FIR Date'],
              ['letter_date', 'Letter Date'],
            ] as Array<[keyof LetterForm, string]>).map(([key, label]) => (
              <label key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
                <span className="muted">{label}</span>
                <input className="input" value={form[key]} onChange={e => setField(key, e.target.value)} />
              </label>
            ))}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          <label className="muted" style={{ fontSize: 12 }}>Letter template</label>
          <select value={templateId} onChange={e => setTemplateId(e.target.value)} style={{ minWidth: 220 }}>
            {templates.map(t => (
              <option key={t.id} value={t.id}>
                {t.name}{t.scope === 'system' ? ' (default)' : t.scope === 'shared' ? ' (shared)' : ''}
              </option>
            ))}
          </select>
          <a href="/isp-letters/templates" className="muted" style={{ fontSize: 11 }}>Edit templates →</a>
        </div>
        <p className="muted" style={{ fontSize: 11, marginTop: formOpen ? 10 : 6, marginBottom: 0 }}>
          These details apply to every letter. The FIR number is filled automatically per case.
        </p>
      </div>

      {msg && <div className="badge info" style={{ padding: '10px 14px', margin: '8px 0' }}>{msg}</div>}
      {error && <div className="badge warning" style={{ padding: '10px 14px', margin: '8px 0' }}>{error}</div>}

      {loading && <p className="muted">Loading cases…</p>}
      {!loading && cases.length === 0 && (
        <div className="card"><p className="muted" style={{ margin: 0 }}>No processed cases yet. Upload &amp; enrich a case first, then its ISP letters appear here.</p></div>
      )}

      {cases.map(c => {
        const isOpen = expanded === c.fir_number
        const lastGen = fmtDate(c.last_generated_at)
        const shownIsps = isOpen
          ? c.isps.filter(x => !filter || x.isp.toLowerCase().includes(filter.toLowerCase()))
          : []
        return (
          <div className="card" key={c.fir_number} style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <h2 style={{ margin: '0 0 2px' }}>FIR {c.fir_number} <span style={{ color: 'var(--muted)', fontWeight: 400, fontSize: 14 }}>· {c.case_title || '—'}</span></h2>
                <div className="muted" style={{ fontSize: 12 }}>
                  {c.total_isps} ISPs · {c.unique_ips.toLocaleString()} unique IPs · {c.total_records.toLocaleString()} records
                  {lastGen && <span style={{ color: 'var(--green)', marginLeft: 8 }}>· Generated ✓ {lastGen}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  className="btn btn-primary"
                  style={{ minWidth: 220, transition: 'none' }}
                  disabled={busy === `${c.fir_number}:ALL`}
                  onClick={() => downloadAll(c)}
                >
                  {busy === `${c.fir_number}:ALL` ? `Generating ${c.total_isps} letters…` : `Download All ISP Letters (ZIP) · ${c.total_isps}`}
                </button>
                <button className="btn btn-ghost" onClick={() => { setExpanded(isOpen ? null : c.fir_number); setFilter('') }}>
                  {isOpen ? 'Hide ISPs ▲' : 'Per-ISP ▼'}
                </button>
              </div>
            </div>

            {isOpen && (
              <div style={{ marginTop: 12 }}>
                <input
                  className="input"
                  placeholder="Filter ISPs…"
                  value={filter}
                  onChange={e => setFilter(e.target.value)}
                  style={{ maxWidth: 280, marginBottom: 10 }}
                />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
                  {shownIsps.map(({ isp, count }) => (
                    <button
                      key={isp}
                      className="btn btn-ghost"
                      style={{ fontSize: 12 }}
                      disabled={busy === `${c.fir_number}:${isp}`}
                      onClick={() => downloadOne(c, isp)}
                      title={`${count} records`}
                    >
                      {busy === `${c.fir_number}:${isp}` ? '…' : `${isp} (${count})`}
                    </button>
                  ))}
                  {shownIsps.length === 0 && <span className="muted" style={{ fontSize: 12 }}>No ISPs match.</span>}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </section>
  )
}
