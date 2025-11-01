<template>
	<div class="w-full bg-black/60 backdrop-blur border-b border-cyan-500/30">
		<div class="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
			<div class="flex items-center gap-2 text-cyan-400 font-semibold tracking-widest">
				<span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
				<span>POLICE INTEL</span>
			</div>
			<nav class="flex items-center gap-4 text-slate-300">
				<NuxtLink to="/" class="hover:text-cyan-400">Dashboard</NuxtLink>
				<NuxtLink to="/upload" class="hover:text-cyan-400">Upload</NuxtLink>
				<NuxtLink to="/ip-list" class="hover:text-cyan-400">IP List</NuxtLink>
				<NuxtLink to="/analytics" class="hover:text-cyan-400">Analytics</NuxtLink>
				<NuxtLink to="/map" class="hover:text-cyan-400">Map</NuxtLink>
			</nav>
		</div>
	</div>
</template>





