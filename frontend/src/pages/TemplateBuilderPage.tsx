import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../lib/auth'
import {
  Block, LetterTemplate, PLACEHOLDERS, newBlock,
  listTemplates, createTemplate, updateTemplate, deleteTemplate, shareTemplate, uploadDocxTemplate,
} from '../lib/templates'

const SAMPLE_ROW = { type: 'IPV4', ip: '1.2.3.4', fromDate: '28-Jan-2025', fromTime: '14:30:25', toDate: '28-Jan-2025', toTime: '15:30:25' }

function PreviewTable({ isp }: { isp: string }) {
  const airtel = isp.toLowerCase().includes('airtel')
  if (airtel) {
    return (
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 11 }}>
        <thead><tr>{['Type', 'Search Value', 'From Date (DD-MMM-YYYY HH24:MI:SS)', 'To Date (DD-MMM-YYYY HH24:MI:SS)'].map(h =>
          <th key={h} style={{ border: '1px solid #888', padding: 4 }}>{h}</th>)}</tr></thead>
        <tbody><tr>{[SAMPLE_ROW.type, SAMPLE_ROW.ip, `${SAMPLE_ROW.fromDate} ${SAMPLE_ROW.fromTime}`, `${SAMPLE_ROW.toDate} ${SAMPLE_ROW.toTime}`].map((c, i) =>
          <td key={i} style={{ border: '1px solid #888', padding: 4 }}>{c}</td>)}</tr></tbody>
      </table>
    )
  }
  const jio = isp.toLowerCase().includes('jio') || isp.toLowerCase().includes('reliance')
  const dateHdr = jio ? 'YYYYMMDD' : 'DD:MM:YYYY'
  const timeHdr = jio ? 'HHMMSS (IST)' : 'HH:MM:SS (IST)'
  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 11 }}>
      <thead><tr>{['Type', 'Search Value', `From Date ${dateHdr}`, `From Time ${timeHdr}`, `To Date ${dateHdr}`, `To Time ${timeHdr}`].map(h =>
        <th key={h} style={{ border: '1px solid #888', padding: 4 }}>{h}</th>)}</tr></thead>
      <tbody><tr>{[SAMPLE_ROW.type, SAMPLE_ROW.ip, jio ? '20250128' : '28:01:2025', jio ? '143025' : '14:30:25', jio ? '20250128' : '28:01:2025', jio ? '153025' : '15:30:25'].map((c, i) =>
        <td key={i} style={{ border: '1px solid #888', padding: 4 }}>{c}</td>)}</tr></tbody>
    </table>
  )
}

function BlockPreview({ block, isp }: { block: Block; isp: string }) {
  if (block.type === 'text') {
    return <p style={{ textAlign: block.align, fontWeight: block.bold ? 700 : 400, fontStyle: block.italic ? 'italic' : 'normal', fontFamily: block.font || 'Calibri', fontSize: (block.size || 10) + 1, whiteSpace: 'pre-wrap', margin: '2px 0' }}>{block.content || ' '}</p>
  }
  if (block.type === 'list') {
    const Tag = block.style === 'numbered' ? 'ol' : 'ul'
    return <Tag style={{ fontSize: (block.size || 10) + 1, margin: '4px 0 4px 20px' }}>{block.items.map((it, i) => <li key={i}>{it}</li>)}</Tag>
  }
  if (block.type === 'ip_table') return <div style={{ margin: '6px 0' }}><PreviewTable isp={isp} /></div>
  return <div style={{ height: (block.lines || 1) * 14 }} />
}

export default function TemplateBuilderPage() {
  const { token, user } = useAuth()
  const [templates, setTemplates] = useState<LetterTemplate[]>([])
  const [selId, setSelId] = useState<string>('')
  const [draft, setDraft] = useState<LetterTemplate | null>(null)
  const [selBlock, setSelBlock] = useState<string>('')
  const [previewIsp, setPreviewIsp] = useState('Airtel')
  const [msg, setMsg] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [upFile, setUpFile] = useState<File | null>(null)
  const [upName, setUpName] = useState('')
  const [upMode, setUpMode] = useState<'raw' | 'convert'>('raw')

  useEffect(() => {
    listTemplates(token).then(r => {
      const list = r.data?.templates ?? []
      setTemplates(list)
      const def = list.find(t => t.name === 'IFSO Dwarka Default') || list[0]
      if (def) { setSelId(def.id); setDraft(structuredClone(def)) }
    })
  }, [token])

  const onSelect = (id: string) => {
    const t = templates.find(x => x.id === id)
    if (t) { setSelId(id); setDraft(structuredClone(t)); setSelBlock('') }
  }

  const isOwn = draft?.scope === 'user' && draft?.owner_id === String(user?.id)
  const block = useMemo(() => draft?.blocks.find(b => b.id === selBlock), [draft, selBlock])

  const mutate = (fn: (d: LetterTemplate) => void) => setDraft(d => { if (!d) return d; const c = structuredClone(d); fn(c); return c })
  const updateBlock = (patch: Partial<Block>) => mutate(d => {
    const b = d.blocks.find(x => x.id === selBlock); if (b) Object.assign(b, patch)
  })
  const move = (i: number, dir: -1 | 1) => mutate(d => {
    const j = i + dir; if (j < 0 || j >= d.blocks.length) return
    ;[d.blocks[i], d.blocks[j]] = [d.blocks[j], d.blocks[i]]
  })
  const addBlock = (type: Block['type']) => {
    if (type === 'ip_table' && draft?.blocks.some(b => b.type === 'ip_table')) { setMsg('Only one IP table allowed'); return }
    mutate(d => { d.blocks.push(newBlock(type)) })
  }
  const removeBlock = (id: string) => mutate(d => { d.blocks = d.blocks.filter(b => b.id !== id) })

  const body = (d: LetterTemplate) => ({ name: d.name, page: d.page, blocks: d.blocks })
  const save = async () => {
    if (!draft || !isOwn) return
    const r = await updateTemplate(token, draft.id, body(draft))
    setMsg(r.success ? 'Saved' : (r.error || 'Save failed'))
    if (r.success) { const list = (await listTemplates(token)).data?.templates ?? []; setTemplates(list) }
  }
  const saveAs = async () => {
    if (!draft) return
    const name = window.prompt('New template name', draft.name + ' (copy)')
    if (!name) return
    const r = await createTemplate(token, { ...body(draft), name })
    if (r.success && r.data) { const list = (await listTemplates(token)).data?.templates ?? []; setTemplates(list); setSelId(r.data.template.id); setDraft(structuredClone(r.data.template)) }
    setMsg(r.success ? 'Created' : (r.error || 'Failed'))
  }
  const del = async () => {
    if (!draft || !isOwn || !window.confirm('Delete this template?')) return
    await deleteTemplate(token, draft.id)
    const list = (await listTemplates(token)).data?.templates ?? []; setTemplates(list)
    const def = list.find(t => t.name === 'IFSO Dwarka Default') || list[0]
    if (def) { setSelId(def.id); setDraft(structuredClone(def)) }
  }
  const share = async () => { if (draft) { await shareTemplate(token, draft.id); setMsg('Shared with department') } }

  const doUpload = async () => {
    if (!upFile) { setMsg('Choose a .docx file first'); return }
    const name = upName.trim() || upFile.name.replace(/\.docx$/i, '')
    const r = await uploadDocxTemplate(token, upFile, name, upMode)
    if (r.success && r.data) {
      const list = (await listTemplates(token)).data?.templates ?? []
      setTemplates(list); setSelId(r.data.template.id); setDraft(structuredClone(r.data.template)); setSelBlock('')
      setShowUpload(false); setUpFile(null); setUpName('')
      setMsg(upMode === 'raw' ? 'Word file uploaded as template' : 'Word file converted to editable blocks')
    } else {
      setMsg(r.error || 'Upload failed')
    }
  }

  const isDocx = draft?.kind === 'docx'

  if (!draft) return <section><p className="muted">Loading templates…</p></section>

  return (
    <section>
      <div style={{ marginBottom: 16 }}>
        <h1>ISP Letter Template Builder</h1>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>Design your own letter layout. The IP table always auto-formats per ISP.</p>
      </div>

      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
        <select value={selId} onChange={e => onSelect(e.target.value)} style={{ minWidth: 220 }}>
          {templates.map(t => <option key={t.id} value={t.id}>{t.name}{t.scope === 'system' ? ' (default)' : t.scope === 'shared' ? ' (shared)' : ''}</option>)}
        </select>
        <button className="btn btn-primary" disabled={!isOwn} onClick={save}>Save</button>
        <button className="btn" onClick={saveAs}>Save As…</button>
        <button className="btn" onClick={saveAs}>Duplicate</button>
        <button className="btn btn-ghost" disabled={!isOwn} onClick={del}>Delete</button>
        {user?.role === 'admin' && <button className="btn btn-ghost" onClick={share}>Share</button>}
        <button className="btn" onClick={() => setShowUpload(v => !v)}>⬆ Upload .docx</button>
        {msg && <span className="muted" style={{ fontSize: 12 }}>{msg}</span>}
      </div>

      {showUpload && (
        <div className="card" style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: 12 }}>Word file (.docx)</label>
              <input type="file" accept=".docx" onChange={e => setUpFile(e.target.files?.[0] ?? null)} />
            </div>
            <div>
              <label style={{ fontSize: 12 }}>Template name</label>
              <input value={upName} onChange={e => setUpName(e.target.value)} placeholder="e.g. My Station Letter" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>
                <input type="radio" checked={upMode === 'raw'} onChange={() => setUpMode('raw')} /> Use as-is (keep exact Word formatting)
              </label>
              <label style={{ fontSize: 12 }}>
                <input type="radio" checked={upMode === 'convert'} onChange={() => setUpMode('convert')} /> Convert to editable blocks
              </label>
            </div>
            <button className="btn btn-primary" onClick={doUpload}>Upload</button>
          </div>
          <p className="muted" style={{ fontSize: 11, marginTop: 10, marginBottom: 0 }}>
            For "Use as-is", put <code>{'{ip_table}'}</code> where the IP table should appear, and tokens like <code>{'{fir_number}'}</code>, <code>{'{officer_name}'}</code> anywhere in the document.
          </p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 16, alignItems: 'start' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <input value={draft.name} onChange={e => mutate(d => { d.name = e.target.value })} disabled={!isOwn && draft.scope !== 'user'} style={{ marginBottom: 10, width: '100%' }} />
          {isDocx && (
            <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
              <p style={{ marginTop: 0 }}>This template is an uploaded Word file, rendered <strong>as-is</strong>. Edit it in Word and re-upload to change the layout.</p>
              <p>These tokens are filled when letters are generated:</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {[...PLACEHOLDERS, 'ip_table'].map(p => (
                  <code key={p} style={{ fontSize: 11, background: 'rgba(0,229,255,0.08)', padding: '2px 6px', borderRadius: 4 }}>{`{${p}}`}</code>
                ))}
              </div>
            </div>
          )}
          {!isDocx && (<>
          <div style={{ display: 'grid', gap: 4, marginBottom: 10 }}>
            {draft.blocks.map((b, i) => (
              <div key={b.id} onClick={() => setSelBlock(b.id)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px', borderRadius: 6, cursor: 'pointer', border: '1px solid var(--border)', background: selBlock === b.id ? 'rgba(0,229,255,0.08)' : 'transparent' }}>
                <span style={{ flex: 1, fontSize: 12 }}>{b.type === 'text' ? `Text · ${(b as any).content.slice(0, 20) || 'empty'}` : b.type === 'list' ? `List (${(b as any).items.length})` : b.type === 'ip_table' ? 'IP Table (auto)' : `Spacer (${(b as any).lines})`}</span>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); move(i, -1) }}>▲</button>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); move(i, 1) }}>▼</button>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); removeBlock(b.id) }}>✕</button>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {(['text', 'list', 'ip_table', 'spacer'] as const).map(t => (
              <button key={t} className="btn" style={{ fontSize: 11 }} onClick={() => addBlock(t)}>+ {t}</button>
            ))}
          </div>

          {block && (
            <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
              {block.type === 'text' && (
                <>
                  <textarea value={block.content} onChange={e => updateBlock({ content: e.target.value } as any)} rows={4} style={{ width: '100%' }} />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    {(['left', 'center', 'right'] as const).map(a => (
                      <label key={a} style={{ fontSize: 12 }}><input type="radio" checked={block.align === a} onChange={() => updateBlock({ align: a } as any)} /> {a}</label>
                    ))}
                    <label style={{ fontSize: 12 }}><input type="checkbox" checked={block.bold} onChange={e => updateBlock({ bold: e.target.checked } as any)} /> Bold</label>
                    <label style={{ fontSize: 12 }}><input type="checkbox" checked={block.italic} onChange={e => updateBlock({ italic: e.target.checked } as any)} /> Italic</label>
                    <input placeholder="font" value={block.font || ''} onChange={e => updateBlock({ font: e.target.value } as any)} style={{ width: 90 }} />
                    <input type="number" placeholder="size" value={block.size || ''} onChange={e => updateBlock({ size: Number(e.target.value) || undefined } as any)} style={{ width: 64 }} />
                    <select onChange={e => { if (e.target.value) { updateBlock({ content: block.content + `{${e.target.value}}` } as any); e.target.value = '' } }}>
                      <option value="">Insert placeholder…</option>
                      {PLACEHOLDERS.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </>
              )}
              {block.type === 'list' && (
                <>
                  <div style={{ marginBottom: 6 }}>
                    {(['numbered', 'bullet'] as const).map(s => <label key={s} style={{ fontSize: 12, marginRight: 10 }}><input type="radio" checked={block.style === s} onChange={() => updateBlock({ style: s } as any)} /> {s}</label>)}
                  </div>
                  {block.items.map((it, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
                      <input value={it} onChange={e => updateBlock({ items: block.items.map((x, k) => k === idx ? e.target.value : x) } as any)} style={{ flex: 1 }} />
                      <button className="btn btn-ghost" onClick={() => updateBlock({ items: block.items.filter((_, k) => k !== idx) } as any)}>✕</button>
                    </div>
                  ))}
                  <button className="btn" style={{ fontSize: 11 }} onClick={() => updateBlock({ items: [...block.items, ''] } as any)}>+ item</button>
                </>
              )}
              {block.type === 'spacer' && (
                <label style={{ fontSize: 12 }}>Lines <input type="number" value={block.lines} onChange={e => updateBlock({ lines: Number(e.target.value) || 1 } as any)} style={{ width: 64 }} /></label>
              )}
              {block.type === 'ip_table' && <p className="muted" style={{ fontSize: 12 }}>Columns auto-format per ISP (Airtel 4-col, Jio/Vi 6-col). Not editable.</p>}
            </div>
          )}
          </>)}
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong style={{ fontSize: 13 }}>Live Preview</strong>
            <label style={{ fontSize: 12 }}>IP table as: <select value={previewIsp} onChange={e => setPreviewIsp(e.target.value)}><option>Airtel</option><option>Jio</option><option>Vodafone Idea</option></select></label>
          </div>
          <div style={{ background: '#fff', color: '#000', padding: '32px 40px', minHeight: 600, boxShadow: '0 0 0 1px var(--border)' }}>
            {isDocx
              ? <p style={{ color: '#555', fontSize: 13 }}>No preview for uploaded Word files — the .docx is used exactly as provided. Generate a letter to see the final result.</p>
              : draft.blocks.map(b => <BlockPreview key={b.id} block={b} isp={previewIsp} />)}
          </div>
          <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>Preview is an approximation. The generated .docx is the final document.</p>
        </div>
      </div>
    </section>
  )
}
