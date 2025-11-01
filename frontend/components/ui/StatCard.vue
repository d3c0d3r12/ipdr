<template>
  <div class="stat-card group hover-lift hover-glow animate-fade-in">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="stat-card-icon">
          <component :is="icon" class="w-6 h-6" />
        </div>
        <div class="stat-card-value">
          <span v-if="animated">{{ displayValue }}</span>
          <span v-else>{{ value }}</span>
        </div>
        <div class="stat-card-label">{{ label }}</div>
        <div v-if="change" class="stat-card-change" :class="changeClass">
          <span v-if="change > 0">↑</span>
          <span v-else>↓</span>
          {{ Math.abs(change) }}%
        </div>
      </div>
      <div v-if="trend" class="ml-4">
        <svg class="w-16 h-12 text-cyber-500/30" viewBox="0 0 64 48" fill="none">
          <path :d="trendPath" stroke="currentColor" stroke-width="2" />
        </svg>
      </div>
    </div>
    
    <!-- Glow effect on hover -->
    <div class="absolute inset-0 bg-gradient-to-r from-cyber-500/0 via-cyber-500/5 to-cyber-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg pointer-events-none"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps<{
  icon: any
  label: string
  value: number | string
  change?: number
  trend?: number[]
  animated?: boolean
}>()

const displayValue = ref(0)

const changeClass = computed(() => {
  if (!props.change) return ''
  return props.change > 0 ? 'text-success-light' : 'text-danger-light'
})

const trendPath = computed(() => {
  if (!props.trend || props.trend.length === 0) return ''
  const points = props.trend
  const width = 64
  const height = 48
  const step = width / (points.length - 1)
  const max = Math.max(...points)
  const min = Math.min(...points)
  const range = max - min || 1
  
  let path = `M 0 ${height - ((points[0] - min) / range) * height}`
  points.forEach((point, i) => {
    if (i > 0) {
      const x = i * step
      const y = height - ((point - min) / range) * height
      path += ` L ${x} ${y}`
    }
  })
  return path
})

// Animate number counting
const animateValue = (start: number, end: number, duration: number = 1000) => {
  const startTime = Date.now()
  const animate = () => {
    const now = Date.now()
    const progress = Math.min((now - startTime) / duration, 1)
    const easeOutQuart = 1 - Math.pow(1 - progress, 4)
    displayValue.value = Math.floor(start + (end - start) * easeOutQuart)
    
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  requestAnimationFrame(animate)
}

onMounted(() => {
  if (props.animated && typeof props.value === 'number') {
    animateValue(0, props.value)
  }
})

watch(() => props.value, (newVal) => {
  if (props.animated && typeof newVal === 'number') {
    animateValue(displayValue.value, newVal)
  }
})
</script>
