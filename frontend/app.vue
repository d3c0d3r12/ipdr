<template>
  <div class="dp-app">
    <!-- Only show navigation on authenticated pages (not login/signup) -->
    <DelhiPoliceNav v-if="showNav" />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
// Import theme CSS
import '~/assets/css/theme.css'

const route = useRoute()
const { checkAuth, isAuthenticated } = useAuth()

// Hide navigation on login and signup pages
// Also hide if not authenticated
const showNav = computed(() => {
  const publicPages = ['/login', '/signup', '/']
  
  // Never show nav on public pages
  if (publicPages.includes(route.path)) {
    return false
  }
  
  // Only show nav if authenticated
  return isAuthenticated.value
})

onMounted(() => {
  checkAuth()
})
</script>

<style>
/* Global App Styles */
.dp-app {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-accent);
}

/* Selection Styling */
::selection {
  background: rgba(30, 58, 138, 0.3);
  color: var(--text-primary);
}
</style>
