<template>
  <div class="ip-lookup-terminal">
    <!-- Terminal Header -->
    <div class="terminal-header">
      <div class="header-dots">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
      </div>
      <div class="header-title">
        <span class="icon">🔍</span>
        UNLIMITED IP LOOKUP SYSTEM
        <span class="blink">_</span>
      </div>
      <div class="header-status" :class="statusClass">
        {{ statusText }}
      </div>
    </div>

    <!-- Terminal Body -->
    <div class="terminal-body" ref="terminalBody">
      <!-- Matrix Rain Background (optional) -->
      <canvas ref="matrixCanvas" class="matrix-bg"></canvas>

      <!-- Terminal Output -->
      <div class="terminal-output">
        <div v-for="(line, index) in terminalLines" :key="index" class="terminal-line" :class="line.type">
          <span class="line-prefix">{{ line.prefix }}</span>
          <span class="line-content" v-html="line.content"></span>
        </div>

        <!-- Progress Bar -->
        <div v-if="isProcessing && progress > 0" class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }">
              <span class="progress-text">{{ progress }}%</span>
            </div>
          </div>
          <div class="progress-info">
            <span>{{ currentIP || 'Processing...' }}</span>
            <span v-if="totalIPs > 0">{{ processedIPs }}/{{ totalIPs }} IPs</span>
          </div>
        </div>

        <!-- Loading Animation -->
        <div v-if="isProcessing" class="loading-animation">
          <span class="spinner">⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏</span>
          <span class="loading-text">{{ loadingText }}</span>
        </div>
      </div>
    </div>

    <!-- Terminal Footer -->
    <div class="terminal-footer">
      <div class="footer-stats">
        <span v-if="totalIPs > 0">📊 Total: {{ totalIPs }}</span>
        <span v-if="successCount > 0">✅ Success: {{ successCount }}</span>
        <span v-if="errorCount > 0">❌ Errors: {{ errorCount }}</span>
        <span v-if="elapsedTime">⏱️ Time: {{ elapsedTime }}</span>
      </div>
      <div class="footer-actions">
        <button v-if="!isProcessing && !isComplete" @click="startLookup" class="btn-start">
          🚀 Start Lookup
        </button>
        <button v-if="isComplete" @click="downloadResults" class="btn-download">
          💾 Download Results
        </button>
        <button v-if="isProcessing" @click="cancelLookup" class="btn-cancel">
          ⏹️ Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  runDir: {
    type: String,
    required: true
  },
  autoStart: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['complete', 'error'])

// State
const terminalLines = ref([])
const isProcessing = ref(false)
const isComplete = ref(false)
const progress = ref(0)
const totalIPs = ref(0)
const processedIPs = ref(0)
const successCount = ref(0)
const errorCount = ref(0)
const currentIP = ref('')
const loadingText = ref('Initializing...')
const elapsedTime = ref('')
const csvPath = ref('')
const jsonPath = ref('')
const eventSource = ref(null)
const startTime = ref(null)
const timerInterval = ref(null)
const matrixCanvas = ref(null)
const terminalBody = ref(null)
const spinnerIndex = ref(0)
const spinnerInterval = ref(null)

// Computed
const statusClass = computed(() => {
  if (isComplete.value) return 'status-complete'
  if (isProcessing.value) return 'status-processing'
  return 'status-idle'
})

const statusText = computed(() => {
  if (isComplete.value) return '✅ COMPLETE'
  if (isProcessing.value) return '⚡ PROCESSING'
  return '⏸️ IDLE'
})

// Methods
const addLine = (content, type = 'info', prefix = '$') => {
  terminalLines.value.push({
    content,
    type,
    prefix,
    timestamp: new Date().toLocaleTimeString()
  })
  nextTick(() => {
    scrollToBottom()
  })
}

const scrollToBottom = () => {
  if (terminalBody.value) {
    terminalBody.value.scrollTop = terminalBody.value.scrollHeight
  }
}

const updateTimer = () => {
  if (startTime.value) {
    const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    elapsedTime.value = `${minutes}:${seconds.toString().padStart(2, '0')}`
  }
}

const updateSpinner = () => {
  const spinners = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  spinnerIndex.value = (spinnerIndex.value + 1) % spinners.length
}

const startLookup = async () => {
  if (!props.runDir) {
    addLine('❌ Error: No run directory specified', 'error', '!')
    return
  }

  isProcessing.value = true
  isComplete.value = false
  progress.value = 0
  processedIPs.value = 0
  successCount.value = 0
  errorCount.value = 0
  startTime.value = Date.now()
  
  // Start timer
  timerInterval.value = setInterval(updateTimer, 1000)
  
  // Start spinner
  spinnerInterval.value = setInterval(updateSpinner, 100)

  addLine('═══════════════════════════════════════════════════════', 'header', '╔')
  addLine('    UNLIMITED IP LOOKUP SYSTEM v2.0', 'header', '║')
  addLine('    Powered by Enhanced Cloudflare Bypass', 'header', '║')
  addLine('═══════════════════════════════════════════════════════', 'header', '╚')
  addLine('')

  try {
    // Create EventSource for SSE
    const url = `http://localhost:8000/api/lookup/stream?run_dir=${encodeURIComponent(props.runDir)}`
    eventSource.value = new EventSource(url)

    eventSource.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleSSEMessage(data)
      } catch (e) {
        console.error('Failed to parse SSE message:', e)
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('SSE Error:', error)
      addLine('❌ Connection error. Retrying...', 'error', '!')
      if (eventSource.value.readyState === EventSource.CLOSED) {
        cleanup()
        addLine('❌ Lookup failed. Please try again.', 'error', '!')
        isProcessing.value = false
      }
    }

  } catch (error) {
    addLine(`❌ Error: ${error.message}`, 'error', '!')
    isProcessing.value = false
    cleanup()
  }
}

const handleSSEMessage = (data) => {
  switch (data.type) {
    case 'status':
      addLine(data.message, 'status', '>')
      loadingText.value = data.message
      if (data.progress !== undefined) {
        progress.value = data.progress
      }
      break

    case 'info':
      addLine(data.message, 'info', 'ℹ')
      if (data.total !== undefined) {
        totalIPs.value = data.total
      }
      break

    case 'progress':
      currentIP.value = data.ip
      processedIPs.value = data.current
      progress.value = data.progress
      loadingText.value = `Processing IP ${data.current}/${data.total}...`
      // Only add every 10th IP to avoid spam
      if (data.current % 10 === 0 || data.current === data.total) {
        addLine(data.message, 'progress', '→')
      }
      break

    case 'success':
      successCount.value++
      addLine(data.message, 'success', '✓')
      break

    case 'warning':
      addLine(data.message, 'warning', '⚠')
      break

    case 'error':
      errorCount.value++
      addLine(data.message, 'error', '✗')
      break

    case 'complete':
      progress.value = 100
      isProcessing.value = false
      isComplete.value = true
      csvPath.value = data.csv_path
      jsonPath.value = data.json_path
      addLine('')
      addLine('═══════════════════════════════════════════════════════', 'success', '╔')
      addLine(data.message, 'success', '║')
      addLine(`    Time Elapsed: ${data.elapsed_minutes?.toFixed(1)} minutes`, 'success', '║')
      addLine(`    CSV: ${data.csv_path}`, 'success', '║')
      addLine(`    JSON: ${data.json_path}`, 'success', '║')
      addLine('═══════════════════════════════════════════════════════', 'success', '╚')
      cleanup()
      emit('complete', { csv: data.csv_path, json: data.json_path })
      break

    case 'done':
      cleanup()
      break
  }
}

const cancelLookup = () => {
  addLine('⏹️ Lookup cancelled by user', 'warning', '!')
  cleanup()
  isProcessing.value = false
}

const cleanup = () => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
  if (spinnerInterval.value) {
    clearInterval(spinnerInterval.value)
    spinnerInterval.value = null
  }
}

const downloadResults = () => {
  if (csvPath.value) {
    window.open(csvPath.value, '_blank')
  }
}

// Matrix Rain Animation
const initMatrix = () => {
  const canvas = matrixCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight

  const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'
  const fontSize = 14
  const columns = canvas.width / fontSize
  const drops = Array(Math.floor(columns)).fill(1)

  const draw = () => {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.fillStyle = '#0F0'
    ctx.font = fontSize + 'px monospace'

    for (let i = 0; i < drops.length; i++) {
      const text = chars[Math.floor(Math.random() * chars.length)]
      ctx.fillText(text, i * fontSize, drops[i] * fontSize)

      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0
      }
      drops[i]++
    }
  }

  const interval = setInterval(draw, 33)
  return () => clearInterval(interval)
}

// Lifecycle
onMounted(() => {
  const cleanupMatrix = initMatrix()
  
  if (props.autoStart) {
    setTimeout(startLookup, 500)
  }

  onUnmounted(() => {
    cleanup()
    if (cleanupMatrix) cleanupMatrix()
  })
})
</script>

<style scoped>
.ip-lookup-terminal {
  background: #000;
  border: 2px solid #0f0;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
  font-family: 'Courier New', monospace;
  color: #0f0;
  overflow: hidden;
  position: relative;
}

/* Terminal Header */
.terminal-header {
  background: linear-gradient(to bottom, #1a1a1a, #000);
  border-bottom: 1px solid #0f0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }

.header-title {
  flex: 1;
  text-align: center;
  font-weight: bold;
  font-size: 14px;
  letter-spacing: 2px;
}

.header-title .icon {
  margin-right: 8px;
}

.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.header-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
}

.status-idle {
  background: #333;
  color: #999;
}

.status-processing {
  background: #ff6b00;
  color: #fff;
  animation: pulse 1.5s infinite;
}

.status-complete {
  background: #0f0;
  color: #000;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* Terminal Body */
.terminal-body {
  position: relative;
  height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: #000;
}

.matrix-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
  pointer-events: none;
}

.terminal-output {
  position: relative;
  z-index: 1;
}

.terminal-line {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
}

.line-prefix {
  margin-right: 8px;
  font-weight: bold;
  min-width: 20px;
}

.line-content {
  flex: 1;
}

/* Line Types */
.terminal-line.header {
  color: #0ff;
  font-weight: bold;
}

.terminal-line.info {
  color: #0f0;
}

.terminal-line.status {
  color: #ff0;
}

.terminal-line.progress {
  color: #0ff;
}

.terminal-line.success {
  color: #0f0;
  font-weight: bold;
}

.terminal-line.warning {
  color: #ff0;
}

.terminal-line.error {
  color: #f00;
}

/* Progress Bar */
.progress-container {
  margin: 16px 0;
  padding: 12px;
  background: rgba(0, 255, 0, 0.1);
  border: 1px solid #0f0;
  border-radius: 4px;
}

.progress-bar {
  height: 24px;
  background: #111;
  border: 1px solid #0f0;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0f0, #0ff);
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  color: #000;
  font-weight: bold;
  font-size: 12px;
  position: relative;
  z-index: 1;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #0ff;
}

/* Loading Animation */
.loading-animation {
  margin: 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0ff;
}

.spinner {
  animation: spin 1s linear infinite;
  font-size: 16px;
}

@keyframes spin {
  0% { content: '⠋'; }
  10% { content: '⠙'; }
  20% { content: '⠹'; }
  30% { content: '⠸'; }
  40% { content: '⠼'; }
  50% { content: '⠴'; }
  60% { content: '⠦'; }
  70% { content: '⠧'; }
  80% { content: '⠇'; }
  90% { content: '⠏'; }
  100% { content: '⠋'; }
}

/* Terminal Footer */
.terminal-footer {
  background: linear-gradient(to top, #1a1a1a, #000);
  border-top: 1px solid #0f0;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #0ff;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

button {
  padding: 8px 16px;
  border: 1px solid #0f0;
  background: #000;
  color: #0f0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}

button:hover {
  background: #0f0;
  color: #000;
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
}

.btn-start {
  border-color: #0f0;
  color: #0f0;
}

.btn-download {
  border-color: #0ff;
  color: #0ff;
}

.btn-cancel {
  border-color: #f00;
  color: #f00;
}

.btn-cancel:hover {
  background: #f00;
  color: #fff;
}

/* Scrollbar */
.terminal-body::-webkit-scrollbar {
  width: 8px;
}

.terminal-body::-webkit-scrollbar-track {
  background: #111;
}

.terminal-body::-webkit-scrollbar-thumb {
  background: #0f0;
  border-radius: 4px;
}

.terminal-body::-webkit-scrollbar-thumb:hover {
  background: #0ff;
}
</style>
