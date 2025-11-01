<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    @click="handleClick"
  >
    <span v-if="loading" class="spinner mr-2"></span>
    <component v-else-if="icon" :is="icon" class="w-5 h-5 mr-2" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  icon?: any
  fullWidth?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'
  
  const variants = {
    primary: 'btn-cyber',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white shadow-lg',
    success: 'bg-success hover:bg-success-dark text-white shadow-lg hover:shadow-glow',
    danger: 'bg-danger hover:bg-danger-dark text-white shadow-lg',
    ghost: 'bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-cyber-500'
  }
  
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  }
  
  const width = props.fullWidth ? 'w-full' : ''
  
  return [
    base,
    variants[props.variant || 'primary'],
    sizes[props.size || 'md'],
    width
  ].join(' ')
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>
