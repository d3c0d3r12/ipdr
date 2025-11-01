<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRuntimeConfig, useNuxtApp } from '#app'
const { $fetch } = useNuxtApp()
const apiBase = useRuntimeConfig().public.apiBase
const summary = ref<any>({ total_ips: 0, countries: {}, top_isps: {} })
onMounted(async () => {
	try { summary.value = await $fetch(`${apiBase}/api/summary`) } catch {}
})
</script>

<template>
	<div class="min-h-screen bg-gradient-to-b from-black via-slate-900 to-black text-slate-200">
		<Navbar />
		<div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
			<h1 class="text-2xl font-bold tracking-wider">Analytics</h1>
			<ChartView :countries="summary.countries || {}" :isps="summary.top_isps || {}" />
		</div>
	</div>
</template>
