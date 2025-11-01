<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRuntimeConfig } from '#app'
import { GlobeAltIcon, ShieldCheckIcon, MapPinIcon, ExclamationTriangleIcon, ClockIcon, DocumentTextIcon, ChartBarIcon, UserGroupIcon } from '@heroicons/vue/24/outline'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'
const stats = ref({ total: 0, countries: 0, cities: 0, suspicious: 0 })
const recentActivity = ref([])
const loading = ref(true)
const currentTime = ref(new Date())

// Update time every second
setInterval(() => {
  currentTime.value = new Date()
}, 1000)

const formattedTime = computed(() => {
  return currentTime.value.toLocaleTimeString('en-IN', { hour12: false })
})

const formattedDate = computed(() => {
  return currentTime.value.toLocaleDateString('en-IN', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
})

onMounted(async () => {
  try {
    const response = await fetch(`${apiBase}/api/data/summary`)
    const data = await response.json()
    stats.value = data
    
    // Simulate recent activity
    recentActivity.value = [
      { time: '2 min ago', action: '205 IPs processed', type: 'success', icon: ShieldCheckIcon },
      { time: '15 min ago', action: 'FIR/2025/1234 uploaded', type: 'info', icon: DocumentTextIcon },
      { time: '1 hour ago', action: 'Suspicious activity detected', type: 'warning', icon: ExclamationTriangleIcon },
      { time: '2 hours ago', action: 'Export completed', type: 'success', icon: ChartBarIcon },
    ]
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    stats.value = { total: 12543, countries: 18, cities: 59, suspicious: 5 }
    recentActivity.value = [
      { time: '2 min ago', action: '205 IPs processed', type: 'success', icon: ShieldCheckIcon },
      { time: '15 min ago', action: 'FIR/2025/1234 uploaded', type: 'info', icon: DocumentTextIcon },
    ]
  } finally {
    loading.value = false
  }
})

const statCards = computed(() => [
  {
    icon: GlobeAltIcon,
    label: 'Total IP Records',
    value: stats.value.total,
    change: 12.5,
    trend: [100, 120, 115, 140, 135, 160, 155, 180],
    color: 'from-cyber-500 to-blue-600'
  },
  {
    icon: MapPinIcon,
    label: 'Countries Tracked',
    value: stats.value.countries,
    change: 5.2,
    trend: [10, 12, 11, 15, 14, 17, 16, 18],
    color: 'from-purple-500 to-pink-600'
  },
  {
    icon: ShieldCheckIcon,
    label: 'Cities Identified',
    value: stats.value.cities,
    change: 8.7,
    trend: [30, 35, 40, 42, 48, 52, 55, 59],
    color: 'from-green-500 to-emerald-600'
  },
  {
    icon: ExclamationTriangleIcon,
    label: 'Suspicious IPs',
    value: stats.value.suspicious,
    change: -2.3,
    trend: [8, 7, 9, 6, 7, 5, 6, 5],
    color: 'from-orange-500 to-red-600'
  },
])
</script>

<template>
  <div class="min-h-screen bg-dark-500 text-slate-200">
    <!-- Top Navigation Bar -->
    <nav class="bg-gradient-to-r from-dark-300 via-dark-200 to-dark-300 border-b border-cyber-500/30 px-6 py-4 backdrop-blur-cyber">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-br from-cyber-500 to-blue-600 rounded-lg flex items-center justify-center">
              <ShieldCheckIcon class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-white font-display tracking-wider">IPDR TRACKING HUB</h1>
              <p class="text-xs text-slate-400">Digital Forensics Intelligence System</p>
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-6">
          <div class="text-right">
            <div class="text-2xl font-mono font-bold text-cyber-400 glow-text">{{ formattedTime }}</div>
            <div class="text-xs text-slate-400">{{ formattedDate }}</div>
          </div>
          <div class="flex items-center space-x-2 px-4 py-2 bg-dark-400 rounded-lg border border-slate-700">
            <div class="w-2 h-2 bg-success rounded-full animate-pulse"></div>
            <span class="text-sm text-slate-300">System Online</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="p-6 space-y-6">
      <!-- Page Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-3xl font-bold text-white mb-2">Command Center</h2>
          <p class="text-slate-400">Real-time IP intelligence and threat monitoring</p>
        </div>
        <div class="flex space-x-3">
          <NuxtLink to="/upload" class="btn-cyber">
            <DocumentTextIcon class="w-5 h-5 mr-2" />
            Upload Evidence
          </NuxtLink>
          <NuxtLink to="/analytics" class="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition-all duration-300">
            <ChartBarIcon class="w-5 h-5 mr-2 inline" />
            Analytics
          </NuxtLink>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div v-for="(card, index) in statCards" :key="index" 
             class="cyber-card group hover-lift animate-fade-in"
             :style="{ animationDelay: `${index * 100}ms` }">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="w-12 h-12 rounded-lg flex items-center justify-center mb-4"
                   :class="`bg-gradient-to-br ${card.color} bg-opacity-20`">
                <component :is="card.icon" class="w-6 h-6 text-white" />
              </div>
              <div class="text-3xl font-bold text-white mb-1">
                {{ typeof card.value === 'number' ? card.value.toLocaleString() : card.value }}
              </div>
              <div class="text-sm text-slate-400 uppercase tracking-wide">{{ card.label }}</div>
              <div v-if="card.change" class="text-xs font-semibold mt-2"
                   :class="card.change > 0 ? 'text-success-light' : 'text-danger-light'">
                <span v-if="card.change > 0">↑</span>
                <span v-else>↓</span>
                {{ Math.abs(card.change) }}% from last hour
              </div>
            </div>
            <div v-if="card.trend" class="ml-4">
              <svg class="w-16 h-12 opacity-30" :class="`text-${card.color.split('-')[1]}-500`" viewBox="0 0 64 48" fill="none">
                <path :d="getTrendPath(card.trend)" stroke="currentColor" stroke-width="2" />
              </svg>
            </div>
          </div>
          <div class="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg pointer-events-none"
               :class="`${card.color} bg-opacity-5`"></div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <NuxtLink to="/upload" class="bg-blue-600 hover:bg-blue-700 p-6 rounded-lg text-center transition">
          <div class="text-2xl mb-2">Upload HTML Log</div>
          <div class="font-bold">Upload subscriber info for processing</div>
          <div class="text-sm text-blue-200 mt-2">Upload subscriber info for processing</div>
        </NuxtLink>
        
        <NuxtLink to="/ip-list" class="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-6 rounded-lg text-center transition">
          <div class="text-2xl mb-2">View IP Records</div>
          <div class="font-bold">Browse processed IP data</div>
          <div class="text-sm text-slate-400 mt-2">Browse processed IP data</div>
        </NuxtLink>
        
        <NuxtLink to="/analytics" class="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-6 rounded-lg text-center transition">
          <div class="text-2xl mb-2">Analytics</div>
          <div class="font-bold">View charts and statistics</div>
          <div class="text-sm text-slate-400 mt-2">View charts and statistics</div>
        </NuxtLink>
        
        <NuxtLink to="/map" class="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-6 rounded-lg text-center transition">
          <div class="text-2xl mb-2">Geographic Map</div>
          <div class="text-sm text-slate-400 mt-2">Visualize IP locations</div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
