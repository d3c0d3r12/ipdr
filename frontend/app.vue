<template>
  <div class="dp-app">
    <!-- Cyber Security Animated Background -->
    <CyberBackground />
    
    <!-- Video Background (optional - place video in public folder) -->
    <VideoBackground v-if="showVideoBackground" :opacity="0.08" />
    
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

// Enable/disable video background (set to true if you have a video file)
const showVideoBackground = ref(false) // Set to true when you add video to public folder

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
  
  // Check if video file exists
  if (typeof window !== 'undefined') {
    fetch('/background-video.mp4', { method: 'HEAD' })
      .then(response => {
        if (response.ok) {
          showVideoBackground.value = true
        }
      })
      .catch(() => {
        // Video not found, keep disabled
        showVideoBackground.value = false
      })
  }
})
</script>

<style>
/* Global App Styles */
.dp-app {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  position: relative;
}

/* Ensure content is above background */
.dp-app > * {
  position: relative;
  z-index: 1;
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
