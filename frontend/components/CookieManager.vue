<template>
  <div class="cookie-manager">
    <!-- Cookie Status Badge -->
    <div class="cookie-status-badge" :class="statusClass">
      <span class="status-icon">{{ statusIcon }}</span>
      <span class="status-text">{{ statusText }}</span>
      <button @click="showModal = true" class="btn-manage">
        🍪 Manage
      </button>
    </div>

    <!-- Cookie Management Modal -->
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>🍪 Cookie Management</h2>
          <button @click="showModal = false" class="btn-close">✕</button>
        </div>

        <div class="modal-body">
          <!-- Current Status -->
          <div class="status-section">
            <h3>Current Status</h3>
            <div class="status-card" :class="statusClass">
              <div class="status-info">
                <span class="status-icon-large">{{ statusIcon }}</span>
                <div>
                  <p class="status-message">{{ cookieStatus.message || 'Loading...' }}</p>
                  <p v-if="cookieStatus.expiry_time" class="expiry-info">
                    Expires: {{ formatExpiry(cookieStatus.expiry_time) }}
                  </p>
                </div>
              </div>
              <button @click="validateCookies" class="btn-validate" :disabled="validating">
                {{ validating ? '🔄 Validating...' : '🔍 Validate' }}
              </button>
            </div>
          </div>

          <!-- Upload Section -->
          <div class="upload-section">
            <h3>Upload New Cookies</h3>
            <div class="upload-area">
              <input
                type="file"
                ref="fileInput"
                accept=".json"
                @change="handleFileSelect"
                style="display: none"
              />
              <button @click="$refs.fileInput.click()" class="btn-upload">
                📁 Select Cookie File
              </button>
              <p v-if="selectedFile" class="file-name">{{ selectedFile.name }}</p>
              <button
                v-if="selectedFile"
                @click="uploadCookies"
                class="btn-upload-confirm"
                :disabled="uploading"
              >
                {{ uploading ? '⏳ Uploading...' : '✅ Upload & Validate' }}
              </button>
            </div>
            <p v-if="uploadMessage" class="upload-message" :class="uploadMessageClass">
              {{ uploadMessage }}
            </p>
          </div>

          <!-- Instructions -->
          <div class="instructions-section">
            <h3>📖 How to Export Cookies</h3>
            <div class="instructions-steps">
              <div class="step">
                <span class="step-number">1</span>
                <div class="step-content">
                  <h4>Install EditThisCookie Extension</h4>
                  <p>Add the extension to Chrome</p>
                  <a href="https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg" target="_blank" class="btn-link">
                    Open Chrome Web Store
                  </a>
                </div>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <div class="step-content">
                  <h4>Visit InfoByIP & Solve Captcha</h4>
                  <p>Go to InfoByIP and complete the Cloudflare challenge</p>
                  <a href="https://www.infobyip.com/ip-8.8.8.8.html" target="_blank" class="btn-link">
                    Open InfoByIP
                  </a>
                </div>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <div class="step-content">
                  <h4>Export Cookies</h4>
                  <p>Click EditThisCookie icon → Click Export button</p>
                  <p class="note">Cookies will be copied to clipboard</p>
                </div>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <div class="step-content">
                  <h4>Save as JSON File</h4>
                  <p>Paste into text file and save as: <code>infobyip_cookies.json</code></p>
                </div>
              </div>
              <div class="step">
                <span class="step-number">5</span>
                <div class="step-content">
                  <h4>Upload Here</h4>
                  <p>Use the upload button above to upload your cookie file</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRuntimeConfig } from '#app'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const showModal = ref(false)
const cookieStatus = ref({})
const selectedFile = ref(null)
const uploading = ref(false)
const validating = ref(false)
const uploadMessage = ref('')
const uploadMessageClass = ref('')

const statusClass = computed(() => {
  if (!cookieStatus.value.cookies_loaded) return 'status-none'
  if (cookieStatus.value.needs_refresh) return 'status-expired'
  if (cookieStatus.value.cookies_valid) return 'status-valid'
  return 'status-invalid'
})

const statusIcon = computed(() => {
  if (!cookieStatus.value.cookies_loaded) return '⚪'
  if (cookieStatus.value.needs_refresh) return '❌'
  if (cookieStatus.value.cookies_valid) return '✅'
  return '⚠️'
})

const statusText = computed(() => {
  if (!cookieStatus.value.cookies_loaded) return 'No Cookies'
  if (cookieStatus.value.needs_refresh) return 'Cookies Expired'
  if (cookieStatus.value.cookies_valid) return 'Cookies Valid'
  return 'Cookies Invalid'
})

const fetchStatus = async () => {
  try {
    const response = await fetch(`${apiBase}/api/cookies/status`)
    if (response.ok) {
      cookieStatus.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching cookie status:', error)
  }
}

const validateCookies = async () => {
  validating.value = true
  try {
    const response = await fetch(`${apiBase}/api/cookies/validate`, {
      method: 'POST'
    })
    if (response.ok) {
      const result = await response.json()
      cookieStatus.value = result.status
      uploadMessage.value = result.message
      uploadMessageClass.value = result.valid ? 'success' : 'error'
    }
  } catch (error) {
    console.error('Error validating cookies:', error)
    uploadMessage.value = 'Validation failed'
    uploadMessageClass.value = 'error'
  } finally {
    validating.value = false
  }
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
  uploadMessage.value = ''
}

const uploadCookies = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  uploadMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await fetch(`${apiBase}/api/cookies/upload`, {
      method: 'POST',
      body: formData
    })

    const result = await response.json()

    if (response.ok) {
      uploadMessage.value = '✅ Cookies uploaded and validated successfully!'
      uploadMessageClass.value = 'success'
      cookieStatus.value = result.status
      selectedFile.value = null
      
      // Emit event to parent
      emit('cookiesUpdated', result.status)
    } else {
      uploadMessage.value = `❌ ${result.detail || 'Upload failed'}`
      uploadMessageClass.value = 'error'
    }
  } catch (error) {
    console.error('Error uploading cookies:', error)
    uploadMessage.value = '❌ Upload failed. Please try again.'
    uploadMessageClass.value = 'error'
  } finally {
    uploading.value = false
  }
}

const formatExpiry = (expiryTime) => {
  const expiry = new Date(expiryTime)
  const now = new Date()
  const hoursRemaining = (expiry - now) / (1000 * 60 * 60)
  
  if (hoursRemaining < 0) return 'Expired'
  if (hoursRemaining < 1) return `${Math.round(hoursRemaining * 60)} minutes`
  return `${Math.round(hoursRemaining)} hours`
}

const emit = defineEmits(['cookiesUpdated'])

onMounted(() => {
  fetchStatus()
  // Refresh status every 5 minutes
  setInterval(fetchStatus, 5 * 60 * 1000)
})
</script>

<style scoped>
.cookie-manager {
  position: relative;
}

.cookie-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid;
}

.status-valid {
  background: rgba(34, 197, 94, 0.1);
  border-color: #22c55e;
  color: #22c55e;
}

.status-expired {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.status-invalid {
  background: rgba(251, 191, 36, 0.1);
  border-color: #fbbf24;
  color: #fbbf24;
}

.status-none {
  background: rgba(156, 163, 175, 0.1);
  border-color: #9ca3af;
  color: #9ca3af;
}

.btn-manage {
  padding: 4px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  color: #3b82f6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-manage:hover {
  background: rgba(59, 130, 246, 0.2);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #1a1a1a;
  border-radius: 12px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid #333;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0;
  color: #fff;
  font-size: 24px;
}

.btn-close {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.modal-body {
  padding: 20px;
}

.status-section,
.upload-section,
.instructions-section {
  margin-bottom: 24px;
}

.status-section h3,
.upload-section h3,
.instructions-section h3 {
  color: #fff;
  margin-bottom: 12px;
  font-size: 16px;
}

.status-card {
  padding: 16px;
  border-radius: 8px;
  border: 2px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon-large {
  font-size: 32px;
}

.status-message {
  color: #fff;
  font-weight: 500;
  margin: 0;
}

.expiry-info {
  color: #999;
  font-size: 12px;
  margin: 4px 0 0 0;
}

.btn-validate {
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  color: #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-validate:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
}

.btn-validate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 2px dashed #444;
}

.btn-upload,
.btn-upload-confirm {
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-upload {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  color: #3b82f6;
}

.btn-upload:hover {
  background: rgba(59, 130, 246, 0.2);
}

.btn-upload-confirm {
  background: #22c55e;
  border: none;
  color: #fff;
}

.btn-upload-confirm:hover:not(:disabled) {
  background: #16a34a;
}

.btn-upload-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-name {
  color: #999;
  font-size: 12px;
  margin: 0;
}

.upload-message {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.upload-message.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid #22c55e;
  color: #22c55e;
}

.upload-message.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #ef4444;
  color: #ef4444;
}

.instructions-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step {
  display: flex;
  gap: 12px;
}

.step-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  color: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step-content h4 {
  color: #fff;
  margin: 0 0 4px 0;
  font-size: 14px;
}

.step-content p {
  color: #999;
  margin: 0;
  font-size: 13px;
}

.step-content .note {
  color: #666;
  font-style: italic;
  margin-top: 4px;
}

.step-content code {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  color: #3b82f6;
  font-size: 12px;
}

.btn-link {
  display: inline-block;
  margin-top: 8px;
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid #3b82f6;
  color: #3b82f6;
  text-decoration: none;
  border-radius: 4px;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-link:hover {
  background: rgba(59, 130, 246, 0.2);
}
</style>
