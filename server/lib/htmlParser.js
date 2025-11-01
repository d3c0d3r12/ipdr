import { load as loadHtml } from 'cheerio';

export function parseHtmlForTimestampIp(html) {
	const $ = loadHtml(html, { xmlMode: false, decodeEntities: true });
	const rows = [];

	// 1) Locate the specific "IP ACTIVITY" table
	let table;
	$('h3').each((_, el) => {
		const text = $(el).text().trim().toLowerCase();
		if (text === 'ip activity') {
			table = $(el).nextAll('table').first();
		}
	});
	if (!table || !table.length) {
		// Fallback: pick the first table that has headers including Timestamp and IP Address
		$('table').each((_, t) => {
			if (table) return;
			const headers = getHeaders($, t);
			if (headers.timestampIdx !== -1 && headers.ipIdx !== -1) table = $(t);
		});
	}
	if (!table || !table.length) return rows; // none found

	// 2) Resolve header indices for accuracy
	const { timestampIdx, ipIdx } = getHeaders($, table);
	const tsIndex = timestampIdx !== -1 ? timestampIdx : 0;
	const ipIndex = ipIdx !== -1 ? ipIdx : 1;

	// 3) Extract body rows using resolved indices
	table.find('tr').each((i, tr) => {
		if (i === 0) return; // header row
		const tds = $(tr).find('td');
		if (!tds.length) return;
		const rawTs = (tds[tsIndex] ? $(tds[tsIndex]).text() : '').trim();
		const rawIp = (tds[ipIndex] ? $(tds[ipIndex]).text() : '').trim();
		if (!rawTs || !rawIp) return;
		if (!isLikelyIp(rawIp)) return;
		if (!isLikelyTimestamp(rawTs)) return;
		rows.push({ timestamp: normalizeTimestamp(rawTs), ip: normalizeIp(rawIp) });
	});

	return rows;
}

function getHeaders($, tableEl) {
	const firstRow = $(tableEl).find('tr').first();
	const cells = firstRow.find('th,td');
	let timestampIdx = -1;
	let ipIdx = -1;
	cells.each((idx, cell) => {
		const label = $(cell).text().trim().toLowerCase();
		if (timestampIdx === -1 && (label === 'timestamp' || label.includes('time'))) timestampIdx = idx;
		if (ipIdx === -1 && (label === 'ip address' || label === 'ip' || label.includes('ip'))) ipIdx = idx;
	});
	return { timestampIdx, ipIdx };
}

function isLikelyTimestamp(s) {
	// ISO-like with Z or offset; sample is "YYYY-MM-DD HH:mm:ss Z"
	return /\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2} ?(?:Z|[+-]\d{2}:?\d{2}|$)/i.test(s);
}

function isLikelyIp(s) {
	// IPv4
	const ipv4 = /^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$/;
	// IPv6 (lenient, allows ::, hex blocks, optional IPv4 tail already covered above)
	const ipv6 = /^([0-9a-f]{1,4}:){1,7}[0-9a-f]{0,4}(::)?[0-9a-f:]*$/i;
	return ipv4.test(s) || ipv6.test(s);
}

function normalizeTimestamp(s) {
	return s.replace(/\s+Z$/i, ' Z').trim();
}

function normalizeIp(s) {
	return s.trim();
}
