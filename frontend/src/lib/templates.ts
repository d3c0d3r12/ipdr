// frontend/src/lib/templates.ts
import { apiRequest } from './api'

export type Align = 'left' | 'center' | 'right'
export type Block =
  | { id: string; type: 'text'; content: string; align: Align; bold: boolean; italic: boolean; font?: string; size?: number }
  | { id: string; type: 'list'; style: 'numbered' | 'bullet'; items: string[]; font?: string; size?: number }
  | { id: string; type: 'ip_table' }
  | { id: string; type: 'spacer'; lines: number }

export type LetterTemplate = {
  id: string
  name: string
  owner_id: string | null
  scope: 'system' | 'user' | 'shared'
  kind: 'blocks' | 'docx'
  page: { margins_inches: Record<string, number>; default_font: string; default_size: number }
  blocks: Block[]
  docx_b64?: string
}

export const PLACEHOLDERS = [
  'fir_number', 'fir_date', 'letter_date', 'police_station', 'sections',
  'complainant', 'isp_name', 'officer_name', 'officer_designation',
  'officer_location', 'officer_contact', 'subject', 'email_reference',
] as const

export async function listTemplates(token: string) {
  return apiRequest<{ templates: LetterTemplate[] }>('/api/letter-templates/', { method: 'GET' }, token)
}
export async function getTemplate(token: string, id: string) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}`, { method: 'GET' }, token)
}
export async function createTemplate(token: string, body: Pick<LetterTemplate, 'name' | 'page' | 'blocks'>) {
  return apiRequest<{ template: LetterTemplate }>('/api/letter-templates/', { method: 'POST', body: JSON.stringify(body) }, token)
}
export async function updateTemplate(token: string, id: string, body: Pick<LetterTemplate, 'name' | 'page' | 'blocks'>) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}`, { method: 'PUT', body: JSON.stringify(body) }, token)
}
export async function deleteTemplate(token: string, id: string) {
  return apiRequest(`/api/letter-templates/${id}`, { method: 'DELETE' }, token)
}
export async function shareTemplate(token: string, id: string) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}/share`, { method: 'POST' }, token)
}

export async function uploadDocxTemplate(token: string, file: File, name: string, mode: 'raw' | 'convert') {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('name', name)
  fd.append('mode', mode)
  return apiRequest<{ template: LetterTemplate }>('/api/letter-templates/upload-docx', { method: 'POST', body: fd }, token)
}

export function newBlock(type: Block['type']): Block {
  const id = Math.random().toString(36).slice(2, 10)
  if (type === 'text') return { id, type, content: '', align: 'left', bold: false, italic: false }
  if (type === 'list') return { id, type, style: 'numbered', items: [''] }
  if (type === 'spacer') return { id, type, lines: 1 }
  return { id, type: 'ip_table' }
}
