<template>
  <div v-if="isAuthenticated && remainingMinutes > 0" class="session-timer" :class="{ warning: remainingMinutes <= 5 }">
    <div class="timer-icon">⏱️</div>
    <div class="timer-content">
      <div class="timer-label">Session</div>
      <div class="timer-value">{{ remainingMinutes }}m</div>
    </div>
    <div v-if="remainingMinutes <= 5" class="timer-warning">
      Expiring soon!
    </div>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated, getRemainingTime } = useAuth()

const remainingMinutes = ref(0)

// Update remaining time every 30 seconds
const updateTimer = () => {
  if (isAuthenticated.value) {
    remainingMinutes.value = getRemainingTime()
  }
}

onMounted(() => {
  updateTimer()
  setInterval(updateTimer, 30000) // Update every 30 seconds
})
</script>

<style scoped>
.session-timer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  transition: all 0.3s ease;
}

.session-timer.warning {
  background: rgba(255, 165, 0, 0.1);
  border-color: rgba(255, 165, 0, 0.5);
  animation: pulse-warning 2s ease-in-out infinite;
}

@keyframes pulse-warning {
  0%, 100% {
    box-shadow: 0 0 5px rgba(255, 165, 0, 0.3);
  }
  50% {
    box-shadow: 0 0 15px rgba(255, 165, 0, 0.6);
  }
}

.timer-icon {
  font-size: 1.25rem;
}

.timer-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.timer-label {
  font-size: 0.625rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.timer-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: #00ffff;
}

.session-timer.warning .timer-value {
  color: #ffaa00;
}

.timer-warning {
  font-size: 0.625rem;
  color: #ffaa00;
  font-weight: 600;
  animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
