<template>
  <nav class="dp-navbar">
    <div class="dp-navbar-container">
      <DelhiPoliceLogo />
      
      <div class="dp-navbar-menu">
        <NuxtLink to="/" class="dp-navbar-link" :class="{ active: route.path === '/' }">
          <span class="nav-icon">🏠</span>
          <span>Dashboard</span>
        </NuxtLink>
        
        <NuxtLink to="/upload" class="dp-navbar-link" :class="{ active: route.path === '/upload' }">
          <span class="nav-icon">📤</span>
          <span>Upload</span>
        </NuxtLink>
        
        <NuxtLink to="/ip-lookup" class="dp-navbar-link" :class="{ active: route.path === '/ip-lookup' }">
          <span class="nav-icon">🔍</span>
          <span>IP Lookup</span>
        </NuxtLink>
        
        <NuxtLink to="/fir-management" class="dp-navbar-link" :class="{ active: route.path === '/fir-management' }">
          <span class="nav-icon">📋</span>
          <span>FIR Management</span>
        </NuxtLink>
        
        <div class="dp-navbar-divider"></div>
        
        <div v-if="isAuthenticated" class="dp-navbar-user">
          <div class="user-info">
            <span class="user-icon">👤</span>
            <span class="user-name">{{ user?.username || 'Officer' }}</span>
          </div>
          <button @click="handleLogout" class="dp-btn dp-btn-ghost dp-btn-sm">
            <span>🚪</span>
            <span>Logout</span>
          </button>
        </div>
        
        <NuxtLink v-else to="/login" class="dp-btn dp-btn-primary dp-btn-sm">
          <span>🔐</span>
          <span>Login</span>
        </NuxtLink>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { isAuthenticated, user, logout } = useAuth()

const handleLogout = async () => {
  await logout()
  router.push('/login')
}
</script>

<style scoped>
.dp-navbar {
  background: #1e293b;
  border-bottom: 2px solid #1e3a8a;
  padding: 1rem 2rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.dp-navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.dp-navbar-menu {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.dp-navbar-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 200ms ease-in-out;
  position: relative;
  font-size: 0.875rem;
}

.dp-navbar-link:hover {
  color: #f8fafc;
  background: #334155;
}

.dp-navbar-link.active {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
}

.dp-navbar-link.active::after {
  content: '';
  position: absolute;
  bottom: -1rem;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
}

.nav-icon {
  font-size: 1.125rem;
}

.dp-navbar-divider {
  width: 1px;
  height: 32px;
  background: #334155;
  margin: 0 0.5rem;
}

.dp-navbar-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #334155;
  border-radius: 0.5rem;
}

.user-icon {
  font-size: 1.25rem;
}

.user-name {
  font-weight: 600;
  color: #f8fafc;
  font-size: 0.875rem;
}

@media (max-width: 1024px) {
  .dp-navbar-menu {
    gap: 0.25rem;
  }
  
  .dp-navbar-link span:not(.nav-icon) {
    display: none;
  }
  
  .user-name {
    display: none;
  }
}

@media (max-width: 768px) {
  .dp-navbar {
    padding: 0.75rem 1rem;
  }
  
  .dp-navbar-container {
    gap: 1rem;
  }
}
</style>
