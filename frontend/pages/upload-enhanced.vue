<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRuntimeConfig } from '#app'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

// Form data
const firNo = ref('')
const file = ref<File | null>(null)
const preserveDuplicates = ref(false)
const bypassCloudflare = ref(false)

// Status tracking
const uploading = ref(false)
const processing = ref(false)
const runDir = ref('')
const uploadResult = ref<any>(null)

// Processing status
const processingStatus = ref({
  stage: 'idle', // idle, uploading, extracting, fetching, processing, complete, error
  progress: 0,
  currentIP: 0,
  totalIPs: 0,
  message: '',
  startTime: null as Date | null,
  logs: [] as string[]
})

let statusInterval: any = null

const progressPercent = computed(() => {
  if (processingStatus.value.totalIPs === 0) return 0
  return Math.round((processingStatus.value.currentIP / processingStatus.value.totalIPs) * 100)
})

const elapsedTime = computed(() => {
  if (!processingStatus.value.startTime) return '0s'
  const elapsed = Math.floor((Date.now() - processingStatus.value.startTime.getTime()) / 1000)
  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`
})

const estimatedTimeRemaining = computed(() => {
  if (processingStatus.value.currentIP === 0) return 'Calculating...'
  if (processingStatus.value.currentIP === processingStatus.value.totalIPs) return 'Complete!'
  
  const elapsed = Date.now() - (processingStatus.value.startTime?.getTime() || Date.now())
  const avgTimePerIP = elapsed / processingStatus.value.currentIP
  const remaining = (processingStatus.value.totalIPs - processingStatus.value.currentIP) * avgTimePerIP
  
  const minutes = Math.floor(remaining / 60000)
  const seconds = Math.floor((remaining % 60000) / 1000)
  return minutes > 0 ? `~${minutes}m ${seconds}s` : `~${seconds}s`
})

function onChange(e: Event) {
  const target = e.target as HTMLInputElement
  file.value = target.files?.[0] || null
}

function addLog(message: string) {
  const timestamp = new Date().toLocaleTimeString()
  processingStatus.value.logs.unshift(`[${timestamp}] ${message}`)
  if (processingStatus.value.logs.length > 50) {
    processingStatus.value.logs = processingStatus.value.logs.slice(0, 50)
  }
}

async function uploadFile() {
  if (!file.value || !firNo.value) {
    processingStatus.value.message = 'FIR number and file are required'
    processingStatus.value.stage = 'error'
    return
  }
  
  // Reset status
  processingStatus.value = {
    stage: 'uploading',
    progress: 0,
    currentIP: 0,
    totalIPs: 0,
    message: 'Uploading file...',
    startTime: new Date(),
    logs: []
  }
  
  uploading.value = true
  addLog('Starting upload...')
  
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('fir', firNo.value)
  formData.append('preserve_duplicates', preserveDuplicates.value.toString())
  formData.append('bypass_cloudflare', bypassCloudflare.value.toString())
  
  try {
    addLog(`Uploading ${file.value.name}...`)
    
    const response = await fetch(`${apiBase}/api/upload/`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error('Upload failed')
    }
    
    const data = await response.json()
    uploadResult.value = data
    runDir.value = data.run_dir
    
    processingStatus.value.stage = 'extracting'
    processingStatus.value.totalIPs = data.unique_ips
    processingStatus.value.message = `Extracted ${data.count_rows} records, ${data.unique_ips} unique IPs`
    
    addLog(`✅ Upload successful!`)
    addLog(`📊 Total records: ${data.count_rows}`)
    addLog(`🎯 Unique IPs: ${data.unique_ips}`)
    addLog(`📦 Batches created: ${data.batches.length}`)
    
    if (bypassCloudflare.value) {
      addLog(`🔥 Cloudflare bypass enabled - unlimited access mode`)
    }
    
    // Start status polling
    startStatusPolling()
    
  } catch (error: any) {
    processingStatus.value.stage = 'error'
    processingStatus.value.message = error?.message || 'Upload failed'
    addLog(`❌ Error: ${error?.message}`)
  } finally {
    uploading.value = false
  }
}

async function startStatusPolling() {
  processing.value = true
  processingStatus.value.stage = 'fetching'
  processingStatus.value.message = 'Fetching IP data from InfoByIP...'
  
  addLog('🚀 Starting background processing...')
  
  statusInterval = setInterval(async () => {
    try {
      const status = await $fetch(`${apiBase}/api/status`, {
        params: { run_dir: runDir.value }
      }) as any
      
      if (status.state === 'fetching') {
        processingStatus.value.stage = 'fetching'
        processingStatus.value.currentIP = status.batches_fetched || 0
        processingStatus.value.message = `Fetching IP data: ${status.batches_fetched}/${status.batches_total} batches`
        
      } else if (status.state === 'merging') {
        processingStatus.value.stage = 'processing'
        processingStatus.value.message = 'Merging and processing results...'
        addLog('📊 Merging results...')
        
      } else if (status.state === 'ready') {
        processingStatus.value.stage = 'complete'
        processingStatus.value.currentIP = processingStatus.value.totalIPs
        processingStatus.value.message = '✅ Processing complete! Ready to download.'
        processingStatus.value.progress = 100
        
        addLog('🎉 Processing complete!')
        addLog(`✅ ${processingStatus.value.totalIPs} IPs processed successfully`)
        
        clearInterval(statusInterval)
        processing.value = false
      }
      
    } catch (error) {
      console.error('Status check error:', error)
    }
  }, 3000) // Check every 3 seconds
}

function downloadCSV() {
  if (!runDir.value) {
    processingStatus.value.message = 'No data to download'
    return
  }
  
  addLog('📥 Downloading CSV...')
  
  // Trigger download
  const downloadUrl = `${apiBase}/api/export?run_dir=${encodeURIComponent(runDir.value)}&format=csv`
  window.open(downloadUrl, '_blank')
  
  addLog('✅ Download started!')
}

function downloadExcel() {
  if (!runDir.value) {
    processingStatus.value.message = 'No data to download'
    return
  }
  
  addLog('📥 Downloading Excel...')
  
  const downloadUrl = `${apiBase}/api/export?run_dir=${encodeURIComponent(runDir.value)}`
  window.open(downloadUrl, '_blank')
  
  addLog('✅ Download started!')
}

function reset() {
  firNo.value = ''
  file.value = null
  preserveDuplicates.value = false
  bypassCloudflare.value = false
  runDir.value = ''
  uploadResult.value = null
  processing.value = false
  uploading.value = false
  
  processingStatus.value = {
    stage: 'idle',
    progress: 0,
    currentIP: 0,
    totalIPs: 0,
    message: '',
    startTime: null,
    logs: []
  }
  
  if (statusInterval) {
    clearInterval(statusInterval)
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-dark-500 via-dark-400 to-dark-500 text-slate-200">
    <!-- Navigation -->
    <nav class="bg-gradient-to-r from-dark-300 via-dark-200 to-dark-300 border-b border-cyber-500/30 px-6 py-4 backdrop-blur-cyber">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg flex items-center justify-center">
            <span class="text-2xl">📤</span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-white font-display">Upload & Process</h1>
            <p class="text-xs text-slate-400">IP Intelligence Extraction</p>
          </div>
        </div>
        <NuxtLink to="/" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition">
          ← Dashboard
        </NuxtLink>
      </div>
    </nav>
    
    <div class="p-6 max-w-6xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <!-- Left Column: Upload Form -->
        <div class="space-y-6">
          <!-- Upload Card -->
          <div class="cyber-card">
            <h2 class="text-xl font-bold mb-4 flex items-center">
              <span class="text-2xl mr-2">📁</span>
              Upload Evidence
            </h2>
            
            <div class="space-y-4">
              <!-- FIR Number -->
              <div>
                <label class="block text-sm font-medium mb-2 text-slate-300">FIR Number</label>
                <input 
                  v-model="firNo" 
                  :disabled="processing"
                  class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none transition disabled:opacity-50" 
                  placeholder="e.g., FIR/2025/1234" 
                />
              </div>
              
              <!-- File Upload -->
              <div>
                <label class="block text-sm font-medium mb-2 text-slate-300">HTML File</label>
                <input 
                  type="file" 
                  accept="text/html,.html" 
                  @change="onChange"
                  :disabled="processing"
                  class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-gradient-to-r file:from-blue-600 file:to-cyan-600 file:text-white hover:file:from-blue-700 hover:file:to-cyan-700 file:transition disabled:opacity-50"
                />
                <p v-if="file" class="text-sm text-cyan-400 mt-2 flex items-center">
                  <span class="mr-2">✓</span>
                  {{ file.name }} ({{ (file.size / 1024).toFixed(2) }} KB)
                </p>
              </div>
              
              <!-- Options -->
              <div class="space-y-3">
                <!-- Preserve Duplicates -->
                <div class="flex items-center space-x-3 p-4 bg-slate-900 border border-slate-700 rounded-lg hover:border-slate-600 transition">
                  <input 
                    type="checkbox" 
                    id="preserveDuplicates" 
                    v-model="preserveDuplicates"
                    :disabled="processing"
                    class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
                  />
                  <label for="preserveDuplicates" class="text-sm font-medium cursor-pointer flex-1">
                    <span class="text-slate-200">Preserve duplicates</span>
                    <span class="block text-xs text-slate-400 mt-1">
                      Keep duplicate IPs in batch files
                    </span>
                  </label>
                </div>
                
                <!-- Cloudflare Bypass -->
                <div class="flex items-center space-x-3 p-4 bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-700/50 rounded-lg hover:border-orange-600/70 transition">
                  <input 
                    type="checkbox" 
                    id="bypassCloudflare" 
                    v-model="bypassCloudflare"
                    :disabled="processing"
                    class="w-4 h-4 text-orange-600 bg-slate-800 border-orange-600 rounded focus:ring-orange-500 focus:ring-2"
                  />
                  <label for="bypassCloudflare" class="text-sm font-medium cursor-pointer flex-1">
                    <div class="flex items-center space-x-2">
                      <span class="text-orange-400">🔥 Bypass Cloudflare</span>
                      <span class="px-2 py-0.5 bg-orange-600 text-white text-xs rounded-full font-bold">UNLIMITED</span>
                    </div>
                    <span class="block text-xs text-orange-300 mt-1">
                      Advanced anti-detection for unlimited InfoByIP access
                    </span>
                    <span class="block text-xs text-orange-400/70 mt-1">
                      ⚡ Slower but bypasses rate limits • 🎯 Best for large datasets
                    </span>
                  </label>
                </div>
              </div>
              
              <!-- Upload Button -->
              <button 
                @click="uploadFile" 
                :disabled="uploading || processing || !file || !firNo"
                class="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-lg font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg hover:shadow-cyan-500/50"
              >
                <span v-if="uploading">⏳ Uploading...</span>
                <span v-else-if="processing">🔄 Processing...</span>
                <span v-else>🚀 Upload & Extract</span>
              </button>
              
              <!-- Reset Button -->
              <button 
                v-if="processingStatus.stage === 'complete' || processingStatus.stage === 'error'"
                @click="reset"
                class="w-full px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition"
              >
                🔄 Start New Upload
              </button>
            </div>
          </div>
          
          <!-- Download Card (Show when complete) -->
          <div v-if="processingStatus.stage === 'complete'" class="cyber-card bg-gradient-to-br from-green-900/20 to-emerald-900/20 border-green-700/50">
            <h3 class="text-lg font-bold mb-4 flex items-center text-green-400">
              <span class="text-2xl mr-2">📥</span>
              Download Results
            </h3>
            
            <div class="grid grid-cols-2 gap-3">
              <button 
                @click="downloadCSV"
                class="px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg font-medium transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                📊 Download CSV
              </button>
              
              <button 
                @click="downloadExcel"
                class="px-4 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-lg font-medium transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                📈 Download Excel
              </button>
            </div>
            
            <p class="text-xs text-green-400 mt-3 text-center">
              ✓ Files will download to your default downloads folder
            </p>
          </div>
        </div>
        
        <!-- Right Column: Status Tracking -->
        <div class="space-y-6">
          <!-- Status Card -->
          <div class="cyber-card">
            <h2 class="text-xl font-bold mb-4 flex items-center justify-between">
              <span class="flex items-center">
                <span class="text-2xl mr-2">📊</span>
                Processing Status
              </span>
              <span v-if="processingStatus.stage !== 'idle'" class="text-sm font-normal">
                {{ elapsedTime }}
              </span>
            </h2>
            
            <!-- Status Badge -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-slate-400">Current Stage:</span>
                <span 
                  class="px-3 py-1 rounded-full text-xs font-bold"
                  :class="{
                    'bg-slate-700 text-slate-300': processingStatus.stage === 'idle',
                    'bg-blue-600 text-white animate-pulse': processingStatus.stage === 'uploading',
                    'bg-cyan-600 text-white': processingStatus.stage === 'extracting',
                    'bg-orange-600 text-white animate-pulse': processingStatus.stage === 'fetching',
                    'bg-purple-600 text-white': processingStatus.stage === 'processing',
                    'bg-green-600 text-white': processingStatus.stage === 'complete',
                    'bg-red-600 text-white': processingStatus.stage === 'error'
                  }"
                >
                  {{ processingStatus.stage.toUpperCase() }}
                </span>
              </div>
              
              <!-- Progress Bar -->
              <div v-if="processingStatus.totalIPs > 0" class="space-y-2">
                <div class="w-full bg-slate-800 rounded-full h-4 overflow-hidden">
                  <div 
                    class="h-full bg-gradient-to-r from-blue-600 via-cyan-500 to-green-500 transition-all duration-500 ease-out flex items-center justify-center text-xs font-bold"
                    :style="{ width: `${progressPercent}%` }"
                  >
                    <span v-if="progressPercent > 10" class="text-white drop-shadow">{{ progressPercent }}%</span>
                  </div>
                </div>
                
                <div class="flex justify-between text-xs text-slate-400">
                  <span>{{ processingStatus.currentIP }} / {{ processingStatus.totalIPs}} IPs</span>
                  <span v-if="processingStatus.stage === 'fetching'">ETA: {{ estimatedTimeRemaining }}</span>
                </div>
              </div>
            </div>
            
            <!-- Status Message -->
            <div class="p-4 bg-slate-900 border border-slate-700 rounded-lg">
              <p class="text-sm text-slate-300">{{ processingStatus.message || 'Ready to upload' }}</p>
            </div>
            
            <!-- Upload Info (when uploaded) -->
            <div v-if="uploadResult" class="mt-4 p-4 bg-slate-900 border border-cyan-700/30 rounded-lg space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-slate-400">FIR Number:</span>
                <span class="text-cyan-400 font-mono">{{ firNo }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-slate-400">Total Records:</span>
                <span class="text-white font-bold">{{ uploadResult.count_rows }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-slate-400">Unique IPs:</span>
                <span class="text-white font-bold">{{ uploadResult.unique_ips }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-slate-400">Batches:</span>
                <span class="text-white font-bold">{{ uploadResult.batches?.length || 0 }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-slate-400">Bypass Mode:</span>
                <span :class="bypassCloudflare ? 'text-orange-400 font-bold' : 'text-slate-400'">
                  {{ bypassCloudflare ? '🔥 ENABLED' : 'Disabled' }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Activity Log -->
          <div class="cyber-card max-h-96 overflow-hidden flex flex-col">
            <h3 class="text-lg font-bold mb-3 flex items-center">
              <span class="text-xl mr-2">📝</span>
              Activity Log
            </h3>
            
            <div class="flex-1 overflow-y-auto space-y-1 bg-slate-900 rounded-lg p-3 border border-slate-700">
              <div v-if="processingStatus.logs.length === 0" class="text-sm text-slate-500 text-center py-4">
                No activity yet...
              </div>
              <div 
                v-for="(log, index) in processingStatus.logs" 
                :key="index"
                class="text-xs font-mono text-slate-300 py-1 border-b border-slate-800 last:border-0"
              >
                {{ log }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cyber-card {
  @apply bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 shadow-xl;
}

.cyber-card:hover {
  @apply border-cyan-500/30 shadow-cyan-500/10;
}
</style>
