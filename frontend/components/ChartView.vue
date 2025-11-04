<script setup lang="ts">
defineProps<{ countries: Record<string, number>, isps: Record<string, number> }>()
</script>

<template>
	<div class="grid md:grid-cols-2 gap-4">
		<div class="bg-slate-900/60 border border-slate-800 rounded p-4">
			<h3 class="text-slate-300 mb-2">Top Countries</h3>
			<ul class="space-y-1">
				<li v-for="(v,k) in countries" :key="k" class="flex justify-between">
					<span class="text-slate-400">{{ k }}</span>
					<span class="text-cyan-400 font-mono">{{ v }}</span>
				</li>
			</ul>
		</div>
		<div class="bg-slate-900/60 border border-slate-800 rounded p-4">
			<h3 class="text-slate-300 mb-2">Top ISPs</h3>
			<ul class="space-y-1">
				<li v-for="(v,k) in isps" :key="k" class="flex justify-between">
					<span class="text-slate-400">{{ k }}</span>
					<span class="text-cyan-400 font-mono">{{ v }}</span>
				</li>
			</ul>
		</div>
	</div>
</template>






