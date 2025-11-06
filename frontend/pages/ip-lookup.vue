<template>
  <div class="ip-lookup-page">
    <div class="page-header">
      <div>
        <h1>🔍 Unlimited IP Lookup System</h1>
        <p class="subtitle">Advanced InfoByIP Integration with Cloudflare Bypass</p>
      </div>
      <CookieManager @cookiesUpdated="onCookiesUpdated" />
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
              <button @click="downloadFile(results.csv, 'ip_lookup_results.csv')" class="btn-download-small">
                💾 Download CSV
              </button>
            </div>
          </div>
          <div class="result-card">
            <div class="card-icon">📋</div>
            <div class="card-content">
              <h3>JSON Results</h3>
              <p>{{ results.json }}</p>
              <button @click="downloadFile(results.json, 'ip_lookup_results.json')" class="btn-download-small">
                💾 Download JSON
              </button>
            </div>
          </div>
        </div>
        
        <!-- Master File Section -->
        <div class="master-file-section">
          <h3>🎯 Create Master File</h3>
          <p>Merge original_log.csv with IP lookup results to create a comprehensive Master file</p>
          <button 
            @click="createMasterFile" 
            :disabled="mergingMaster"
            class="btn-create-master"
          >
            {{ mergingMaster ? '⏳ Creating Master File...' : '✨ Create Master File.csv' }}
          </button>
          
          <div v-if="masterFile" class="master-result">
            <div class="success-message">
              ✅ Master file created successfully!
            </div>
            <div class="master-info">
              <p><strong>Total Records:</strong> {{ masterFile.total_records }}</p>
              <p><strong>Columns:</strong> {{ masterFile.columns.join(', ') }}</p>
            </div>
            <button @click="downloadFile(masterFile.master_file, 'Master file.csv')" class="btn-download-master">
              💾 Download Master File.csv
            </button>
          </div>
        </div>

        <!-- Fix to Start Section -->
        <div v-if="masterFile" class="card master-section">
          <h3>🔧 Fix to Start</h3>
          <p>Remove header row and prepare file for Final Report Generator</p>
          <button 
            @click="fixToStart" 
            :disabled="fixingFile"
            class="btn-fix-start"
          >
            {{ fixingFile ? '⏳ Processing...' : '🚀 Fix to Start' }}
          </button>
          
          <div v-if="fixedFile" class="fixed-result">
            <div class="success-message">
              ✅ Fixed file created successfully!
            </div>
            <div class="fixed-info">
              <p><strong>Total Records:</strong> {{ fixedFile.total_records }}</p>
              <p><strong>Status:</strong> Header removed, ready for Final Report Generator</p>
            </div>
            <button @click="downloadFile(fixedFile.fixed_file, 'fully_fixed.csv')" class="btn-download-fixed">
              💾 Download fully_fixed.csv
            </button>
            
            <div class="final-report-info">
              <h4>📊 Next Step: Final Report Generator</h4>
              <p>Upload <strong>fully_fixed.csv</strong> to the Final Report Generator to get your complete analysis report.</p>
              <a href="/Final Report Generator_V1.html" target="_blank" class="btn-final-report">
                🎯 Open Final Report Generator
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import IPLookupTerminal from '~/components/IPLookupTerminal.vue'

// Composables
const { authenticatedFetch, restoreState } = useAuthenticatedFetch()

// State
const runDirInput = ref('')
const selectedRunDir = ref('')
const autoStart = ref(false)
const results = ref(null)
const recentRuns = ref([])
const mergingMaster = ref(false)
const masterFile = ref(null)
const fixingFile = ref(false)
const fixedFile = ref(null)

// Watch and save state to localStorage when it changes
watch([selectedRunDir, results, masterFile, fixedFile], () => {
  if (typeof window !== 'undefined') {
    if (selectedRunDir.value) localStorage.setItem('current_run_dir', selectedRunDir.value)
    if (results.value) localStorage.setItem('current_results', JSON.stringify(results.value))
    if (masterFile.value) localStorage.setItem('current_master_file', JSON.stringify(masterFile.value))
    if (fixedFile.value) localStorage.setItem('current_fixed_file', JSON.stringify(fixedFile.value))
  }
})

// Methods
const loadRunDirectory = async () => {
  if (!runDirInput.value.trim()) {
    alert('Please enter a run directory path')
    return
  }

  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase
    // Verify the directory has original_log.csv
    const response = await fetch(`${apiBase}/api/lookup/status?run_dir=${encodeURIComponent(runDirInput.value)}`)
    
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

const onLookupComplete = async (data) => {
  results.value = data
  console.log('Lookup complete:', data)
  
  // Auto-store results in database if FIR number is provided
  const urlParams = new URLSearchParams(window.location.search)
  const firNumber = urlParams.get('fir_number')
  
  if (firNumber && data.csv) {
    try {
      console.log('Auto-storing results for FIR:', firNumber)
      
      const config = useRuntimeConfig()
      const apiBase = config.public.apiBase
      // Fetch the CSV file
      const csvResponse = await fetch(`${apiBase}${data.csv}`)
      const csvBlob = await csvResponse.blob()
      const csvFile = new File([csvBlob], 'ip_lookup_results.csv', { type: 'text/csv' })
      
      // Upload to FIR database
      const formData = new FormData()
      formData.append('file', csvFile)
      
      // Get auth token
      const token = localStorage.getItem('auth_token')
      
      // Split FIR number (e.g., "254/25" -> "254" and "25")
      // If no year provided, use current year
      const parts = firNumber.split('/')
      const firNum = parts[0]
      const year = parts[1] || new Date().getFullYear().toString().slice(-2)
      
      const storeResponse = await fetch(`${apiBase}/api/fir/store-ip-results/${firNum}/${year}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
      
      if (storeResponse.ok) {
        const result = await storeResponse.json()
        alert(`✅ Success! ${result.ips_stored} IPs automatically stored in database for ${firNumber}`)
        console.log('Auto-store successful:', result)
      } else {
        console.error('Auto-store failed:', await storeResponse.text())
      }
    } catch (error) {
      console.error('Error auto-storing results:', error)
      // Don't show error to user - they can still download manually
    }
  }
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

const downloadFile = async (filePath, fileName) => {
  if (typeof window === 'undefined') return
  
  try {
    console.log('📥 Downloading file:', filePath)
    
    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase
    
    // Ensure filePath starts with /
    const cleanPath = filePath.startsWith('/') ? filePath : `/${filePath}`
    
    // Build full URL
    const url = `${apiBase}${cleanPath}`
    console.log('🌐 Full URL:', url)
    
    // Fetch the file with error handling
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/octet-stream, */*'
      }
    })
    
    console.log('📡 Response status:', response.status)
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Download failed:', errorText)
      throw new Error(`Failed to download: ${response.status} - ${errorText}`)
    }
    
    // Get the blob
    const blob = await response.blob()
    console.log('📦 Blob size:', blob.size, 'bytes')
    console.log('📦 Blob type:', blob.type)
    
    if (blob.size === 0) {
      throw new Error('Downloaded file is empty')
    }
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.style.display = 'none'
    document.body.appendChild(link)
    
    // Trigger download
    link.click()
    
    // Clean up after a short delay
    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    }, 100)
    
    console.log('✅ Download initiated:', fileName)
    alert(`✅ Download started: ${fileName}`)
    
  } catch (error) {
    console.error('❌ Download error:', error)
    alert(`Failed to download file: ${error.message}\n\nPlease check:\n1. Backend is running\n2. File exists\n3. Check browser console for details`)
  }
}

const createMasterFile = async () => {
  if (!selectedRunDir.value) {
    alert('No run directory selected')
    return
  }
  
  mergingMaster.value = true
  masterFile.value = null
  
  try {
    console.log('Creating master file for:', selectedRunDir.value)
    
    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase
    
    const formData = new FormData()
    formData.append('run_dir', selectedRunDir.value)
    
    // Use authenticatedFetch - automatically handles 401 and preserves state
    const response = await authenticatedFetch(`${apiBase}/api/merge-master-file`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || 'Failed to create master file')
    }
    
    const data = await response.json()
    console.log('Master file created:', data)
    
    masterFile.value = data
    alert(`✅ Master file created successfully!\n${data.total_records} records merged`)
    
  } catch (error) {
    console.error('Master file error:', error)
    alert(`Failed to create master file: ${error.message}`)
  } finally {
    mergingMaster.value = false
  }
}

const fixToStart = async () => {
  if (!masterFile.value) {
    alert('Please create Master file first')
    return
  }
  
  fixingFile.value = true
  fixedFile.value = null
  
  try {
    console.log('Creating fixed file for:', selectedRunDir.value)
    
    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase
    
    const formData = new FormData()
    formData.append('run_dir', selectedRunDir.value)
    
    // Use authenticatedFetch - automatically handles 401 and preserves state
    const response = await authenticatedFetch(`${apiBase}/api/fix-to-start`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || 'Failed to create fixed file')
    }
    
    const data = await response.json()
    console.log('Fixed file created:', data)
    
    fixedFile.value = data
    alert(`✅ Fixed file created successfully!\n${data.total_records} records ready for Final Report Generator`)
    
  } catch (error) {
    console.error('Fix to start error:', error)
    alert(`Failed to create fixed file: ${error.message}`)
  } finally {
    fixingFile.value = false
  }
}

// Cookie update handler
const onCookiesUpdated = (status) => {
  console.log('Cookies updated:', status)
  // Could show a notification or refresh status
}

// Lifecycle
onMounted(async () => {
  // Restore preserved state if user was redirected to login
  const preserved = restoreState()
  if (preserved && preserved.pageData) {
    console.log('🔄 Restoring preserved state...')
    
    // Restore run directory
    if (preserved.pageData.runDir) {
      selectedRunDir.value = preserved.pageData.runDir
      runDirInput.value = preserved.pageData.runDir
    }
    
    // Restore results
    if (preserved.pageData.results) {
      try {
        results.value = JSON.parse(preserved.pageData.results)
      } catch (e) {
        console.error('Failed to restore results:', e)
      }
    }
    
    // Restore master file
    if (preserved.pageData.masterFile) {
      try {
        masterFile.value = JSON.parse(preserved.pageData.masterFile)
      } catch (e) {
        console.error('Failed to restore master file:', e)
      }
    }
    
    // Restore fixed file
    if (preserved.pageData.fixedFile) {
      try {
        fixedFile.value = JSON.parse(preserved.pageData.fixedFile)
      } catch (e) {
        console.error('Failed to restore fixed file:', e)
      }
    }
    
    console.log('✅ State restored successfully!')
    alert('✅ Welcome back! Your research data has been restored.')
  }
  
  loadRecentRuns()

  // Check if run_dir is passed in query params
  const urlParams = new URLSearchParams(window.location.search)
  const runDir = urlParams.get('run_dir')
  const shouldAutoStart = urlParams.get('auto_start') === 'true'
  
  console.log('📍 IP Lookup Page Loaded')
  console.log('  - run_dir:', runDir)
  console.log('  - auto_start:', shouldAutoStart)
  
  if (runDir) {
    runDirInput.value = runDir
    autoStart.value = shouldAutoStart
    
    // Verify directory exists with retry logic (directory might not be created immediately)
    const maxRetries = 5
    let retryCount = 0
    
    while (retryCount < maxRetries) {
      try {
        const config = useRuntimeConfig()
        const apiBase = config.public.apiBase
        console.log(`🔍 Verifying directory (attempt ${retryCount + 1}/${maxRetries}):`, runDir)
        
        const response = await fetch(`${apiBase}/api/lookup/status?run_dir=${encodeURIComponent(runDir)}`)
        
        if (response.ok) {
          const data = await response.json()
          console.log('✅ Directory verified:', data)
          
          if (data.total_ips > 0) {
            selectedRunDir.value = runDir
            saveToRecentRuns(runDir, data)
            console.log('✅ Auto-start enabled:', shouldAutoStart)
            break // Success!
          } else {
            console.error('❌ No IPs found in directory')
            alert('No IPs found in the uploaded file. Please check your HTML file.')
            break
          }
        } else if (response.status === 404) {
          // Directory not found, retry
          console.warn(`⚠️ Directory not found yet (attempt ${retryCount + 1}/${maxRetries}), retrying in 1 second...`)
          retryCount++
          if (retryCount < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          } else {
            console.error('❌ Directory not found after all retries')
            alert('Could not find the uploaded directory. The file might still be processing. Please wait a moment and try refreshing.')
          }
        } else {
          console.error('❌ Directory verification failed:', response.status)
          alert('Could not verify the uploaded directory. Please try again.')
          break
        }
      } catch (error) {
        console.error(`❌ Error verifying directory (attempt ${retryCount + 1}):`, error)
        retryCount++
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        } else {
          // Fallback: still try to load it
          console.warn('⚠️ Using fallback: setting directory without verification')
          selectedRunDir.value = runDir
          break
        }
      }
    }
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(0, 255, 0, 0.05);
  border: 1px solid #0f0;
  border-radius: 8px;
}

.page-header > div:first-child {
  flex: 1;
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
  font-family: 'Courier New', monospace;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-download-small:hover {
  background: #0f0;
  color: #000;
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
}

/* Master File Section */
.master-file-section {
  margin-top: 24px;
  padding: 24px;
  background: rgba(0, 255, 255, 0.05);
  border: 2px solid #0ff;
  border-radius: 8px;
}

.master-file-section h3 {
  margin: 0 0 8px;
  color: #0ff;
  font-size: 20px;
}

.master-file-section p {
  margin: 0 0 16px;
  color: #999;
  font-size: 14px;
}

.btn-create-master {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #0ff 0%, #0f0 100%);
  border: none;
  border-radius: 8px;
  color: #000;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
}

.btn-create-master:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
}

.btn-create-master:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.master-result {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 255, 0, 0.05);
  border: 1px solid #0f0;
  border-radius: 8px;
}

.success-message {
  color: #0f0;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
}

.master-info {
  margin-bottom: 16px;
}

.master-info p {
  margin: 4px 0;
  color: #0ff;
  font-size: 14px;
}

.master-info strong {
  color: #0f0;
}

.btn-download-master {
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

/* Fix to Start Button */
.btn-fix-start {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #ff0080 0%, #ff8c00 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 0 20px rgba(255, 0, 128, 0.3);
}

.btn-fix-start:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(255, 0, 128, 0.5);
}

.btn-fix-start:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.fixed-result {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 0, 128, 0.05);
  border: 1px solid #ff0080;
  border-radius: 8px;
}

.fixed-info {
  margin-bottom: 16px;
}

.fixed-info p {
  margin: 4px 0;
  color: #ff8c00;
  font-size: 14px;
}

.fixed-info strong {
  color: #ff0080;
}

.btn-download-fixed {
  width: 100%;
  padding: 12px;
  background: #000;
  border: 2px solid #ff0080;
  border-radius: 4px;
  color: #ff0080;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.btn-download-fixed:hover {
  background: rgba(255, 0, 128, 0.1);
  box-shadow: 0 0 15px rgba(255, 0, 128, 0.3);
}

.final-report-info {
  margin-top: 20px;
  padding: 16px;
  background: rgba(0, 255, 255, 0.05);
  border: 2px dashed #0ff;
  border-radius: 8px;
}

.final-report-info h4 {
  color: #0ff;
  margin-bottom: 8px;
  font-size: 16px;
}

.final-report-info p {
  color: #0f0;
  margin-bottom: 12px;
  font-size: 14px;
}

.btn-final-report {
  display: inline-block;
  padding: 12px 24px;
  background: linear-gradient(135deg, #0ff 0%, #00ff88 100%);
  border: none;
  border-radius: 6px;
  color: #000;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
}

.btn-final-report:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 25px rgba(0, 255, 255, 0.5);
}

.btn-download-master:hover {
  background: #0f0;
  color: #000;
  box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
}
</style>
