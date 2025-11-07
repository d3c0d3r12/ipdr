<template>
  <NuxtLink to="/" class="dp-logo">
    <div class="dp-logo-icon">
      <img src="/Delhi_Police_Logo-1.png" alt="Delhi Police" class="dp-logo-image" />
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
  width: 56px;
  height: 56px;
  background: white;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), 0 0 20px rgba(30, 58, 138, 0.3);
  position: relative;
  overflow: hidden;
  padding: 0.25rem;
}

.dp-logo-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.2) 50%, transparent 70%);
  animation: shimmer 3s infinite;
  z-index: 1;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.dp-logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  position: relative;
  z-index: 0;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
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
