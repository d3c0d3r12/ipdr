<script setup lang="ts">
import { ref } from 'vue'
import { useRuntimeConfig } from '#app'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'
const firNo = ref('')
const file = ref<File | null>(null)
const preserveDuplicates = ref(false)
const bypassCloudflare = ref(false)
const message = ref('')
const runDir = ref('')
const uploading = ref(false)

function onChange(e: Event) {
  const target = e.target as HTMLInputElement
  file.value = target.files?.[0] || null
}

async function uploadFile() {
  if (!file.value || !firNo.value) {
    message.value = 'FIR number and file are required'
    return
  }
  
  uploading.value = true
  message.value = 'Uploading...'
  
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('fir', firNo.value)
  formData.append('preserve_duplicates', preserveDuplicates.value.toString())
  formData.append('bypass_cloudflare', bypassCloudflare.value.toString())
  
  try {
    const response = await fetch(`${apiBase}/api/upload/`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error('Upload failed')
    }
    
    const data = await response.json()
    runDir.value = data.run_dir
    message.value = `File uploaded successfully! Rows: ${data.count_rows}, Unique IPs: ${data.unique_ips}`
    
    // Auto-redirect to IP lookup if Cloudflare bypass is enabled
    if (bypassCloudflare.value && data.unique_ips > 0) {
      message.value += ' - Redirecting to IP Lookup...'
      setTimeout(() => {
        navigateTo(`/ip-lookup?run_dir=${encodeURIComponent(data.run_dir)}&auto_start=true`)
      }, 2000)
    }
  } catch (error: any) {
    message.value = error?.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}

function startIPLookup() {
  if (!runDir.value) {
    message.value = 'Please upload a file first'
    return
  }
  navigateTo(`/ip-lookup?run_dir=${encodeURIComponent(runDir.value)}&auto_start=true`)
}

async function processBatches() {
  if (!runDir.value) { message.value = 'Upload first'; return }
  message.value = 'Processing InfoByIP CSVs...'
  try {
    const res:any = await $fetch(`${apiBase}/api/process`, { method: 'POST', params: { run_dir: runDir.value } })
    message.value = `Master ready. ${res.lookup_size} IPs enriched.`
  } catch (e:any) {
    message.value = e?.data?.detail || 'Process failed (ensure infobyip_batch_*.csv are in the run folder)'
  }
}

function downloadExcel() {
  if (!runDir.value) { message.value = 'Upload/process first'; return }
  window.open(`${apiBase}/api/export?run_dir=${encodeURIComponent(runDir.value)}`, '_blank')
}

async function checkStatus() {
  if (!runDir.value) return
  const s:any = await $fetch(`${apiBase}/api/status`, { params: { run_dir: runDir.value } })
  status.value = s
  if (s?.state === 'ready') {
    clearInterval(pollTimer)
    pollTimer = null
    message.value = 'Master Excel ready.'
  } else if (s?.state === 'fetching') {
    message.value = `Fetching ${s.batches_fetched}/${s.batches_total} batches...`
  } else if (s?.state === 'merging') {
    message.value = 'Merging results...'
  }
}

function startPolling() {
  clearInterval(pollTimer)
  pollTimer = setInterval(checkStatus, 3000)
}
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-slate-200">
    <nav class="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-400">📤 Upload HTML Log</h1>
        <NuxtLink to="/" class="text-slate-400 hover:text-slate-200">← Back to Dashboard</NuxtLink>
      </div>
    </nav>
    
    <div class="p-6 max-w-2xl mx-auto">
      <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h2 class="text-xl font-bold mb-4">Upload Subscriber HTML</h2>
        <p class="text-slate-400 mb-6">Upload Google subscriber HTML files for IP extraction and processing</p>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-2">FIR Number</label>
            <input 
              v-model="firNo" 
              class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded focus:border-blue-500 focus:outline-none" 
              placeholder="e.g., FIR/2025/1234" 
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-2">HTML File</label>
            <input 
              type="file" 
              accept="text/html,.html" 
              @change="onChange" 
              class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
            />
            <p v-if="file" class="text-sm text-slate-400 mt-2">Selected: {{ file.name }}</p>
          </div>
          
          <div class="flex items-center space-x-3 p-4 bg-slate-900 border border-slate-700 rounded">
            <input 
              type="checkbox" 
              id="preserveDuplicates" 
              v-model="preserveDuplicates"
              class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label for="preserveDuplicates" class="text-sm font-medium cursor-pointer">
              <span class="text-slate-200">Preserve duplicates</span>
              <span class="block text-xs text-slate-400 mt-1">
                Keep duplicate IPs in batch files (slower but maintains original structure)
              </span>
            </label>
          </div>
          
          <div class="flex items-center space-x-3 p-4 bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-700/50 rounded">
            <input 
              type="checkbox" 
              id="bypassCloudflare" 
              v-model="bypassCloudflare"
              class="w-4 h-4 text-orange-600 bg-slate-800 border-orange-600 rounded focus:ring-orange-500 focus:ring-2"
            />
            <label for="bypassCloudflare" class="text-sm font-medium cursor-pointer">
              <div class="flex items-center space-x-2">
                <span class="text-orange-400">🔥 Bypass Cloudflare</span>
                <span class="px-2 py-0.5 bg-orange-600 text-white text-xs rounded-full font-bold">UNLIMITED</span>
              </div>
              <span class="block text-xs text-orange-300 mt-1">
                Use advanced anti-detection to bypass Cloudflare protection for unlimited InfoByIP access
              </span>
              <span class="block text-xs text-orange-400/70 mt-1">
                ⚡ Slower but bypasses rate limits • 🎯 Best for large datasets • 🔒 Stealth mode enabled
              </span>
            </label>
          </div>
          
          <button 
            @click="uploadFile" 
            :disabled="uploading"
            class="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {{ uploading ? 'Uploading...' : 'Upload & Extract' }}
          </button>
          
          <div v-if="message" class="p-4 bg-slate-900 border border-slate-700 rounded">
            <p class="text-sm">{{ message }}</p>
          </div>
          
          <div v-if="runDir" class="p-4 bg-slate-900 border border-green-700 rounded">
            <p class="text-sm text-green-400 font-medium mb-2">✓ Upload Successful</p>
            <p class="text-xs text-slate-400 mb-3">Run Directory: {{ runDir }}</p>
            
            <!-- IP Lookup Button -->
            <button 
              @click="startIPLookup"
              class="w-full px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded font-medium transition flex items-center justify-center space-x-2"
            >
              <span>🔍</span>
              <span>Start Unlimited IP Lookup</span>
              <span class="px-2 py-0.5 bg-white/20 text-xs rounded-full">NEW</span>
            </button>
            
            <p class="text-xs text-green-300 mt-2 text-center">
              ⚡ Real-time progress • 🎯 Hacker terminal UI • 🚀 Auto-bypass Cloudflare
            </p>
          </div>
        </div>
        
        <div class="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded">
          <p class="text-sm text-blue-300">
            <strong>Note:</strong> After upload, the system will automatically extract IP activity data. 
            For full enrichment, ensure InfoByIP CSVs are placed in the run folder.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
