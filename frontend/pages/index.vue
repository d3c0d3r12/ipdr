<script setup lang="ts">
// Redirect to login or dashboard based on auth status
const { isAuthenticated, checkAuth } = useAuth()
const router = useRouter()

onMounted(() => {
  checkAuth()
  
  if (isAuthenticated.value) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
})
</script>

<template>
  <div class="min-h-screen bg-black flex items-center justify-center">
    <div class="text-center">
      <div class="spinner"></div>
      <p class="text-cyan-400 mt-4">Redirecting...</p>
    </div>
  </div>
</template>

<style scoped>
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 255, 255, 0.2);
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
