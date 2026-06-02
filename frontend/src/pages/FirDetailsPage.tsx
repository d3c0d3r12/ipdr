import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest, API_BASE } from '../lib/api'
import { useAuth } from '../lib/auth'

type Stats = {
  total_ip_lookups?: number
  unique_ips?: number
  unique_countries?: number
  unique_cities?: number
  total_isps?: number
  top_isps?: Array<{ isp: string; count: number }>
  run_dir?: string | null
}

type LookupRow = {
  ip_address?: string
  ip_type?: string
  country?: string
  city?: string
  isp?: string
  lookup_status?: string
}

type LetterForm = {
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

const FIXED_FIELDS = {
  subject: 'Reg provide information in case',
  email_reference: '',
  body_description:
    'It is to bring to your kind notice that a case has been registered in this police station. In the investigation of the said case, the IP addresses mentioned in the attachment are required to be verified. You are requested to provide the subscriber/user details along with CDR/IP logs for the mentioned IP addresses at the earliest to facilitate the investigation.',
}

export default function FirDetailsPage() {
  const { token } = useAuth()
  const { firNumber = '' } = useParams()
  const fir = decodeURIComponent(firNumber)
  const [stats, setStats] = useState<Stats>({})
  const [rows, setRows] = useState<LookupRow[]>([])

  // ── ISP letters ──────────────────────────────────────────────────────────
  const [letterForm, setLetterForm] = useState<LetterForm>({
    fir_number: fir,
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
  const [allLoading, setAllLoading] = useState(false)
  const [ispLoading, setIspLoading] = useState<string | null>(null)
  const [letterMsg, setLetterMsg] = useState('')
  const [letterErr, setLetterErr] = useState('')

  useEffect(() => {
    Promise.all([
      apiRequest<Stats>(`/api/fir/${encodeURIComponent(fir)}/statistics`, {}, token),
      apiRequest<{ ip_lookups: LookupRow[] }>(`/api/fir/${encodeURIComponent(fir)}/ip-lookups?limit=200`, {}, token)
    ]).then(([a, b]) => {
      if (a.success && a.data) setStats(a.data)
      if (b.success) setRows(b.data?.ip_lookups || [])
    })
  }, [fir, token])

  const runDir = stats.run_dir || ''

  const buildPayload = () => {
    const fd = new FormData()
    Object.entries({ ...letterForm, ...FIXED_FIELDS }).forEach(([k, v]) => fd.append(k, String(v)))
    return fd
  }

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    Object.assign(document.createElement('a'), { href: url, download: filename }).click()
    URL.revokeObjectURL(url)
  }

  const downloadAllLetters = async () => {
    if (!runDir || !token) { setLetterErr('No processed run found for this case.'); return }
    setLetterErr(''); setLetterMsg(''); setAllLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/process/ipdr/letters?run_dir=${encodeURIComponent(runDir)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: buildPayload() })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setLetterErr(d.detail || 'Failed to generate letters'); return }
      downloadBlob(await res.blob(), `ISP_Letters_${fir.replace(/\//g, '-')}.zip`)
      setLetterMsg('All ISP letters downloaded ✓')
    } catch (err) { setLetterErr(err instanceof Error ? err.message : 'Failed') }
    finally { setAllLoading(false) }
  }

  const downloadLetterForIsp = async (isp: string) => {
    if (!runDir || !token) { setLetterErr('No processed run found for this case.'); return }
    setLetterErr(''); setLetterMsg(''); setIspLoading(isp)
    try {
      const res = await fetch(
        `${API_BASE}/api/process/ipdr/letter?run_dir=${encodeURIComponent(runDir)}&isp=${encodeURIComponent(isp)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: buildPayload() })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setLetterErr(d.detail || 'Failed'); return }
      downloadBlob(await res.blob(), `${isp.replace(/[\\/]/g, '_')}_Letter_${fir.replace(/\//g, '-')}.docx`)
      setLetterMsg(`Letter for ${isp} downloaded ✓`)
    } catch (err) { setLetterErr(err instanceof Error ? err.message : 'Failed') }
    finally { setIspLoading(null) }
  }

  const setField = (k: keyof LetterForm, v: string) => setLetterForm(p => ({ ...p, [k]: v }))

  return (
    <section>
      <h1>FIR Details: {fir}</h1>
      <div className="grid-3">
        <div className="card metric"><strong>{stats.total_ip_lookups || 0}</strong><span>Total Lookups</span></div>
        <div className="card metric"><strong>{stats.unique_ips || 0}</strong><span>Unique IPs</span></div>
        <div className="card metric"><strong>{stats.unique_countries || 0}</strong><span>Countries</span></div>
      </div>

      {/* ── ISP LETTERS ── */}
      <div className="card">
        <h2>ISP Letters</h2>
        {!runDir && (
          <p className="muted" style={{ fontSize: 13 }}>No processed run found for this case yet. Upload &amp; enrich IPDR first.</p>
        )}
        {runDir && (
          <>
            <p className="muted" style={{ fontSize: 12, marginTop: -4 }}>
              Generate ISP request letters from this case's data (run <code>{runDir}</code>).
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10, margin: '12px 0' }}>
              {([
                ['fir_number', 'FIR Number'],
                ['fir_date', 'FIR Date'],
                ['letter_date', 'Letter Date'],
                ['police_station', 'Police Station'],
                ['sections', 'Sections'],
                ['complainant', 'Complainant'],
                ['officer_name', 'Officer Name'],
                ['officer_designation', 'Officer Designation'],
                ['officer_location', 'Officer Location'],
                ['officer_contact', 'Officer Contact'],
              ] as Array<[keyof LetterForm, string]>).map(([key, label]) => (
                <label key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
                  <span className="muted">{label}</span>
                  <input
                    className="input"
                    value={letterForm[key]}
                    onChange={e => setField(key, e.target.value)}
                  />
                </label>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                disabled={allLoading}
                onClick={downloadAllLetters}
                style={{ minWidth: 260, transition: 'none' }}
              >
                {allLoading
                  ? `Generating ${stats.total_isps || ''} letters…`
                  : `Download All ISP Letters (ZIP)${stats.total_isps ? ` · ${stats.total_isps} ISPs` : ''}`}
              </button>
              {letterMsg && <span className="badge info" style={{ padding: '6px 10px' }}>{letterMsg}</span>}
              {letterErr && <span className="badge warning" style={{ padding: '6px 10px' }}>{letterErr}</span>}
            </div>
            {allLoading && (
              <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
                Building one Word document per ISP — this can take ~30s for hundreds of ISPs. For a specific provider, use the single-ISP buttons below (faster).
              </p>
            )}

            {stats.top_isps && stats.top_isps.length > 0 && (
              <div style={{ marginTop: 14 }}>
                <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>Or download a single ISP's letter:</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {stats.top_isps.map(({ isp, count }) => (
                    <button
                      key={isp}
                      className="btn btn-ghost"
                      style={{ fontSize: 12 }}
                      disabled={ispLoading === isp}
                      onClick={() => downloadLetterForIsp(isp)}
                      title={`${count} records`}
                    >
                      {ispLoading === isp ? '…' : `${isp} (${count})`}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="card">
        <h2>IP Lookup Records</h2>
        <table>
          <thead>
            <tr>
              <th>IP</th>
              <th>Type</th>
              <th>Country</th>
              <th>City</th>
              <th>ISP</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.ip_address}-${i}`}>
                <td>{r.ip_address || '-'}</td>
                <td>{r.ip_type ? <span className="badge neutral">{r.ip_type}</span> : '-'}</td>
                <td>{r.country || '-'}</td>
                <td>{r.city || '-'}</td>
                <td>{r.isp || '-'}</td>
                <td>{r.lookup_status || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
