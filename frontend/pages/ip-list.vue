<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRuntimeConfig } from '#app'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'
const records = ref<any[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await fetch(`${apiBase}/api/data/?limit=100`)
    const data = await response.json()
    records.value = data.records || []
  } catch (e: any) {
    error.value = 'Failed to load records'
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-slate-200">
    <nav class="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-400"> Processed IP Records</h1>
        <NuxtLink to="/" class="text-slate-400 hover:text-slate-200"> Back to Dashboard</NuxtLink>
      </div>
    </nav>
    
    <div class="p-6">
      <div class="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <div class="p-4 border-b border-slate-700">
          <h2 class="text-lg font-semibold">IP Activity Records</h2>
          <p class="text-sm text-slate-400 mt-1">Showing {{ records.length }} records</p>
        </div>
        
        <div v-if="loading" class="p-8 text-center text-slate-400">
          Loading records...
        </div>
        
        <div v-else-if="error" class="p-8 text-center text-red-400">
          {{ error }}
        </div>
        
        <div v-else-if="records.length === 0" class="p-8 text-center text-slate-400">
          No records found. Upload HTML files to get started.
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-900">
              <tr>
                <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Timestamp</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">IP Address</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Country</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">City</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">ISP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(record, index) in records" :key="index" class="border-t border-slate-700 hover:bg-slate-750">
                <td class="px-4 py-3 text-sm">{{ record.timestamp || record.timestamp_original }}</td>
                <td class="px-4 py-3 text-sm font-mono text-blue-400">{{ record.ip || record.ip_original }}</td>
                <td class="px-4 py-3 text-sm">{{ record.country || record.Country || '-' }}</td>
                <td class="px-4 py-3 text-sm">{{ record.city || record.City || '-' }}</td>
                <td class="px-4 py-3 text-sm">{{ record.isp || record.ISP || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
