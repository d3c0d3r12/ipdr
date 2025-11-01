<script setup lang="ts">
defineProps<{ records: any[] }>()
</script>

<template>
	<div class="overflow-auto border border-slate-800 rounded">
		<table class="min-w-full text-sm">
			<thead class="bg-slate-800/60 text-slate-300">
				<tr>
					<th class="text-left px-3 py-2">Timestamp</th>
					<th class="text-left px-3 py-2">IP</th>
					<th class="text-left px-3 py-2">Country</th>
					<th class="text-left px-3 py-2">Region</th>
					<th class="text-left px-3 py-2">City</th>
					<th class="text-left px-3 py-2">ISP</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="r in records" :key="r.row_index" class="border-b border-slate-800 hover:bg-slate-800/40">
					<td class="px-3 py-2">{{ r.timestamp || r.timestamp_original }}</td>
					<td class="px-3 py-2 font-mono text-cyan-300">{{ r.ip || r.ip_original }}</td>
					<td class="px-3 py-2">{{ r.country }}</td>
					<td class="px-3 py-2">{{ r.region }}</td>
					<td class="px-3 py-2">{{ r.city }}</td>
					<td class="px-3 py-2">{{ r.isp }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>





