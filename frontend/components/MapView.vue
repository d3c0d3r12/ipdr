<script setup lang="ts">
defineProps<{ items: any[] }>()
</script>

<template>
	<div class="bg-slate-900/60 border border-slate-800 rounded p-4 text-slate-400">
		<p class="mb-2">Map placeholder (hook to Mapbox or Leaflet).</p>
		<p>Total records: {{ items.length }}</p>
	</div>
</template>





