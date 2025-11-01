<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRuntimeConfig, useNuxtApp } from '#app'
const { $fetch } = useNuxtApp()
const apiBase = useRuntimeConfig().public.apiBase
const items = ref<any[]>([])
onMounted(async () => {
	try {
		const res:any = await $fetch(`${apiBase}/api/data`, { params: { page: 1, page_size: 500 } })
		items.value = res.items
	} catch {}
})
</script>

<template>
	<div class="min-h-screen bg-gradient-to-b from-black via-slate-900 to-black text-slate-200">
		<Navbar />
		<div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
			<h1 class="text-2xl font-bold tracking-wider">Map</h1>
			<MapView :items="items" />
		</div>
	</div>
</template>
