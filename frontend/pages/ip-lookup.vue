<template>
  <div class="ip-lookup-page">
    <div class="page-header">
      <h1>🔍 Unlimited IP Lookup System</h1>
      <p class="subtitle">Advanced InfoByIP Integration with Cloudflare Bypass</p>
    </div>

    <!-- Run Directory Selection -->
    <div v-if="!selectedRunDir" class="run-selector">
      <div class="selector-card">
        <h2>📁 Select Processed Run Directory</h2>
        <p>Choose a directory from the upload/extraction phase to start IP lookup</p>
        
        <div class="input-group">
          <label for="runDir">Run Directory Path:</label>
          <input
            id="runDir"
            v-model="runDirInput"
            type="text"
            placeholder="backend/processed/20251031_125529_202"
            class="dir-input"
            @keyup.enter="loadRunDirectory"
          />
          <button @click="loadRunDirectory" class="btn-load">
            Load Directory
          </button>
        </div>

        <!-- Recent Runs -->
        <div v-if="recentRuns.length > 0" class="recent-runs">
          <h3>Recent Runs:</h3>
          <div class="runs-list">
            <div
              v-for="run in recentRuns"
              :key="run.path"
              class="run-item"
              @click="selectRun(run)"
            >
              <div class="run-info">
                <span class="run-name">{{ run.name }}</span>
                <span class="run-date">{{ run.date }}</span>
              </div>
              <div class="run-stats">
                <span>{{ run.ipCount }} IPs</span>
                <span v-if="run.hasResults" class="has-results">✅ Results Available</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Manual Path Examples -->
        <div class="path-examples">
          <h4>Example Paths:</h4>
          <code>backend/processed/20251031_125529_202</code>
          <code>C:\Users\saheb\Downloads\New FIR\backend\processed\20251031_125529_202</code>
        </div>
      </div>
    </div>

    <!-- IP Lookup Terminal -->
    <div v-else class="terminal-container">
      <div class="terminal-header-info">
        <div class="info-item">
          <span class="label">Run Directory:</span>
          <span class="value">{{ selectedRunDir }}</span>
        </div>
        <button @click="changeDirectory" class="btn-change">
          📁 Change Directory
        </button>
      </div>

      <IPLookupTerminal
        :run-dir="selectedRunDir"
        :auto-start="autoStart"
        @complete="onLookupComplete"
        @error="onLookupError"
      />

      <!-- Results Section -->
      <div v-if="results" class="results-section">
        <h2>📊 Lookup Results</h2>
        <div class="results-grid">
          <div class="result-card">
            <div class="card-icon">📄</div>
            <div class="card-content">
              <h3>CSV Results</h3>
              <p>{{ results.csv }}</p>
              <a :href="results.csv" download class="btn-download-small">
                💾 Download CSV
              </a>
            </div>
          </div>
          <div class="result-card">
            <div class="card-icon">📋</div>
            <div class="card-content">
              <h3>JSON Results</h3>
              <p>{{ results.json }}</p>
              <a :href="results.json" download class="btn-download-small">
                💾 Download JSON
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import IPLookupTerminal from '~/components/IPLookupTerminal.vue'

// State
const runDirInput = ref('')
const selectedRunDir = ref('')
const autoStart = ref(false)
const results = ref(null)
const recentRuns = ref([])

// Methods
const loadRunDirectory = async () => {
  if (!runDirInput.value.trim()) {
    alert('Please enter a run directory path')
    return
  }

  try {
    // Verify the directory has original_log.csv
    const response = await fetch(`/api/lookup/status?run_dir=${encodeURIComponent(runDirInput.value)}`)
    
    if (!response.ok) {
      throw new Error('Directory not found or invalid')
    }

    const data = await response.json()
    
    if (data.total_ips === 0) {
      alert('No IPs found in original_log.csv. Please select a valid processed directory.')
      return
    }

    selectedRunDir.value = runDirInput.value
    autoStart.value = false

    // Save to recent runs
    saveToRecentRuns(runDirInput.value, data)

  } catch (error) {
    alert(`Error loading directory: ${error.message}`)
  }
}

const selectRun = (run) => {
  runDirInput.value = run.path
  loadRunDirectory()
}

const changeDirectory = () => {
  selectedRunDir.value = ''
  results.value = null
}

const onLookupComplete = (data) => {
  results.value = data
  console.log('Lookup complete:', data)
}

const onLookupError = (error) => {
  console.error('Lookup error:', error)
  alert(`Lookup failed: ${error.message}`)
}

const saveToRecentRuns = (path, data) => {
  const run = {
    path,
    name: path.split('/').pop() || path.split('\\').pop(),
    date: new Date().toLocaleString(),
    ipCount: data.total_ips,
    hasResults: data.has_results
  }

  // Add to recent runs (max 5)
  const recent = JSON.parse(localStorage.getItem('recentRuns') || '[]')
  const filtered = recent.filter(r => r.path !== path)
  filtered.unshift(run)
  const limited = filtered.slice(0, 5)
  localStorage.setItem('recentRuns', JSON.stringify(limited))
  recentRuns.value = limited
}

const loadRecentRuns = () => {
  const recent = JSON.parse(localStorage.getItem('recentRuns') || '[]')
  recentRuns.value = recent
}

// Lifecycle
onMounted(() => {
  loadRecentRuns()

  // Check if run_dir is passed in query params
  const urlParams = new URLSearchParams(window.location.search)
  const runDir = urlParams.get('run_dir')
  if (runDir) {
    runDirInput.value = runDir
    loadRunDirectory()
    autoStart.value = urlParams.get('auto_start') === 'true'
  }
})
</script>

<style scoped>
.ip-lookup-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  padding: 24px;
  color: #0f0;
  font-family: 'Courier New', monospace;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(0, 255, 0, 0.05);
  border: 1px solid #0f0;
  border-radius: 8px;
}

.page-header h1 {
  font-size: 32px;
  margin: 0;
  color: #0f0;
  text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
}

.subtitle {
  margin: 8px 0 0;
  color: #0ff;
  font-size: 14px;
}

/* Run Selector */
.run-selector {
  max-width: 800px;
  margin: 0 auto;
}

.selector-card {
  background: #000;
  border: 2px solid #0f0;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
}

.selector-card h2 {
  margin: 0 0 8px;
  color: #0f0;
}

.selector-card p {
  margin: 0 0 24px;
  color: #0ff;
  font-size: 14px;
}

.input-group {
  margin-bottom: 24px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  color: #0f0;
  font-size: 14px;
}

.dir-input {
  width: 100%;
  padding: 12px;
  background: #000;
  border: 1px solid #0f0;
  border-radius: 4px;
  color: #0f0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  margin-bottom: 12px;
}

.dir-input:focus {
  outline: none;
  border-color: #0ff;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.btn-load {
  width: 100%;
  padding: 12px;
  background: #000;
  border: 2px solid #0f0;
  border-radius: 4px;
  color: #0f0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-load:hover {
  background: #0f0;
  color: #000;
  box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
}

/* Recent Runs */
.recent-runs {
  margin: 24px 0;
}

.recent-runs h3 {
  margin: 0 0 12px;
  color: #0ff;
  font-size: 16px;
}

.runs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.run-item {
  padding: 12px;
  background: rgba(0, 255, 0, 0.05);
  border: 1px solid #0f0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.run-item:hover {
  background: rgba(0, 255, 0, 0.1);
  border-color: #0ff;
  transform: translateX(4px);
}

.run-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.run-name {
  color: #0f0;
  font-weight: bold;
}

.run-date {
  color: #999;
  font-size: 12px;
}

.run-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #0ff;
}

.has-results {
  color: #0f0;
}

/* Path Examples */
.path-examples {
  margin-top: 24px;
  padding: 16px;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid #0ff;
  border-radius: 4px;
}

.path-examples h4 {
  margin: 0 0 8px;
  color: #0ff;
  font-size: 14px;
}

.path-examples code {
  display: block;
  padding: 8px;
  margin: 4px 0;
  background: #000;
  border: 1px solid #0ff;
  border-radius: 4px;
  color: #0ff;
  font-size: 12px;
}

/* Terminal Container */
.terminal-container {
  max-width: 1200px;
  margin: 0 auto;
}

.terminal-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(0, 255, 0, 0.05);
  border: 1px solid #0f0;
  border-radius: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.label {
  color: #0ff;
  font-weight: bold;
}

.value {
  color: #0f0;
}

.btn-change {
  padding: 8px 16px;
  background: #000;
  border: 1px solid #0ff;
  border-radius: 4px;
  color: #0ff;
  font-family: 'Courier New', monospace;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-change:hover {
  background: #0ff;
  color: #000;
}

/* Results Section */
.results-section {
  margin-top: 24px;
  padding: 24px;
  background: rgba(0, 255, 0, 0.05);
  border: 2px solid #0f0;
  border-radius: 8px;
}

.results-section h2 {
  margin: 0 0 16px;
  color: #0f0;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.result-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #000;
  border: 1px solid #0f0;
  border-radius: 8px;
}

.card-icon {
  font-size: 32px;
}

.card-content {
  flex: 1;
}

.card-content h3 {
  margin: 0 0 8px;
  color: #0f0;
  font-size: 16px;
}

.card-content p {
  margin: 0 0 12px;
  color: #0ff;
  font-size: 12px;
  word-break: break-all;
}

.btn-download-small {
  display: inline-block;
  padding: 6px 12px;
  background: #000;
  border: 1px solid #0f0;
  border-radius: 4px;
  color: #0f0;
  text-decoration: none;
  font-size: 12px;
  transition: all 0.3s;
}

.btn-download-small:hover {
  background: #0f0;
  color: #000;
}
</style>
