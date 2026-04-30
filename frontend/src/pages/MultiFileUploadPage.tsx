import { FormEvent, useRef, useState } from 'react'
import { apiRequest } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Link } from 'react-router-dom'

type ProcessResult = {
  fir_number?: string
  total_files?: number
  processed_files?: number
  total_ips?: number
  run_dir?: string
  message?: string
  errors?: string[]
}

export default function MultiFileUploadPage() {
  const { token } = useAuth()
  const [files, setFiles] = useState<FileList | null>(null)
  const [firNumber, setFirNumber] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProcessResult | null>(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!files || files.length === 0 || !firNumber.trim()) return

    setLoading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    Array.from(files).forEach(f => formData.append('files', f))
    formData.append('fir_number', firNumber.trim())

    const response = await apiRequest<ProcessResult>(
      '/api/multi-file/upload-html-files',
      { method: 'POST', body: formData },
      token
    )

    setLoading(false)
    if (!response.success) {
      setError(response.error || 'Upload failed')
      return
    }
    setResult(response.data ?? null)
    if (response.data?.run_dir) {
      localStorage.setItem('latest_run_dir', response.data.run_dir)
    }
  }

  const fileCount = files ? files.length : 0
  const fileNames = files ? Array.from(files).map(f => f.name) : []

  return (
    <section>
      {/* Page Header */}
      <div style={{ marginBottom: 22 }}>
        <h1>Multi-File Upload</h1>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>
          Upload multiple IPDR HTML files for a single FIR case in one batch
        </p>
      </div>

      {/* Flow Steps */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 0,
        marginBottom: 24, overflowX: 'auto', paddingBottom: 4,
      }}>
        {[
          { n: '01', label: 'Select Files',    active: true },
          { n: '02', label: 'Process Batch',   active: !!result },
          { n: '03', label: 'IP Enrichment',   active: false },
          { n: '04', label: 'IP Lookup',       active: false },
          { n: '05', label: 'ISP Letters',     active: false },
        ].map((step, i) => (
          <div key={step.n} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 14px', borderRadius: 8,
              border: `1px solid ${step.active ? 'rgba(0,229,255,0.3)' : 'var(--border)'}`,
              background: step.active ? 'rgba(0,229,255,0.06)' : 'transparent',
            }}>
              <span style={{
                fontFamily: 'Orbitron, monospace', fontSize: 10, fontWeight: 900,
                color: step.active ? 'var(--cyan)' : 'var(--muted)',
              }}>{step.n}</span>
              <span style={{ fontSize: 12, color: step.active ? 'var(--text-bright)' : 'var(--muted)', whiteSpace: 'nowrap' }}>
                {step.label}
              </span>
            </div>
            {i < 4 && (
              <div style={{ width: 24, height: 1, background: 'var(--border)', flexShrink: 0 }} />
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, alignItems: 'start' }}>
        {/* Upload Form */}
        <div className="card" style={{ marginBottom: 0 }}>
          <h2 style={{ marginBottom: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              width: 24, height: 24, borderRadius: 6, background: 'rgba(0,229,255,0.1)',
              border: '1px solid rgba(0,229,255,0.2)', display: 'inline-flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 11, color: 'var(--cyan)', fontWeight: 900,
            }}>1</span>
            Upload IPDR Files
          </h2>

          <form onSubmit={onSubmit} style={{ display: 'grid', gap: 16 }}>
            {/* FIR Number */}
            <div>
              <label>FIR Number *</label>
              <input
                value={firNumber}
                onChange={e => setFirNumber(e.target.value)}
                placeholder="e.g. 201/25, 275-25"
                required
                style={{ fontFamily: 'JetBrains Mono, monospace' }}
              />
              <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                All uploaded files will be linked to this FIR
              </div>
            </div>

            {/* File Drop Zone */}
            <div>
              <label>IPDR HTML / ZIP Files *</label>
              <div
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${fileCount > 0 ? 'rgba(0,229,255,0.4)' : 'var(--border)'}`,
                  borderRadius: 10,
                  padding: '28px 20px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: fileCount > 0 ? 'rgba(0,229,255,0.04)' : 'rgba(0,8,22,0.5)',
                  transition: 'all 200ms',
                }}
              >
                {fileCount === 0 ? (
                  <>
                    <div style={{ marginBottom: 8 }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--muted)', margin: '0 auto' }}>
                        <path d="M12 3v10m0-10 4 4m-4-4-4 4M4 17v2h16v-2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                      </svg>
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text)', marginBottom: 4 }}>
                      Click to select files
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                      Accepts .html, .htm, .zip — multiple files supported
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ color: 'var(--cyan)', fontWeight: 700, marginBottom: 8, fontSize: 14 }}>
                      {fileCount} file{fileCount !== 1 ? 's' : ''} selected
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                      {fileNames.slice(0, 6).map(name => (
                        <span key={name} style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 4,
                          background: 'rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.2)',
                          color: 'var(--text)', fontFamily: 'JetBrains Mono, monospace',
                          maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }}>{name}</span>
                      ))}
                      {fileNames.length > 6 && (
                        <span style={{ fontSize: 11, color: 'var(--muted)' }}>+{fileNames.length - 6} more</span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>Click to change selection</div>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".html,.htm,.zip"
                onChange={e => setFiles(e.target.files)}
                style={{ display: 'none' }}
              />
            </div>

            {error && <div className="alert error">{error}</div>}

            <button
              className="btn btn-primary"
              disabled={loading || fileCount === 0 || !firNumber.trim()}
              style={{ padding: '11px', fontSize: 13, letterSpacing: '0.5px' }}
            >
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeDashoffset="10" />
                  </svg>
                  Processing {fileCount} file{fileCount !== 1 ? 's' : ''}...
                </span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M12 3v10m0-10 4 4m-4-4-4 4M4 17v2h16v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  Upload & Process Files
                </span>
              )}
            </button>
          </form>
        </div>

        {/* Info Panel */}
        <div style={{ display: 'grid', gap: 12 }}>
          <div className="card" style={{ marginBottom: 0 }}>
            <h3 style={{ marginBottom: 12, color: 'var(--cyan)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              How it works
            </h3>
            <div style={{ display: 'grid', gap: 10 }}>
              {[
                { step: '01', text: 'Select all IPDR HTML files from the same case', color: 'var(--cyan)' },
                { step: '02', text: 'Enter the FIR number to link all files', color: 'var(--cyan)' },
                { step: '03', text: 'Files are parsed and IPs extracted in batch', color: 'var(--purple)' },
                { step: '04', text: 'Proceed to IP Enrichment on Upload page', color: 'var(--green)' },
              ].map(item => (
                <div key={item.step} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{
                    fontFamily: 'Orbitron, monospace', fontSize: 9, fontWeight: 900,
                    color: item.color, flexShrink: 0, paddingTop: 2,
                  }}>{item.step}</span>
                  <span style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ marginBottom: 0, padding: '12px 14px' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 8 }}>
              Supported Formats
            </div>
            {['.html / .htm', '.zip (containing HTML files)'].map(fmt => (
              <div key={fmt} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ color: 'var(--green)', fontSize: 12 }}>✓</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text)' }}>{fmt}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="card" style={{ marginTop: 16, borderColor: 'rgba(0,255,136,0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'rgba(0,255,136,0.1)', border: '1px solid rgba(0,255,136,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17l-5-5" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--green)', fontSize: 14 }}>Processing Complete</div>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>{result.message || 'Files processed successfully'}</div>
            </div>
          </div>

          <div className="mini-grid" style={{ marginBottom: 16 }}>
            {[
              { label: 'FIR Number',       value: result.fir_number || firNumber, mono: true },
              { label: 'Files Processed',  value: `${result.processed_files ?? result.total_files ?? fileCount}` },
              { label: 'IPs Extracted',    value: result.total_ips?.toString() ?? '—' },
            ].map(item => (
              <div key={item.label} className="metric-box">
                <strong style={{ fontFamily: item.mono ? 'JetBrains Mono, monospace' : undefined, fontSize: 16 }}>
                  {item.value}
                </strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {result.errors && result.errors.length > 0 && (
            <div className="alert warning" style={{ marginBottom: 12 }}>
              {result.errors.length} file(s) had warnings during processing
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Link to="/upload" className="btn btn-primary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              Go to IP Enrichment
            </Link>
            <Link to="/ip-lookup" className="btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M10 18a8 8 0 1 1 5.29-14.01A8 8 0 0 1 10 18Zm8 2-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              IP Lookup
            </Link>
            <button className="btn btn-ghost" onClick={() => { setResult(null); setFiles(null); setFirNumber('') }}>
              Upload More
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </section>
  )
}
