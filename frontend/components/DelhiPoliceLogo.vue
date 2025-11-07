<template>
  <NuxtLink to="/" class="dp-logo">
    <div class="dp-logo-icon">
      <span class="dp-logo-badge">🛡️</span>
    </div>
    <div class="dp-logo-text">
      <div class="dp-logo-title">DELHI POLICE</div>
      <div class="dp-logo-subtitle">IPDR Tracking Hub</div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
// Delhi Police Logo Component
// Professional branding for law enforcement
</script>

<style scoped>
.dp-logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--text-primary);
  text-decoration: none;
  transition: all 200ms ease-in-out;
}

.dp-logo:hover {
  transform: translateY(-2px);
}

.dp-logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(30, 58, 138, 0.5);
  position: relative;
  overflow: hidden;
}

.dp-logo-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.dp-logo-badge {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.dp-logo-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.dp-logo-title {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.dp-logo-subtitle {
  font-size: 0.75rem;
  font-weight: 500;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

@media (max-width: 768px) {
  .dp-logo-text {
    display: none;
  }
}
</style>
