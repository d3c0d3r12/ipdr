import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '../lib/api'
import { useAuth } from '../lib/auth'

// ── Types ─────────────────────────────────────────────────────────────────────
type FirCase = {
  fir_number: string
  case_title: string
  status?: string
  priority?: string
  total_ips?: number
  created_at?: string
}

type EnrichTask = {
  task_id: string
  total_ips: number
  completed_ips: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  error?: string | null
}

type IspSummaryRow = { isp: string; count: number }
type TypeSummaryRow = { type: string; count: number }
type EnrichSummary = {
  run_dir: string
  generated_at: string
  total_unique_ips: number
  total_records: number
  by_isp: IspSummaryRow[]
  by_type?: TypeSummaryRow[]
  shared_ips: string[]
  tor_count?: number
  tor_list_loaded?: boolean
}

type EnrichedIpRow = {
  ip: string
  occurrences: number
  first_seen?: string
  last_seen?: string
  ip_type?: string
  is_tor?: boolean
  isp?: string
  organization?: string
  country?: string
  region?: string
  city?: string
  latitude?: string
  longitude?: string
  timezone?: string
  postal_code?: string
  source?: string
  whois?: unknown
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

type Stage = 'idle' | 'uploading' | 'enriching' | 'done' | 'failed'
type CaseMode = 'select' | 'create'

function normalizeRunDir(value: string) {
  const parts = value.trim().replace(/\\/g, '/').split('/').filter(Boolean)
  return parts[parts.length - 1] || ''
}

function today() {
  const d = new Date()
  return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
}

const PRIORITY_COLORS: Record<string, string> = {
  high: 'var(--red)', critical: 'var(--red)',
  medium: 'var(--orange)', low: 'var(--green)',
}

const _MOBILE_ISP = ['airtel', 'jio', 'vodafone', 'bsnl', 'mtnl', 'vi limited', 'idea', 'docomo', 'mobile', 'wireless', 'cellular', 'gsm', '4g', '5g']
const _VPS_ISP    = ['amazon', 'aws', 'google', 'microsoft', 'azure', 'digitalocean', 'linode', 'akamai', 'cloudflare', 'vultr', 'hetzner', 'ovh', 'contabo', 'leaseweb', 'hosting', 'cloud', 'datacenter', 'server', 'rackspace', 'oracle cloud', 'fastly', 'zscaler']
const _BB_ISP     = ['act fibernet', 'hathway', 'excitel', 'you broadband', 'den networks', 'sify', 'spectranet', 'atria', 'connect broadband', 'broadband', 'fiber', 'ftth', 'dsl', 'cable']

function ispCategory(isp: string): { label: string; color: string; bg: string; border: string } {
  const l = isp.toLowerCase()
  if (_MOBILE_ISP.some(k => l.includes(k))) return { label: 'Mobile/Telecom', color: 'var(--cyan)',   bg: 'rgba(37,99,235,0.08)',  border: 'rgba(37,99,235,0.2)' }
  if (_VPS_ISP.some(k => l.includes(k)))    return { label: 'VPS/Hosting',    color: 'var(--orange)', bg: 'rgba(234,88,12,0.08)',  border: 'rgba(234,88,12,0.2)' }
  if (_BB_ISP.some(k => l.includes(k)))     return { label: 'Broadband',      color: 'var(--green)',  bg: 'rgba(22,163,74,0.08)',  border: 'rgba(22,163,74,0.2)' }
  return { label: 'ISP', color: 'var(--muted)', bg: '#f3f4f6', border: 'var(--border)' }
}

function typeBadge(ipType: string | undefined, isTor: boolean | undefined): { label: string; color: string; bg: string } {
  if (isTor || ipType === 'TOR') return { label: 'TOR',      color: '#dc2626', bg: 'rgba(220,38,38,0.08)' }
  switch (ipType) {
    case 'VPN':         return { label: 'VPN',      color: 'var(--orange)', bg: 'rgba(234,88,12,0.08)' }
    case 'VPS':         return { label: 'VPS',       color: '#ea580c',       bg: 'rgba(234,88,12,0.08)' }
    case 'Datacenter':  return { label: 'VPS',       color: '#ea580c',       bg: 'rgba(234,88,12,0.08)' }
    case 'Mobile':      return { label: 'Mobile',    color: 'var(--cyan)',   bg: 'rgba(37,99,235,0.08)' }
    case 'Residential': return { label: 'Broadband', color: 'var(--green)',  bg: 'rgba(22,163,74,0.08)' }
    case 'IPv6':        return { label: 'IPv6',       color: 'var(--purple)', bg: 'rgba(124,58,237,0.08)' }
    default:            return { label: ipType || 'IPv4', color: 'var(--muted)', bg: '#f3f4f6' }
  }
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function UploadPage() {
  const { token } = useAuth()

  // ── Step 1: Case selection ──────────────────────────────────────────────────
  const [selectedCase, setSelectedCase] = useState<FirCase | null>(null)
  const [caseMode, setCaseMode] = useState<CaseMode>('select')
  const [existingCases, setExistingCases] = useState<FirCase[]>([])
  const [casesLoading, setCasesLoading] = useState(false)
  const [caseSearch, setCaseSearch] = useState('')
  const [caseError, setCaseError] = useState('')
  const [caseCreating, setCaseCreating] = useState(false)
  const [newCase, setNewCase] = useState({
    fir_number: '', case_title: '', priority: 'medium', case_description: '',
  })

  // ── Step 2: Upload + enrichment ─────────────────────────────────────────────
  const [file, setFile] = useState<File | null>(null)
  const [preserveDuplicates, setPreserveDuplicates] = useState(false)
  const [stage, setStage] = useState<Stage>('idle')
  const [runDir, setRunDir] = useState(localStorage.getItem('latest_run_dir') || '')
  const [task, setTask] = useState<EnrichTask | null>(null)
  const [summary, setSummary] = useState<EnrichSummary | null>(null)
  const [results, setResults] = useState<EnrichedIpRow[]>([])
  const [resultsTotal, setResultsTotal] = useState(0)
  const [resultsPage, setResultsPage] = useState(1)
  const [selected, setSelected] = useState<EnrichedIpRow | null>(null)
  const [error, setError] = useState('')
  const RESULTS_PAGE_SIZE = 100

  // ── Letters ─────────────────────────────────────────────────────────────────
  const [lettersLoading, setLettersLoading] = useState(false)
  const [letterIspLoading, setLetterIspLoading] = useState<string | null>(null)
  const [letterMsg, setLetterMsg] = useState('')
  const [letterFormOpen, setLetterFormOpen] = useState(false)
  const [letterForm, setLetterForm] = useState<LetterForm>({
    fir_number: '',
    fir_date: today(),
    letter_date: today(),
    police_station: 'Special Cell',
    sections: '',
    complainant: '',
    officer_name: '',
    officer_designation: 'IFSO, Special Cell',
    officer_location: 'Sec. 16C, Dwarka, New Delhi',
    officer_contact: '',
  })

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Fetch existing cases ────────────────────────────────────────────────────
  useEffect(() => {
    if (!token) return
    setCasesLoading(true)
    fetch(`${API_BASE}/api/fir/?limit=100`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setExistingCases(d.cases || []))
      .catch(() => {})
      .finally(() => setCasesLoading(false))
  }, [token])

  // ── Filtered cases for search ───────────────────────────────────────────────
  const filteredCases = existingCases.filter(c =>
    !caseSearch || c.fir_number.toLowerCase().includes(caseSearch.toLowerCase()) ||
    c.case_title?.toLowerCase().includes(caseSearch.toLowerCase())
  )

  // ── Create new case ─────────────────────────────────────────────────────────
  const handleCreateCase = async () => {
    if (!newCase.fir_number.trim() || !newCase.case_title.trim()) {
      setCaseError('FIR Number and Case Title are required')
      return
    }
    setCaseCreating(true)
    setCaseError('')
    try {
      const res = await fetch(`${API_BASE}/api/fir/create`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newCase),
      })
      const data = await res.json()
      if (!res.ok) {
        setCaseError(data.detail || 'Failed to create case')
        return
      }
      const created: FirCase = {
        fir_number: newCase.fir_number.trim(),
        case_title: newCase.case_title.trim(),
        priority: newCase.priority,
        status: 'active',
      }
      setExistingCases(prev => [created, ...prev])
      confirmSelectCase(created)
    } catch {
      setCaseError('Network error — could not create case')
    } finally {
      setCaseCreating(false)
    }
  }

  const confirmSelectCase = (c: FirCase) => {
    setSelectedCase(c)
    setLetterForm(p => ({ ...p, fir_number: c.fir_number }))
    setCaseError('')
  }

  // ── Poll enrichment ─────────────────────────────────────────────────────────
  const stopPoll = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  const loadResults = useCallback(async (rd: string, page = 1) => {
    const offset = (page - 1) * RESULTS_PAGE_SIZE
    const [sRes, rRes] = await Promise.all([
      fetch(`${API_BASE}/api/process/ipdr/enrich/summary?run_dir=${encodeURIComponent(rd)}`,
        { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_BASE}/api/process/ipdr/enrich/results?run_dir=${encodeURIComponent(rd)}&limit=${RESULTS_PAGE_SIZE}&offset=${offset}`,
        { headers: { Authorization: `Bearer ${token}` } }),
    ])
    const sd = await sRes.json().catch(() => ({}))
    const rd2 = await rRes.json().catch(() => ({}))
    if (sRes.ok) setSummary(sd as EnrichSummary)
    if (rRes.ok) {
      setResults((rd2.results || []) as EnrichedIpRow[])
      setResultsTotal(rd2.total ?? rd2.count ?? 0)
      setResultsPage(page)
    }
  }, [token, RESULTS_PAGE_SIZE])

  const pollStatus = useCallback(async (taskId: string) => {
    const res = await fetch(
      `${API_BASE}/api/process/ipdr/enrich/status?task_id=${encodeURIComponent(taskId)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    const data: EnrichTask = await res.json().catch(() => ({}))
    if (!res.ok) return
    setTask(data)
    if (data.status === 'completed') {
      stopPoll()
      setStage('done')
      const rd = normalizeRunDir(runDir)
      if (rd) await loadResults(rd)
    } else if (data.status === 'failed') {
      stopPoll()
      setStage('failed')
      setError(data.error || 'Enrichment failed')
    }
  }, [token, runDir, loadResults])

  const startEnrich = useCallback(async (rd: string) => {
    setStage('enriching')
    setError('')
    const res = await fetch(
      `${API_BASE}/api/process/ipdr/enrich/start?run_dir=${encodeURIComponent(rd)}`,
      { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
    )
    const data = await res.json().catch(() => ({}))
    if (!res.ok) { setError(data.detail || 'Failed to start enrichment'); setStage('failed'); return }

    const t: EnrichTask = { task_id: data.task_id, total_ips: data.total_ips, completed_ips: 0, status: 'running', progress: 0 }
    setTask(t)
    pollRef.current = setInterval(() => { void pollStatus(data.task_id) }, 1200)
    void pollStatus(data.task_id)
  }, [token, pollStatus])

  useEffect(() => () => stopPoll(), [])

  // ── Upload submit ───────────────────────────────────────────────────────────
  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!file || !token || !selectedCase) return

    stopPoll()
    setStage('uploading')
    setError('')
    setSummary(null)
    setResults([])
    setTask(null)
    setSelected(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('fir', selectedCase.fir_number)
    formData.append('preserve_duplicates', String(preserveDuplicates))

    try {
      const res = await fetch(`${API_BASE}/api/upload/`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Upload failed'); setStage('failed'); return }

      const rd = normalizeRunDir(data.run_dir || data.output_dir || '')
      if (rd) {
        localStorage.setItem('latest_run_dir', rd)
        setRunDir(rd)
        await startEnrich(rd)
      } else {
        setError('No run directory returned from server')
        setStage('failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload error')
      setStage('failed')
    }
  }

  // ── Reset ───────────────────────────────────────────────────────────────────
  const resetAll = () => {
    stopPoll()
    localStorage.removeItem('latest_run_dir')
    setFile(null)
    setPreserveDuplicates(false)
    setStage('idle')
    setRunDir('')
    setTask(null)
    setSummary(null)
    setResults([])
    setResultsTotal(0)
    setResultsPage(1)
    setSelected(null)
    setError('')
    setLetterMsg('')
    setSelectedCase(null)
    setCaseSearch('')
    setCaseError('')
    setNewCase({ fir_number: '', case_title: '', priority: 'medium', case_description: '' })
    setCaseMode('select')
  }

  // ── ISP Letters ─────────────────────────────────────────────────────────────
  const buildLetterPayload = () => {
    const fd = new FormData()
    Object.entries({ ...letterForm, ...FIXED_FIELDS }).forEach(([k, v]) => fd.append(k, v))
    return fd
  }

  const downloadLetters = async () => {
    const rd = normalizeRunDir(runDir)
    if (!rd || !token) return
    setLetterMsg('')
    setError('')
    const missing = (Object.keys(letterForm) as (keyof LetterForm)[]).find(k => !String(letterForm[k] || '').trim())
    if (missing) { setError(`Missing: ${missing.replace(/_/g, ' ')}`); return }
    setLettersLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/process/ipdr/letters?run_dir=${encodeURIComponent(rd)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: buildLetterPayload() })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail || 'Failed to generate letters'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: `ISP_Letters_${letterForm.fir_number.replace(/\//g, '-')}.zip` }).click()
      URL.revokeObjectURL(url)
      setLetterMsg('All ISP letters downloaded ✓')
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed') }
    finally { setLettersLoading(false) }
  }

  const downloadLetterForIsp = async (isp: string) => {
    const rd = normalizeRunDir(runDir)
    if (!rd || !token) return
    if (!letterForm.fir_number || !letterForm.officer_name) { setError('Fill FIR number & officer name first'); return }
    setLetterIspLoading(isp)
    setError('')
    try {
      const res = await fetch(
        `${API_BASE}/api/process/ipdr/letter?run_dir=${encodeURIComponent(rd)}&isp=${encodeURIComponent(isp)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: buildLetterPayload() })
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail || 'Failed'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: `${isp.replace(/[\\/]/g, '_')}_Letter_${letterForm.fir_number.replace(/\//g, '-')}.docx` }).click()
      URL.revokeObjectURL(url)
    } catch (err) { setError(err instanceof Error ? err.message : 'Failed') }
    finally { setLetterIspLoading(null) }
  }

  const progress = task ? Math.round(task.progress ?? (task.total_ips > 0 ? (task.completed_ips / task.total_ips) * 100 : 0)) : 0
  const rd = normalizeRunDir(runDir)
  const busy = stage === 'uploading' || stage === 'enriching'

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <section style={{ padding: 0 }}>

      {/* ══════════════════════════════════════════════════════════════
          SETUP PHASE — centered wizard (no results yet)
      ══════════════════════════════════════════════════════════════ */}
      {!summary && !busy && (
        <div style={{ maxWidth: 580, margin: '0 auto', padding: '4px 0 32px', display: 'grid', gap: 14 }}>

          {/* Page header */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div>
              <h1 style={{ marginBottom: 4 }}>Upload IPDR</h1>
              <p className="muted" style={{ fontSize: 13, margin: 0 }}>Select or create a FIR case, then upload the file for enrichment.</p>
            </div>
            <a href="/multi-file-upload" className="btn btn-ghost" style={{ fontSize: 12, whiteSpace: 'nowrap', flexShrink: 0 }}>Multi-file ↗</a>
          </div>

          {/* Step track */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
            {([
              { n: '1', label: 'Select Case', done: !!selectedCase, active: !selectedCase },
              { n: '2', label: 'Upload & Process', done: false, active: !!selectedCase },
            ] as const).map((s, i) => (
              <div key={s.n} style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 7, padding: '7px 13px', borderRadius: 8,
                  background: s.active ? 'rgba(37,99,235,0.06)' : s.done ? 'rgba(22,163,74,0.06)' : '#f9fafb',
                  border: `1px solid ${s.active ? 'rgba(37,99,235,0.25)' : s.done ? 'rgba(22,163,74,0.2)' : 'var(--border)'}`,
                }}>
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700,
                    background: s.done ? 'rgba(22,163,74,0.1)' : s.active ? 'rgba(37,99,235,0.1)' : '#f3f4f6',
                    color: s.done ? 'var(--green)' : s.active ? 'var(--cyan)' : 'var(--muted)',
                  }}>{s.done ? '✓' : s.n}</div>
                  <span style={{ fontSize: 12, fontWeight: s.active ? 600 : 500, color: s.active ? 'var(--text-bright)' : s.done ? 'var(--green)' : 'var(--muted)' }}>{s.label}</span>
                </div>
                {i < 1 && <svg width="24" height="10" viewBox="0 0 24 10" fill="none" style={{ flexShrink: 0 }}><path d="M0 5h20M16 1l4 4-4 4" stroke="var(--border)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>}
              </div>
            ))}
          </div>

          {stage === 'failed' && error && <div className="alert error">{error}</div>}

          {/* STEP 1 — Case */}
          {!selectedCase ? (
            <div className="card" style={{ marginBottom: 0 }}>
              <h2 style={{ marginBottom: 14 }}>Step 1 — FIR Case</h2>
              <div style={{ display: 'flex', gap: 5, marginBottom: 14, background: '#f3f4f6', borderRadius: 8, padding: 4 }}>
                {(['select', 'create'] as CaseMode[]).map(m => (
                  <button key={m} type="button" onClick={() => { setCaseMode(m); setCaseError('') }} style={{
                    flex: 1, padding: '7px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    border: 'none', transition: 'all 0.15s',
                    background: caseMode === m ? (m === 'create' ? 'rgba(37,99,235,0.1)' : 'rgba(124,58,237,0.1)') : 'transparent',
                    color: caseMode === m ? (m === 'create' ? 'var(--cyan)' : 'var(--purple)') : 'var(--muted)',
                    boxShadow: caseMode === m ? `0 0 0 1px ${m === 'create' ? 'rgba(37,99,235,0.2)' : 'rgba(124,58,237,0.2)'}` : 'none',
                  }}>{m === 'select' ? '📂 Select Existing' : '✚ Create New'}</button>
                ))}
              </div>

              {caseMode === 'select' && (
                <>
                  <input placeholder="Search FIR number or title…" value={caseSearch} onChange={e => setCaseSearch(e.target.value)} style={{ marginBottom: 10 }} />
                  {casesLoading
                    ? <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--muted)', fontSize: 13, padding: '10px 0' }}><Spinner /> Loading cases…</div>
                    : filteredCases.length === 0
                      ? <div style={{ fontSize: 13, color: 'var(--muted)', padding: '10px 0', textAlign: 'center' }}>{existingCases.length === 0 ? 'No cases yet — create one' : 'No matches found'}</div>
                      : <div style={{ display: 'grid', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
                          {filteredCases.map(c => (
                            <button key={c.fir_number} type="button" onClick={() => confirmSelectCase(c)} style={{
                              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                              padding: '10px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'left',
                              background: '#ffffff', border: '1px solid var(--border)', transition: 'border-color 0.15s, background 0.15s',
                            }}
                              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(124,58,237,0.3)'; (e.currentTarget as HTMLElement).style.background = 'rgba(124,58,237,0.04)' }}
                              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.background = '#ffffff' }}>
                              <div>
                                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--purple)', marginBottom: 2 }}>{c.fir_number}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-bright)', fontWeight: 500 }}>{c.case_title}</div>
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3, flexShrink: 0 }}>
                                {c.priority && <span style={{ fontSize: 10, fontWeight: 700, color: PRIORITY_COLORS[c.priority.toLowerCase()] || 'var(--muted)', textTransform: 'uppercase' }}>{c.priority}</span>}
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="var(--muted)" strokeWidth="2" strokeLinecap="round" /></svg>
                              </div>
                            </button>
                          ))}
                        </div>
                  }
                  {caseError && <div className="alert error" style={{ marginTop: 8 }}>{caseError}</div>}
                </>
              )}

              {caseMode === 'create' && (
                <div style={{ display: 'grid', gap: 10 }}>
                  <div><label>FIR Number *</label><input value={newCase.fir_number} onChange={e => setNewCase(p => ({ ...p, fir_number: e.target.value }))} placeholder="e.g. 201/25" style={{ fontFamily: 'JetBrains Mono, monospace' }} /></div>
                  <div><label>Case Title *</label><input value={newCase.case_title} onChange={e => setNewCase(p => ({ ...p, case_title: e.target.value }))} placeholder="e.g. Cyber Fraud — Online Banking" /></div>
                  <div>
                    <label>Priority</label>
                    <select value={newCase.priority} onChange={e => setNewCase(p => ({ ...p, priority: e.target.value }))} style={{ width: '100%' }}>
                      <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
                    </select>
                  </div>
                  <div><label>Description (optional)</label><input value={newCase.case_description} onChange={e => setNewCase(p => ({ ...p, case_description: e.target.value }))} placeholder="Brief description" /></div>
                  {caseError && <div className="alert error">{caseError}</div>}
                  <button type="button" className="btn btn-primary" onClick={handleCreateCase} disabled={caseCreating} style={{ fontSize: 13, padding: '10px' }}>
                    {caseCreating ? <><Spinner /> Creating…</> : <><svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg> Create Case &amp; Continue</>}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ marginBottom: 0, borderColor: 'rgba(124,58,237,0.2)', background: 'rgba(124,58,237,0.03)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 4 }}>Active Case</div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: 'var(--purple)', fontWeight: 700, marginBottom: 2 }}>{selectedCase.fir_number}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-bright)', fontWeight: 600, marginBottom: 6 }}>{selectedCase.case_title}</div>
                  <div style={{ display: 'flex', gap: 10 }}>
                    {selectedCase.status && <span style={{ fontSize: 11, color: 'var(--muted)' }}>Status: <span style={{ color: 'var(--cyan)' }}>{selectedCase.status}</span></span>}
                    {selectedCase.priority && <span style={{ fontSize: 11, color: PRIORITY_COLORS[selectedCase.priority.toLowerCase()] || 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>{selectedCase.priority}</span>}
                  </div>
                </div>
                <button type="button" className="btn btn-ghost" onClick={() => { setSelectedCase(null); setCaseError(''); setSummary(null); setResults([]); setStage('idle') }} style={{ fontSize: 11, padding: '5px 10px', flexShrink: 0 }}>Change</button>
              </div>
            </div>
          )}

          {/* STEP 2 — Upload */}
          {selectedCase && (
            <div className="card" style={{ marginBottom: 0 }}>
              <h2 style={{ marginBottom: 14 }}>Step 2 — Upload IPDR File</h2>
              <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12 }}>
                <div>
                  <label>IPDR File (HTML or CSV)</label>
                  <input type="file" accept=".html,.htm,.csv" onChange={e => setFile(e.target.files?.[0] || null)} required />
                  {file && <div style={{ fontSize: 11, color: 'var(--cyan)', marginTop: 4, fontFamily: 'JetBrains Mono, monospace' }}>✓ {file.name}</div>}
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, color: 'var(--text)', textTransform: 'none', letterSpacing: 0, fontWeight: 500 }}>
                  <input type="checkbox" checked={preserveDuplicates} onChange={e => setPreserveDuplicates(e.target.checked)} style={{ width: 'auto', accentColor: 'var(--cyan)' }} />
                  Preserve duplicate IP entries
                </label>
                <button className="btn btn-primary" disabled={!file || !token} style={{ padding: '11px', fontSize: 13 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v10m0-10 4 4m-4-4-4 4M4 17v2h16v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                  Upload &amp; Process
                </button>
                {!token && <div className="alert error">Login required</div>}
              </form>
            </div>
          )}

          {/* Last run shortcut */}
          {selectedCase && runDir && (
            <div className="card" style={{ marginBottom: 0, padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 3 }}>Previous run</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--cyan)' }}>{runDir}</div>
              </div>
              <button className="btn" style={{ fontSize: 11, padding: '5px 12px', flexShrink: 0 }} onClick={() => loadResults(normalizeRunDir(runDir))}>Load Results</button>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          PROGRESS PHASE
      ══════════════════════════════════════════════════════════════ */}
      {busy && (
        <div style={{ maxWidth: 620, margin: '32px auto' }}>
          <div className="card" style={{ borderColor: 'rgba(37,99,235,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(37,99,235,0.06)', border: '1px solid rgba(37,99,235,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Spinner color="var(--cyan)" />
              </div>
              <div>
                <div style={{ fontWeight: 700, color: 'var(--text-bright)', fontSize: 15 }}>{stage === 'uploading' ? 'Uploading & Parsing File…' : 'Enriching IP Data…'}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                  {stage === 'uploading' ? 'Extracting IP addresses from IPDR file' : task ? `${task.completed_ips} / ${task.total_ips} IPs enriched` : 'Starting enrichment engine…'}
                </div>
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 7, fontSize: 11 }}>
                <span style={{ color: 'var(--muted)' }}>{stage === 'uploading' ? 'Upload' : 'GeoIP · ASN · VPS / TOR Detection'}</span>
                <span style={{ fontFamily: 'Orbitron, monospace', color: 'var(--cyan)', fontWeight: 700 }}>{stage === 'uploading' ? '—' : `${progress}%`}</span>
              </div>
              <div className="progress-bar" style={{ height: 7, borderRadius: 4 }}>
                <div className="progress-fill" style={{ width: stage === 'uploading' ? '100%' : `${Math.max(progress, 3)}%`, borderRadius: 4 }} />
              </div>
            </div>
            {task && (
              <div className="mini-grid">
                {[{ label: 'Total IPs', value: task.total_ips }, { label: 'Completed', value: task.completed_ips }, { label: 'Status', value: task.status }].map(item => (
                  <div key={item.label} className="metric-box">
                    <strong style={{ fontFamily: 'Orbitron, monospace', fontSize: 16 }}>{item.value}</strong>
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          RESULTS PHASE — two-panel layout
      ══════════════════════════════════════════════════════════════ */}
      {summary && (
        <div>
          {/* ── Results top bar ── */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: 12, flexWrap: 'wrap', marginBottom: 14,
            padding: '11px 16px', borderRadius: 10,
            background: 'rgba(22,163,74,0.04)', border: '1px solid rgba(22,163,74,0.15)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              {/* Case badge */}
              {selectedCase && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingRight: 12, borderRight: '1px solid var(--border)' }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" /></svg>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--purple)', fontWeight: 700 }}>{selectedCase.fir_number}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-bright)', fontWeight: 600 }}>{selectedCase.case_title}</span>
                </div>
              )}
              {/* Stat pills */}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                <StatPill label="Entries" value={summary.total_records} />
                <StatPill label="Unique IPs" value={summary.total_unique_ips} />
                <StatPill label="Repeated" value={summary.shared_ips?.length || 0} />
                {(summary.tor_count ?? 0) > 0 && <StatPill label="TOR" value={summary.tor_count!} color="var(--red)" bg="rgba(220,38,38,0.06)" border="rgba(220,38,38,0.2)" />}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <a className="btn" style={{ fontSize: 11, padding: '5px 10px' }} href={`${API_BASE}/api/process/ipdr/enrich/export/csv?run_dir=${encodeURIComponent(rd)}`} target="_blank" rel="noreferrer">CSV</a>
              <a className="btn" style={{ fontSize: 11, padding: '5px 10px' }} href={`${API_BASE}/api/process/ipdr/enrich/export/json?run_dir=${encodeURIComponent(rd)}`} target="_blank" rel="noreferrer">JSON</a>
              <a className="btn" style={{ fontSize: 11, padding: '5px 10px' }} href={`${API_BASE}/api/process/ipdr/enrich/export/pdf?run_dir=${encodeURIComponent(rd)}`} target="_blank" rel="noreferrer">PDF</a>
              <button className="btn btn-ghost" onClick={resetAll} style={{ fontSize: 11, color: 'var(--red)', borderColor: 'rgba(255,51,102,0.25)', padding: '5px 10px' }}>Reset</button>
            </div>
          </div>

          {stage === 'failed' && error && <div className="alert error" style={{ marginBottom: 12 }}>{error}</div>}

          {/* ── Two-panel grid ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 14, alignItems: 'start' }}>

            {/* ── LEFT PANEL: ISP breakdown + Letter form ── */}
            <div style={{ display: 'grid', gap: 12, position: 'sticky', top: 0 }}>

              {/* ISP Breakdown */}
              {(summary.by_isp || []).length > 0 && (
                <IspBreakdownTable
                  rows={summary.by_isp}
                  totalUniqueIps={summary.total_unique_ips}
                  torCount={summary.tor_count}
                  torListLoaded={summary.tor_list_loaded}
                  byType={summary.by_type}
                  letterIspLoading={letterIspLoading}
                  onDownloadLetter={downloadLetterForIsp}
                  token={!!token}
                />
              )}

              {/* Collapsible letter form */}
              <div className="card" style={{ marginBottom: 0 }}>
                <button type="button" onClick={() => setLetterFormOpen(x => !x)} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  width: '100%', background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 15V3M12 15l-4-4m4 4 4-4M2 17v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2" stroke="var(--cyan)" strokeWidth="2" strokeLinecap="round" /></svg>
                    <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-bright)' }}>Generate ISP Letters</span>
                  </div>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" style={{ transition: 'transform 0.2s', transform: letterFormOpen ? 'rotate(180deg)' : 'none' }}>
                    <path d="M6 9l6 6 6-6" stroke="var(--muted)" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </button>

                {letterFormOpen && (
                  <div style={{ marginTop: 14, display: 'grid', gap: 10 }}>
                    <p className="muted" style={{ fontSize: 11, margin: 0 }}>Fill case-specific details — standard body text is auto-applied.</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <LField label="FIR Number *" value={letterForm.fir_number} onChange={v => setLetterForm(p => ({ ...p, fir_number: v }))} mono />
                      <LField label="FIR Date *" value={letterForm.fir_date} onChange={v => setLetterForm(p => ({ ...p, fir_date: v }))} placeholder="DD.MM.YYYY" />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <LField label="Letter Date *" value={letterForm.letter_date} onChange={v => setLetterForm(p => ({ ...p, letter_date: v }))} placeholder="DD.MM.YYYY" />
                      <LField label="Police Station *" value={letterForm.police_station} onChange={v => setLetterForm(p => ({ ...p, police_station: v }))} />
                    </div>
                    <LField label="IPC Sections *" value={letterForm.sections} onChange={v => setLetterForm(p => ({ ...p, sections: v }))} placeholder="e.g. 420, 66(C) IT Act" />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <LField label="Officer Name *" value={letterForm.officer_name} onChange={v => setLetterForm(p => ({ ...p, officer_name: v }))} />
                      <LField label="Contact *" value={letterForm.officer_contact} onChange={v => setLetterForm(p => ({ ...p, officer_contact: v }))} placeholder="+91 98XXXXXXXX" />
                    </div>
                    <LField label="Designation *" value={letterForm.officer_designation} onChange={v => setLetterForm(p => ({ ...p, officer_designation: v }))} />
                    <LField label="Officer Location *" value={letterForm.officer_location} onChange={v => setLetterForm(p => ({ ...p, officer_location: v }))} />
                    <LField label="Complainant *" value={letterForm.complainant} onChange={v => setLetterForm(p => ({ ...p, complainant: v }))} />
                    {error && <div className="alert error">{error}</div>}
                    {letterMsg && <div className="alert success">{letterMsg}</div>}
                    <button className="btn btn-primary" onClick={downloadLetters} disabled={lettersLoading || !token} style={{ fontSize: 12, padding: '9px 14px' }}>
                      {lettersLoading ? <><Spinner /> Generating…</> : <><svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 15V3M12 15l-4-4m4 4 4-4M2 17v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg> Download All Letters (ZIP)</>}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* ── RIGHT PANEL: IP Results ── */}
            <div className="card" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <h2 style={{ margin: 0 }}>
                  IP Records
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: 'var(--cyan)', marginLeft: 8, fontWeight: 400 }}>{resultsTotal.toLocaleString()}</span>
                </h2>
                {selected && <button className="btn btn-ghost" style={{ fontSize: 11, padding: '4px 8px' }} onClick={() => setSelected(null)}>✕ Close Detail</button>}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 290px' : '1fr', gap: 12 }}>
                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: 36 }}>#</th>
                        <th>IP Address</th>
                        <th>ISP</th>
                        <th>Country</th>
                        <th>City</th>
                        <th style={{ width: 80 }}>Type</th>
                        <th style={{ width: 50 }}>Uses</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((r, i) => {
                        const badge = typeBadge(r.ip_type, r.is_tor)
                        return (
                          <tr key={r.ip} onClick={() => setSelected(selected?.ip === r.ip ? null : r)} style={{ cursor: 'pointer', background: r.is_tor ? 'rgba(220,38,38,0.04)' : selected?.ip === r.ip ? 'rgba(37,99,235,0.04)' : undefined }}>
                            <td style={{ color: 'var(--muted)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}>{(resultsPage - 1) * RESULTS_PAGE_SIZE + i + 1}</td>
                            <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: r.is_tor ? 'var(--red)' : 'var(--cyan)' }}>{r.ip}</td>
                            <td style={{ fontSize: 12, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.isp || '—'}</td>
                            <td style={{ fontSize: 12 }}>{r.country || '—'}</td>
                            <td style={{ fontSize: 12 }}>{r.city || '—'}</td>
                            <td>
                              <span style={{ display: 'inline-block', padding: '2px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700, letterSpacing: '0.4px', color: badge.color, background: badge.bg }}>
                                {badge.label}
                              </span>
                            </td>
                            <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>{r.occurrences || 0}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>

                  {resultsTotal > RESULTS_PAGE_SIZE && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, flexWrap: 'wrap', gap: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--muted)' }}>Page {resultsPage} of {Math.ceil(resultsTotal / RESULTS_PAGE_SIZE)} · {resultsTotal.toLocaleString()} total</span>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn" style={{ fontSize: 11, padding: '4px 10px' }} disabled={resultsPage <= 1} onClick={() => loadResults(normalizeRunDir(runDir), resultsPage - 1)}>← Prev</button>
                        <button className="btn" style={{ fontSize: 11, padding: '4px 10px' }} disabled={resultsPage >= Math.ceil(resultsTotal / RESULTS_PAGE_SIZE)} onClick={() => loadResults(normalizeRunDir(runDir), resultsPage + 1)}>Next →</button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Detail pane */}
                {selected && (
                  <div style={{ background: '#f9fafb', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                      {(() => { const b = typeBadge(selected.ip_type, selected.is_tor); return <span style={{ padding: '3px 8px', borderRadius: 5, fontSize: 10, fontWeight: 700, color: b.color, background: b.bg }}>{b.label}</span> })()}
                      <span style={{ fontFamily: 'Orbitron, monospace', fontSize: 12, color: selected.is_tor ? 'var(--red)' : 'var(--cyan)', fontWeight: 700 }}>{selected.ip}</span>
                    </div>
                    {([['ISP', selected.isp], ['Organization', selected.organization], ['Country', selected.country], ['Region', selected.region], ['City', selected.city], ['Timezone', selected.timezone], ['IP Type', selected.ip_type], ['TOR Exit', selected.is_tor ? 'Yes' : null], ['Occurrences', String(selected.occurrences || 0)], ['First Seen', selected.first_seen], ['Last Seen', selected.last_seen]] as [string, string | undefined | null][])
                      .filter(([, v]) => v)
                      .map(([label, value]) => (
                        <div key={label} style={{ marginBottom: 8, display: 'grid', gridTemplateColumns: '90px 1fr', gap: 6 }}>
                          <span style={{ color: 'var(--muted)', fontSize: 10 }}>{label}</span>
                          <span style={{ color: label === 'TOR Exit' ? 'var(--red)' : 'var(--text-bright)', fontSize: 11, wordBreak: 'break-all', fontWeight: label === 'TOR Exit' ? 700 : 400 }}>{value}</span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </section>
  )
}

// ── ISP Breakdown Table ───────────────────────────────────────────────────────
function IspBreakdownTable({
  rows, totalUniqueIps, torCount, torListLoaded, byType,
  letterIspLoading, onDownloadLetter, token,
}: {
  rows: IspSummaryRow[]
  totalUniqueIps: number
  torCount?: number
  torListLoaded?: boolean
  byType?: TypeSummaryRow[]
  letterIspLoading: string | null
  onDownloadLetter: (isp: string) => void
  token: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const maxRow = rows.reduce((m, r) => Math.max(m, r.count), 1)
  const visible = expanded ? rows : rows.slice(0, 12)

  return (
    <div className="card" style={{ marginBottom: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <h2 style={{ margin: 0 }}>ISP Breakdown</h2>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--muted)', background: '#f3f4f6', border: '1px solid var(--border)', borderRadius: 5, padding: '2px 7px' }}>
            {rows.length} ISPs
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {/* TOR count badge */}
          {(torCount ?? 0) > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 9px', borderRadius: 6, background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.2)', fontSize: 11, fontWeight: 700, color: 'var(--red)' }}>
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.2"/><path d="M12 8v5M12 16v.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>
              {torCount} TOR exit IPs
            </span>
          )}
          {torListLoaded === false && (
            <span style={{ padding: '3px 9px', borderRadius: 6, background: 'rgba(234,88,12,0.06)', border: '1px solid rgba(234,88,12,0.2)', fontSize: 10, color: 'var(--orange)' }}>
              TOR list not loaded — run update_tor_list.py
            </span>
          )}
        </div>
      </div>

      {/* Type breakdown pills */}
      {byType && byType.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {byType.map(t => {
            const b = typeBadge(t.type, false)
            const pct = totalUniqueIps > 0 ? Math.round((t.count / totalUniqueIps) * 100) : 0
            return (
              <div key={t.type} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 6, background: b.bg, border: `1px solid ${b.color}33`, fontSize: 11 }}>
                <span style={{ fontWeight: 700, color: b.color }}>{t.type}</span>
                <span style={{ color: 'var(--muted)' }}>·</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-bright)', fontSize: 11 }}>{t.count}</span>
                <span style={{ color: 'var(--muted)', fontSize: 10 }}>{pct}%</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ tableLayout: 'fixed', width: '100%' }}>
          <colgroup>
            <col style={{ width: 26 }} />
            <col style={{ width: '30%' }} />
            <col style={{ width: 110 }} />
            <col />
            <col style={{ width: 100 }} />
          </colgroup>
          <thead>
            <tr>
              <th style={{ color: 'var(--muted)', fontSize: 10 }}>#</th>
              <th>ISP / Telecom Operator</th>
              <th>Type</th>
              <th>IPs &amp; Share</th>
              <th style={{ textAlign: 'right' }}>Letter</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((r, idx) => {
              const cat = ispCategory(r.isp)
              const pct = totalUniqueIps > 0 ? (r.count / totalUniqueIps) * 100 : 0
              const barPct = maxRow > 0 ? (r.count / maxRow) * 100 : 0
              return (
                <tr key={r.isp}>
                  <td style={{ color: 'var(--muted)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace', textAlign: 'center' }}>{idx + 1}</td>
                  <td style={{ fontWeight: 500, maxWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.isp}>{r.isp}</td>
                  <td>
                    <span style={{ display: 'inline-block', padding: '2px 7px', borderRadius: 4, fontSize: 9, fontWeight: 700, letterSpacing: '0.4px', color: cat.color, background: cat.bg, border: `1px solid ${cat.border}`, whiteSpace: 'nowrap' }}>
                      {cat.label}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--text-bright)', flexShrink: 0, minWidth: 28, textAlign: 'right' }}>{r.count}</span>
                      <div style={{ flex: 1, height: 5, background: '#f3f4f6', borderRadius: 3, overflow: 'hidden', minWidth: 40 }}>
                        <div style={{ height: '100%', width: `${barPct}%`, background: cat.color, borderRadius: 3, transition: 'width 0.4s ease', opacity: 0.75 }} />
                      </div>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--muted)', flexShrink: 0, minWidth: 32, textAlign: 'right' }}>{pct.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn" style={{ fontSize: 10, padding: '3px 9px' }}
                      onClick={() => onDownloadLetter(r.isp)} disabled={letterIspLoading === r.isp || !token}>
                      {letterIspLoading === r.isp ? <Spinner /> : 'DOCX'}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {rows.length > 12 && (
        <button type="button" className="btn btn-ghost" onClick={() => setExpanded(x => !x)}
          style={{ marginTop: 10, width: '100%', fontSize: 11, padding: '6px' }}>
          {expanded ? `Show less ↑` : `Show all ${rows.length} ISPs ↓`}
        </button>
      )}
    </div>
  )
}

function StatPill({ label, value, color = 'var(--text-bright)', bg = '#f3f4f6', border = 'var(--border)' }: {
  label: string; value: number; color?: string; bg?: string; border?: string
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 6, background: bg, border: `1px solid ${border}` }}>
      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, color }}>{value.toLocaleString()}</span>
      <span style={{ fontSize: 11, color: 'var(--muted)' }}>{label}</span>
    </div>
  )
}

function Spinner({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 0.8s linear infinite', flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="2" strokeDasharray="32" strokeDashoffset="10" />
    </svg>
  )
}

function LField({ label, value, onChange, placeholder = '', mono = false }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; mono?: boolean }) {
  return (
    <div>
      <label>{label}</label>
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={mono ? { fontFamily: 'JetBrains Mono, monospace' } : undefined} />
    </div>
  )
}
