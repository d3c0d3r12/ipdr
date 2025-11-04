<template>
  <div class="cookie-service-dashboard">
    <div class="dashboard-card">
      <div class="card-header">
        <h3>🍪 Cookie Auto-Refresh Service</h3>
        <div class="service-status" :class="serviceStatusClass">
          <span class="status-dot"></span>
          {{ serviceStatus }}
        </div>
      </div>

      <div class="card-body">
        <!-- Service Info -->
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Status:</span>
            <span class="info-value">{{ serviceData.running ? '🟢 Running' : '🔴 Stopped' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Auto-Refresh:</span>
            <span class="info-value">{{ serviceData.auto_refresh_enabled ? '✅ Enabled' : '⏸️ Disabled' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Last Refresh:</span>
            <span class="info-value">{{ formatTime(serviceData.last_refresh) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Next Refresh:</span>
            <span class="info-value">{{ formatTime(serviceData.next_refresh) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Total Refreshes:</span>
            <span class="info-value">{{ serviceData.refresh_count || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Errors:</span>
            <span class="info-value">{{ serviceData.error_count || 0 }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="actions">
          <button
            @click="manualRefresh"
            class="btn btn-primary"
            :disabled="refreshing"
          >
            {{ refreshing ? '⏳ Refreshing...' : '🔄 Refresh Now' }}
          </button>
          
          <button
            v-if="serviceData.auto_refresh_enabled"
            @click="toggleAutoRefresh"
            class="btn btn-secondary"
          >
            ⏸️ Disable Auto-Refresh
          </button>
          <button
            v-else
            @click="toggleAutoRefresh"
            class="btn btn-success"
          >
            ▶️ Enable Auto-Refresh
          </button>
        </div>

        <!-- Status Message -->
        <div v-if="statusMessage" class="status-message" :class="statusMessageClass">
          {{ statusMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRuntimeConfig } from '#app'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const serviceData = ref({})
const refreshing = ref(false)
const statusMessage = ref('')
const statusMessageClass = ref('')
let refreshInterval = null

const serviceStatus = computed(() => {
  if (!serviceData.value.running) return 'Service Stopped'
  if (!serviceData.value.auto_refresh_enabled) return 'Manual Mode'
  return 'Auto-Refresh Active'
})

const serviceStatusClass = computed(() => {
  if (!serviceData.value.running) return 'status-stopped'
  if (!serviceData.value.auto_refresh_enabled) return 'status-manual'
  return 'status-active'
})

const fetchServiceStatus = async () => {
  try {
    const response = await fetch(`${apiBase}/api/cookies/service/status`)
    if (response.ok) {
      serviceData.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching service status:', error)
  }
}

const manualRefresh = async () => {
  refreshing.value = true
  statusMessage.value = ''

  try {
    const response = await fetch(`${apiBase}/api/cookies/service/refresh`, {
      method: 'POST'
    })

    const result = await response.json()

    if (response.ok) {
      statusMessage.value = `✅ ${result.message}`
      statusMessageClass.value = 'success'
      await fetchServiceStatus()
    } else {
      statusMessage.value = `❌ ${result.detail || 'Refresh failed'}`
      statusMessageClass.value = 'error'
    }
  } catch (error) {
    console.error('Error refreshing:', error)
    statusMessage.value = '❌ Failed to refresh cookies'
    statusMessageClass.value = 'error'
  } finally {
    refreshing.value = false
  }
}

const toggleAutoRefresh = async () => {
  try {
    const endpoint = serviceData.value.auto_refresh_enabled ? 'disable' : 'enable'
    const response = await fetch(`${apiBase}/api/cookies/service/${endpoint}`, {
      method: 'POST'
    })

    if (response.ok) {
      const result = await response.json()
      statusMessage.value = `✅ ${result.message}`
      statusMessageClass.value = 'success'
      await fetchServiceStatus()
    }
  } catch (error) {
    console.error('Error toggling auto-refresh:', error)
    statusMessage.value = '❌ Failed to toggle auto-refresh'
    statusMessageClass.value = 'error'
  }
}

const formatTime = (isoString) => {
  if (!isoString) return 'Never'
  
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = date - now
  const diffMins = Math.round(diffMs / 60000)
  const diffHours = Math.round(diffMs / 3600000)
  
  if (diffMins < -60) {
    return `${Math.abs(Math.round(diffMins / 60))} hours ago`
  } else if (diffMins < 0) {
    return `${Math.abs(diffMins)} minutes ago`
  } else if (diffMins < 60) {
    return `in ${diffMins} minutes`
  } else {
    return `in ${diffHours} hours`
  }
}

onMounted(() => {
  fetchServiceStatus()
  // Refresh status every 30 seconds
  refreshInterval = setInterval(fetchServiceStatus, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.cookie-service-dashboard {
  padding: 20px;
}

.dashboard-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  border: 1px solid #333;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #333;
  background: rgba(255, 255, 255, 0.02);
}

.card-header h3 {
  margin: 0;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.status-active {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid #22c55e;
}

.status-active .status-dot {
  background: #22c55e;
}

.status-manual {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.status-manual .status-dot {
  background: #3b82f6;
}

.status-stopped {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.status-stopped .status-dot {
  background: #ef4444;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.card-body {
  padding: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  color: #999;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid #444;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-success {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
}

.btn-success:hover {
  background: linear-gradient(135deg, #16a34a, #15803d);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
}

.status-message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-top: 16px;
}

.status-message.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid #22c55e;
  color: #22c55e;
}

.status-message.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #ef4444;
  color: #ef4444;
}
</style>
