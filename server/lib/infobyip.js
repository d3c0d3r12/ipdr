import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';

const INFOBYIP_URL = 'https://www.infobyip.com/ipbulklookup.php';

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

export async function runInfoByIpBulkLookup(ipListPath, workDir) {
	const csvOut = path.join(workDir, 'infobyip.csv');
	const ipText = fs.readFileSync(ipListPath, 'utf8');
	const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
	try {
		const page = await browser.newPage();
		await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
		await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
		page.setDefaultNavigationTimeout(180000);
		page.setDefaultTimeout(180000);

		for (let attempt = 1; attempt <= 3; attempt++) {
			try {
				if (fs.existsSync(csvOut)) fs.unlinkSync(csvOut);

				await page.goto(INFOBYIP_URL, { waitUntil: 'domcontentloaded' });
				await page.waitForSelector('textarea[name="list"]', { visible: true });

				// Fill textarea via DOM to avoid throttled typing
				await page.evaluate((text) => {
					const ta = document.querySelector('textarea[name="list"]');
					if (ta) { ta.value = text; }
				}, ipText);

				// Submit
				await Promise.all([
					page.click('input[type="submit"][name="submit"]'),
					page.waitForNavigation({ waitUntil: 'networkidle2' })
				]);

				// Wait for either CSV link or results table
				await page.waitForFunction(() => {
					const link = Array.from(document.querySelectorAll('a')).find(a => /csv/i.test(a.textContent || '') || /csv/i.test(a.getAttribute('href') || ''));
					const table = document.querySelector('table');
					return !!(link || table);
				}, { polling: 500, timeout: 120000 });

				// Try direct CSV link first
				const csvHref = await page.evaluate(() => {
					const a = Array.from(document.querySelectorAll('a')).find(a => /csv/i.test(a.textContent || '') || /csv/i.test(a.getAttribute('href') || ''));
					return a ? a.getAttribute('href') : '';
				});

				if (csvHref) {
					const csvUrl = new URL(csvHref, INFOBYIP_URL).toString();
					const resp = await page.goto(csvUrl, { waitUntil: 'networkidle2' });
					if (resp && (resp.headers()['content-type'] || '').includes('text/csv')) {
						const buffer = await resp.buffer();
						fs.writeFileSync(csvOut, buffer);
					}
				}

				// Fallback: click CSV link and capture response
				if (!fs.existsSync(csvOut)) {
					const linkHandles = await page.$x("//a[contains(., 'CSV') or contains(@href, 'csv')]");
					if (linkHandles.length) {
						const [response] = await Promise.all([
							page.waitForResponse(res => (res.headers()['content-type'] || '').includes('text/csv'), { timeout: 120000 }),
							linkHandles[0].click()
						]);
						const buffer = await response.buffer();
						fs.writeFileSync(csvOut, buffer);
					}
				}

				// Last resort: scrape the results table and emit CSV
				if (!fs.existsSync(csvOut)) {
					const tableCsv = await page.evaluate(() => {
						const table = document.querySelector('table');
						if (!table) return '';
						const rows = Array.from(table.querySelectorAll('tr')).map(tr => Array.from(tr.querySelectorAll('th,td')).map(td => td.innerText.replace(/\s+/g, ' ').trim()));
						return rows.map(r => r.map(field => '"' + field.replaceAll('"', '""') + '"').join(',')).join('\n');
					});
					if (tableCsv) fs.writeFileSync(csvOut, tableCsv, 'utf8');
				}

				if (!fs.existsSync(csvOut)) throw new Error('CSV not captured');
				return csvOut;
			} catch (err) {
				if (attempt === 3) throw err;
				await delay(2000 * attempt);
			}
		}
		throw new Error('Unexpected: retries exhausted');
	} finally {
		await browser.close();
	}
}

export async function runInfoByIpBulkLookupBatches(allIps, workDir, batchSize = 100) {
	const mergedCsvPath = path.join(workDir, 'infobyip_merged.csv');
	let header = '';
	const out = [];
	for (let i = 0; i < allIps.length; i += batchSize) {
		const chunk = allIps.slice(i, i + batchSize);
		const listPath = path.join(workDir, `ips_${i}.txt`);
		fs.writeFileSync(listPath, chunk.join('\n'));
		try {
			const csvPath = await runInfoByIpBulkLookup(listPath, workDir);
			const batchCsvPath = path.join(workDir, `infobyip_${i}.csv`);
			// Save a copy per batch for visibility
			fs.copyFileSync(csvPath, batchCsvPath);
			const csvText = fs.readFileSync(csvPath, 'utf8');
			const lines = csvText.split(/\r?\n/).filter(Boolean);
			if (!lines.length) continue;
			if (!header) {
				header = lines[0];
				out.push(header);
			}
			for (let j = 1; j < lines.length; j++) out.push(lines[j]);
			await delay(1000);
		} catch (e) {
			fs.appendFileSync(path.join(workDir, 'log.txt'), `[batch ${i}] error: ${e?.message || e}\n`);
		}
	}
	if (out.length) fs.writeFileSync(mergedCsvPath, out.join('\n'), 'utf8');
	return mergedCsvPath;
}
