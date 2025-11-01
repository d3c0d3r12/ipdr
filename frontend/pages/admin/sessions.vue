<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRuntimeConfig } from '#app'
import { UserGroupIcon, GlobeAltIcon, DevicePhoneMobileIcon, ComputerDesktopIcon, ClockIcon, MapPinIcon } from '@heroicons/vue/24/outline'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const activeSessions = ref([])
const sessionStats = ref({
  total_sessions: 0,
  unique_visitors: 0,
  authenticated_sessions: 0,
  avg_duration_seconds: 0,
  device_breakdown: {},
  top_countries: []
})
const recentActivities = ref([])
const loading = ref(true)
const selectedDays = ref(7)

const formatDuration = (seconds: number) => {
  if (!seconds) return '0s'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m ${secs}s`
  return `${secs}s`
}

const formatIdleTime = (seconds: number) => {
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${Math.floor(seconds / 3600)}h ago`
}

const getDeviceIcon = (deviceType: string) => {
  if (deviceType === 'mobile') return DevicePhoneMobileIcon
  if (deviceType === 'tablet') return DevicePhoneMobileIcon
  return ComputerDesktopIcon
}

const fetchActiveSessions = async () => {
  try {
    const response = await fetch(`${apiBase}/api/tracking/sessions/active`)
    const data = await response.json()
    activeSessions.value = data.sessions || []
  } catch (error) {
    console.error('Error fetching active sessions:', error)
  }
}

const fetchSessionStats = async () => {
  try {
    const response = await fetch(`${apiBase}/api/tracking/sessions/stats?days=${selectedDays.value}`)
    const data = await response.json()
    sessionStats.value = data
  } catch (error) {
    console.error('Error fetching session stats:', error)
  }
}

const fetchRecentActivities = async () => {
  try {
    const response = await fetch(`${apiBase}/api/tracking/activities/recent?limit=20`)
    const data = await response.json()
    recentActivities.value = data.activities || []
  } catch (error) {
    console.error('Error fetching recent activities:', error)
  }
}

const loadData = async () => {
  loading.value = true
  await Promise.all([
    fetchActiveSessions(),
    fetchSessionStats(),
    fetchRecentActivities()
  ])
  loading.value = false
}

onMounted(() => {
  loadData()
  // Auto-refresh every 30 seconds
  setInterval(loadData, 30000)
})

const deviceBreakdownArray = computed(() => {
  return Object.entries(sessionStats.value.device_breakdown || {}).map(([device, count]) => ({
    device,
    count
  }))
})
</script>

<template>
  <div class="min-h-screen bg-dark-500 text-slate-200">
    <!-- Navigation -->
    <nav class="bg-gradient-to-r from-dark-300 via-dark-200 to-dark-300 border-b border-cyber-500/30 px-6 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <NuxtLink to="/" class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-br from-cyber-500 to-blue-600 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-white">User Session Tracking</h1>
              <p class="text-xs text-slate-400">Admin Dashboard</p>
            </div>
          </NuxtLink>
        </div>
        <NuxtLink to="/" class="text-slate-400 hover:text-slate-200 transition">
          ← Back to Dashboard
        </NuxtLink>
      </div>
    </nav>

    <div class="p-6 space-y-6">
      <!-- Stats Overview -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="cyber-card">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-slate-400 uppercase tracking-wide mb-2">Total Sessions</div>
              <div class="text-3xl font-bold text-white">{{ sessionStats.total_sessions.toLocaleString() }}</div>
              <div class="text-xs text-slate-500 mt-1">Last {{ selectedDays }} days</div>
            </div>
            <div class="w-12 h-12 bg-gradient-to-br from-cyber-500 to-blue-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-6 h-6 text-cyber-400" />
            </div>
          </div>
        </div>

        <div class="cyber-card">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-slate-400 uppercase tracking-wide mb-2">Unique Visitors</div>
              <div class="text-3xl font-bold text-white">{{ sessionStats.unique_visitors.toLocaleString() }}</div>
              <div class="text-xs text-slate-500 mt-1">By IP address</div>
            </div>
            <div class="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <GlobeAltIcon class="w-6 h-6 text-purple-400" />
            </div>
          </div>
        </div>

        <div class="cyber-card">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-slate-400 uppercase tracking-wide mb-2">Authenticated</div>
              <div class="text-3xl font-bold text-white">{{ sessionStats.authenticated_sessions }}</div>
              <div class="text-xs text-slate-500 mt-1">Logged in users</div>
            </div>
            <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <UserGroupIcon class="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        <div class="cyber-card">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm text-slate-400 uppercase tracking-wide mb-2">Avg Duration</div>
              <div class="text-3xl font-bold text-white">{{ formatDuration(sessionStats.avg_duration_seconds) }}</div>
              <div class="text-xs text-slate-500 mt-1">Per session</div>
            </div>
            <div class="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 bg-opacity-20 rounded-lg flex items-center justify-center">
              <ClockIcon class="w-6 h-6 text-orange-400" />
            </div>
          </div>
        </div>
      </div>

      <!-- Device & Country Breakdown -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Device Breakdown -->
        <div class="cyber-card">
          <h3 class="text-xl font-bold text-white mb-4 flex items-center">
            <ComputerDesktopIcon class="w-6 h-6 mr-2 text-cyber-400" />
            Device Breakdown
          </h3>
          <div class="space-y-3">
            <div v-for="item in deviceBreakdownArray" :key="item.device" class="flex items-center justify-between p-3 bg-dark-300 rounded-lg">
              <div class="flex items-center space-x-3">
                <component :is="getDeviceIcon(item.device)" class="w-5 h-5 text-cyber-400" />
                <span class="capitalize text-slate-200">{{ item.device || 'Unknown' }}</span>
              </div>
              <div class="flex items-center space-x-3">
                <div class="text-sm text-slate-400">{{ item.count }} sessions</div>
                <div class="w-16 h-2 bg-dark-400 rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-cyber-500 to-blue-600" 
                       :style="{ width: `${(item.count / sessionStats.total_sessions) * 100}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Countries -->
        <div class="cyber-card">
          <h3 class="text-xl font-bold text-white mb-4 flex items-center">
            <MapPinIcon class="w-6 h-6 mr-2 text-cyber-400" />
            Top Countries
          </h3>
          <div class="space-y-3">
            <div v-for="(country, index) in sessionStats.top_countries.slice(0, 5)" :key="index" 
                 class="flex items-center justify-between p-3 bg-dark-300 rounded-lg">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-gradient-to-br from-cyber-500 to-blue-600 bg-opacity-20 rounded-full flex items-center justify-center text-xs font-bold">
                  {{ index + 1 }}
                </div>
                <span class="text-slate-200">{{ country.country }}</span>
              </div>
              <div class="flex items-center space-x-3">
                <div class="text-sm text-slate-400">{{ country.count }} visits</div>
                <div class="w-16 h-2 bg-dark-400 rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-purple-500 to-pink-600" 
                       :style="{ width: `${(country.count / sessionStats.total_sessions) * 100}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Sessions -->
      <div class="cyber-card">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-white flex items-center">
            <div class="w-3 h-3 bg-success rounded-full mr-3 animate-pulse"></div>
            Active Sessions
            <span class="ml-3 text-sm font-normal text-slate-400">({{ activeSessions.length }} online)</span>
          </h3>
          <button @click="loadData" class="px-4 py-2 bg-cyber-600 hover:bg-cyber-500 rounded-lg text-sm font-semibold transition">
            Refresh
          </button>
        </div>

        <div v-if="loading" class="text-center py-8 text-slate-400">
          <div class="spinner mx-auto mb-4"></div>
          Loading sessions...
        </div>

        <div v-else-if="activeSessions.length === 0" class="text-center py-8 text-slate-400">
          No active sessions
        </div>

        <div v-else class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>IP Address</th>
                <th>Location</th>
                <th>Device</th>
                <th>Browser</th>
                <th>Session Start</th>
                <th>Last Activity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in activeSessions" :key="session.session_id">
                <td>
                  <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-gradient-to-br from-cyber-500 to-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {{ session.username ? session.username.charAt(0).toUpperCase() : '?' }}
                    </div>
                    <span class="font-medium">{{ session.username || 'Anonymous' }}</span>
                  </div>
                </td>
                <td class="font-mono text-cyber-400">{{ session.ip_address }}</td>
                <td>{{ session.location }}</td>
                <td>
                  <div class="flex items-center space-x-2">
                    <component :is="getDeviceIcon(session.device)" class="w-4 h-4 text-slate-400" />
                    <span class="capitalize">{{ session.device }}</span>
                  </div>
                </td>
                <td>{{ session.browser }}</td>
                <td class="text-sm text-slate-400">{{ new Date(session.session_start).toLocaleString() }}</td>
                <td class="text-sm text-slate-400">{{ formatIdleTime(session.idle_seconds) }}</td>
                <td>
                  <span class="badge badge-success">Active</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Activities -->
      <div class="cyber-card">
        <h3 class="text-xl font-bold text-white mb-6 flex items-center">
          <ClockIcon class="w-6 h-6 mr-2 text-cyber-400" />
          Recent Activities
        </h3>

        <div class="space-y-2">
          <div v-for="activity in recentActivities.slice(0, 10)" :key="activity.id"
               class="flex items-center justify-between p-3 bg-dark-300 rounded-lg hover:bg-dark-200 transition">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <span class="badge" :class="{
                  'badge-success': activity.status === 'success',
                  'badge-danger': activity.status === 'error',
                  'badge-warning': activity.status === 'pending'
                }">
                  {{ activity.activity_type }}
                </span>
                <span class="text-sm text-slate-300">{{ activity.description || activity.page_url }}</span>
              </div>
            </div>
            <div class="text-xs text-slate-500">
              {{ new Date(activity.timestamp).toLocaleString() }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(6, 182, 212, 0.2);
  border-top-color: #06b6d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
