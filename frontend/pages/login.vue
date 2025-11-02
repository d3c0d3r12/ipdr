<template>
  <div class="cyber-login-container">
    <!-- Animated Background -->
    <div class="cyber-bg">
      <div class="grid-lines"></div>
      <div class="scan-line"></div>
    </div>

    <!-- Login Card -->
    <div class="login-card">
      <!-- Header -->
      <div class="login-header">
        <div class="logo-container">
          <div class="logo-icon">🔒</div>
          <div class="logo-text">
            <h1>IPDR TRACKING HUB</h1>
            <p>Delhi Police Cyber Cell</p>
          </div>
        </div>
        <div class="security-badge">
          <span class="badge-icon">🛡️</span>
          <span class="badge-text">SECURE ACCESS</span>
        </div>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">
            <span class="label-icon">👤</span>
            Username / Badge Number
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Enter your username"
            required
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="password">
            <span class="label-icon">🔑</span>
            Password
          </label>
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Enter your password"
            required
            :disabled="loading"
          />
          <button
            type="button"
            class="toggle-password"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? '👁️' : '👁️‍🗨️' }}
          </button>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          {{ error }}
        </div>

        <!-- Success Message -->
        <div v-if="success" class="success-message">
          <span class="success-icon">✅</span>
          {{ success }}
        </div>

        <!-- Login Button -->
        <button type="submit" class="login-button" :disabled="loading">
          <span v-if="!loading" class="button-content">
            <span class="button-icon">🚀</span>
            <span>ACCESS SYSTEM</span>
          </span>
          <span v-else class="button-loading">
            <span class="spinner"></span>
            <span>AUTHENTICATING...</span>
          </span>
        </button>

        <!-- Login Options -->
        <div class="login-options">
          <label class="remember-me">
            <input type="checkbox" v-model="rememberMe" />
            <span>Remember me</span>
          </label>
          <a href="#" class="forgot-password">Forgot Password?</a>
        </div>

        <!-- Signup Link -->
        <div class="signup-link">
          <p>Don't have an account?</p>
          <NuxtLink to="/signup" class="link">Register Here</NuxtLink>
        </div>
      </form>

      <!-- Footer -->
      <div class="login-footer">
        <p class="footer-text">
          <span class="footer-icon">🔐</span>
          Authorized Personnel Only
        </p>
        <p class="footer-subtext">
          All activities are monitored and logged
        </p>
      </div>
    </div>

    <!-- System Info -->
    <div class="system-info">
      <div class="info-item">
        <span class="info-label">System Status:</span>
        <span class="info-value online">🟢 ONLINE</span>
      </div>
      <div class="info-item">
        <span class="info-label">Security Level:</span>
        <span class="info-value">🔴 MAXIMUM</span>
      </div>
      <div class="info-item">
        <span class="info-label">Last Update:</span>
        <span class="info-value">{{ currentTime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { login } = useAuth()
const router = useRouter()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref('')
const currentTime = ref('')

// Update time
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-IN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

const handleLogin = async () => {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    const result = await login(username.value, password.value)

    if (result.success) {
      success.value = 'Login successful! Redirecting...'
      
      // Track login activity
      if (process.client) {
        const { tracking } = useApi()
        tracking.logActivity('login', 'User logged in', '/login')
      }

      // Redirect to dashboard
      setTimeout(() => {
        router.push('/dashboard')
      }, 1000)
    } else {
      error.value = result.message || 'Login failed'
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred during login'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.cyber-login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

/* Animated Background */
.cyber-bg {
  position: absolute;
  inset: 0;
  opacity: 0.3;
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0, 255, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(0, 255, 255, 0.8), 
    transparent
  );
  animation: scan 3s linear infinite;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

/* Login Card */
.login-card {
  background: rgba(10, 10, 10, 0.95);
  border: 2px solid #00ffff;
  border-radius: 12px;
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  box-shadow: 
    0 0 30px rgba(0, 255, 255, 0.3),
    inset 0 0 20px rgba(0, 255, 255, 0.05);
  position: relative;
  z-index: 10;
}

/* Header */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logo-icon {
  font-size: 3rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.logo-text h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #00ffff;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
  font-family: 'Courier New', monospace;
}

.logo-text p {
  font-size: 0.875rem;
  color: #00ff88;
  margin: 0.25rem 0 0 0;
}

.security-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid #ff0000;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #ff0000;
  font-weight: 600;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  position: relative;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #00ffff;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 6px;
  color: #ffffff;
  font-size: 1rem;
  font-family: 'Courier New', monospace;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #00ffff;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
  background: rgba(0, 255, 255, 0.1);
}

.form-group input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  top: 2.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.toggle-password:hover {
  opacity: 1;
}

/* Messages */
.error-message,
.success-message {
  padding: 0.875rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.error-message {
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid #ff0000;
  color: #ff6b6b;
}

.success-message {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid #00ff88;
  color: #00ff88;
}

/* Login Button */
.login-button {
  padding: 1rem;
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  border: none;
  border-radius: 6px;
  color: #000000;
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 255, 255, 0.5);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-content,
.button-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #000000;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Login Options */
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #888;
  cursor: pointer;
}

.remember-me input {
  cursor: pointer;
}

.forgot-password {
  color: #00ffff;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-password:hover {
  color: #00ff88;
}

/* Signup Link */
.signup-link {
  text-align: center;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid rgba(0, 255, 255, 0.1);
}

.signup-link p {
  color: #888;
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
}

.signup-link .link {
  color: #00ffff;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}

.signup-link .link:hover {
  color: #00ff88;
}

/* Footer */
.login-footer {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(0, 255, 255, 0.2);
  text-align: center;
}

.footer-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #ff6b6b;
  font-weight: 600;
  font-size: 0.875rem;
  margin: 0 0 0.5rem 0;
}

.footer-subtext {
  color: #666;
  font-size: 0.75rem;
  margin: 0;
}

/* System Info */
.system-info {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  z-index: 5;
}

.info-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.info-label {
  color: #666;
}

.info-value {
  color: #00ffff;
  font-weight: 600;
}

.info-value.online {
  color: #00ff88;
}

/* Responsive */
@media (max-width: 640px) {
  .cyber-login-container {
    padding: 1rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
  }

  .system-info {
    bottom: 1rem;
    right: 1rem;
    font-size: 0.65rem;
  }
}
</style>
