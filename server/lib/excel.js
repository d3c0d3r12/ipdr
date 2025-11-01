import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import xlsx from 'xlsx';

export async function buildExcel({ firNo, htmlRows, infobyipCsvPath, outputPath }) {
	const csvText = fs.readFileSync(infobyipCsvPath, 'utf8');
	const records = parse(csvText, { columns: true, skip_empty_lines: true });
	// Build lookup by IP
	const byIp = new Map();
	for (const rec of records) {
		const ip = (rec.IP || rec.Ip || rec.ip || '').trim();
		if (ip) byIp.set(ip, rec);
	}
	// Merge rows
	const out = [];
	for (const row of htmlRows) {
		const rec = byIp.get(row.ip) || {};
		out.push({
			'FIR No.': firNo,
			'Timestamp': row.timestamp,
			'IP Address': row.ip,
			'Country': rec.Country || rec.country || rec["Country Name"] || '',
			'Region': rec.Region || rec.region || rec.State || '',
			'City': rec.City || rec.city || '',
			'ISP': rec.ISP || rec.isp || rec["Organization"] || '',
			'Timezone': rec.Timezone || rec.timezone || rec["Time Zone"] || ''
		});
	}
	const ws = xlsx.utils.json_to_sheet(out);
	const wb = xlsx.utils.book_new();
	xlsx.utils.book_append_sheet(wb, ws, 'Master');
	xlsx.writeFile(wb, outputPath);
	return outputPath;
}


