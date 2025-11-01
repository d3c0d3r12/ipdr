import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { parseHtmlForTimestampIp } from './lib/htmlParser.js';
import { runInfoByIpBulkLookupBatches } from './lib/infobyip.js';
import { buildExcel } from './lib/excel.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });
const runsBaseDir = process.env.RUNS_DIR ? path.resolve(process.env.RUNS_DIR) : path.join(__dirname, '../runs');
if (!fs.existsSync(runsBaseDir)) fs.mkdirSync(runsBaseDir, { recursive: true });

const app = express();
const upload = multer({ dest: uploadsDir });

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.get('/health', (_req, res) => res.json({ ok: true }));

app.get('/', (req, res) => {
	res.type('html').send(`<!doctype html>
<html>
<head><meta charset="utf-8"><title>Delhi Police | IP Trace</title>
<style>
:root{--bg:#0b1220;--card:#111a2d;--muted:#9fb0c6;--text:#e6e9ef;--border:#22304d;--primary:#3b82f6;--primary-600:#2563eb;--accent:#22c55e}
*{box-sizing:border-box}
body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:var(--bg);color:var(--text)}
.container{max-width:980px;margin:0 auto;padding:48px 24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:32px;box-shadow:0 8px 28px rgba(0,0,0,.28)}
.h{margin:0 0 10px 0;font-size:26px}
.p{margin:0 0 22px 0;color:#b6c2d0;line-height:1.5}
label{display:block;margin:1rem 0 .4rem;font-weight:700;color:#d3dcf0}
input[type="text"]{width:100%;padding:1rem;border-radius:10px;border:1px solid var(--border);background:#0c1426;color:var(--text);font-size:16px}
.input-file{display:flex;align-items:center;gap:12px}
input[type="file"]{display:none}
.file-btn{appearance:none;border:1px dashed var(--border);background:#0c1426;color:var(--text);padding:.9rem 1.1rem;border-radius:10px;cursor:pointer}
.file-name{color:var(--muted);font-size:13px}
.row{display:flex;gap:12px;align-items:center;margin-top:22px;flex-wrap:wrap}
.btn{appearance:none;border:0;border-radius:10px;padding:.9rem 1.2rem;font-weight:800;cursor:pointer;font-size:15px;display:inline-flex;align-items:center;gap:8px}
.btn.primary{background:var(--primary);color:#fff}
.btn.primary:hover{background:var(--primary-600)}
.btn.secondary{background:transparent;color:#93c5fd;border:1px solid #2a3a5a}
.btn.secondary:hover{background:#0c1426}
.btn:disabled{opacity:.6;cursor:not-allowed}
.note{font-size:13px;color:var(--muted);margin-top:10px}
.footer{margin-top:22px;color:#8ea0b8;font-size:12px}
.spinner{display:none;margin-left:8px;border:3px solid #2a3a5a;border-top:3px solid #fff;border-radius:50%;width:16px;height:16px;animation:spin 1s linear infinite}
@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
.badge{display:inline-block;background:#0c1b34;border:1px solid var(--border);border-radius:999px;padding:.25rem .6rem;color:#b6c2d0;font-size:12px}
</style></head>
<body>
	<div class="container">
		<div class="card">
			<h1 class="h">Cyber Cell IP Trace Uploader</h1>
			<p class="p">Upload Google subscriber HTML. We will extract only the IP Activity table (Timestamp + IP Address), enrich all IPs via InfoByIP in batches of 100, then generate a master Excel.</p>
			<form id="f" method="post" action="/process" enctype="multipart/form-data">
				<label>FIR No.</label>
				<input name="firNo" type="text" placeholder="e.g., FIR/2025/1234" required />
				<label>SubscriberInfo HTML file</label>
				<div class="input-file">
					<label class="file-btn" for="htmlfile">📄 Choose HTML file</label>
					<input id="htmlfile" type="file" name="htmlfile" accept="text/html,.html" required />
					<span id="fileName" class="file-name">No file chosen</span>
				</div>
				<div class="note">We do not read other sections of the HTML. Duplicates are preserved.</div>
				<div class="row">
					<button id="submitBtn" class="btn primary" type="submit">▶ Process</button>
					<button id="resetBtn" class="btn secondary" type="button">↺ Reset</button>
					<div id="spin" class="spinner"></div>
				</div>
			</form>
			<div class="footer">For authorized use. Data is processed locally; IP enrichment is fetched from InfoByIP.</div>
		</div>
	</div>
	<script>
		const f=document.getElementById('f');
		const btn=document.getElementById('submitBtn');
		const spin=document.getElementById('spin');
		const fileInput=document.getElementById('htmlfile');
		const fileName=document.getElementById('fileName');
		const resetBtn=document.getElementById('resetBtn');
		fileInput.addEventListener('change',()=>{fileName.textContent=fileInput.files[0]?fileInput.files[0].name:'No file chosen'});
		resetBtn.addEventListener('click',()=>{f.reset();fileName.textContent='No file chosen'});
		f.addEventListener('submit',()=>{btn.disabled=true;spin.style.display='inline-block';btn.textContent='Processing...';});
	</script>
</body></html>`);
});

app.post('/process', upload.single('htmlfile'), async (req, res) => {
	const startedAt = Date.now();
	try {
		const firNo = (req.body.firNo || '').trim();
		if (!firNo) return res.status(400).send('FIR No. required');
		if (!req.file) return res.status(400).send('HTML file required');

		const htmlPath = req.file.path;
		const htmlContent = fs.readFileSync(htmlPath, 'utf8');
		const rows = parseHtmlForTimestampIp(htmlContent);
		if (!rows.length) return res.status(400).send('No Timestamp/IP rows found');

		// Prepare per-run folder runs/<timestamp>_<safeFIR>
		const safeFir = firNo.replace(/[^a-z0-9_-]+/gi, '-').slice(0, 64) || 'FIR';
		const ts = new Date().toISOString().replace(/[:.]/g, '').replace('T','_').replace('Z','');
		const workDir = path.join(runsBaseDir, `${ts}_${safeFir}`);
		fs.mkdirSync(workDir, { recursive: true });

		// Preserve duplicates: use all IPs in order
		const allIps = rows.map(r => r.ip);

		// Save the exact IP list used
		fs.writeFileSync(path.join(workDir, 'ips.txt'), allIps.join('\n'));

		// Run batches (100 IPs per request) over all IPs and merge CSVs
		const mergedCsvPath = await runInfoByIpBulkLookupBatches(allIps, workDir, 100);

		// Build master Excel from merged CSV
		const excelPath = path.join(workDir, 'master.xlsx');
		await buildExcel({ firNo, htmlRows: rows, infobyipCsvPath: mergedCsvPath, outputPath: excelPath });

		const ms = Date.now() - startedAt;
		res.type('html').send(`<!doctype html><html><body style="font-family:Segoe UI,Arial,sans-serif;padding:32px;background:#0b1220;color:#e6e9ef">
			<h2 style="margin-top:0">Completed in ${ms} ms</h2>
			<p><span class=\"badge\">${rows.length} rows (duplicates preserved)</span> <span class=\"badge\">Batched by 100</span> <span class=\"badge\">FIR: ${escapeHtml(firNo)}</span></p>
			<p class=\"note\">Saved under: ${escapeHtml(workDir)}</p>
			<div style=\"display:flex;gap:12px;flex-wrap:wrap;margin-top:16px\">
				<a style=\"text-decoration:none\" href=\"/download?path=${encodeURIComponent(mergedCsvPath)}\"><button class=\"btn secondary\">⬇ Download Merged CSV</button></a>
				<a style=\"text-decoration:none\" href=\"/download?path=${encodeURIComponent(excelPath)}\"><button class=\"btn primary\">⬇ Download Master Excel</button></a>
				<a style=\"text-decoration:none\" href=\"/\"><button class=\"btn secondary\">＋ Process Another</button></a>
			</div>
		</body></html>`);
	} catch (err) {
		console.error(err);
		const msg = (err && err.message) ? String(err.message) : 'Unknown error';
		res.status(500).type('html').send(`<!doctype html><html><body style="font-family:Segoe UI,Arial,sans-serif;padding:32px;background:#0b1220;color:#e6e9ef">
			<h2 style="margin-top:0">Processing failed</h2>
			<pre style="white-space:pre-wrap;background:#111a2d;border:1px solid #22304d;border-radius:10px;padding:14px">${escapeHtml(msg)}</pre>
			<div style="margin-top:12px"><a style="color:#93c5fd" href="/">← Back</a></div>
		</body></html>`);
	}
});

app.get('/download', (req, res) => {
	const p = req.query.path;
	if (!p) return res.status(400).send('path is required');
	const abs = path.isAbsolute(p) ? p : path.join(__dirname, '..', p);
	if (!fs.existsSync(abs)) return res.status(404).send('file not found');
	res.download(abs);
});

function escapeHtml(s) {
	return s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on http://localhost:${port}`));
