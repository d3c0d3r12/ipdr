<template>
  <div class="signup-container">
    <!-- Animated Background -->
    <div class="cyber-bg">
      <div class="grid-lines"></div>
      <div class="scan-line"></div>
    </div>

    <!-- Signup Card -->
    <div class="signup-card">
      <!-- Header -->
      <div class="signup-header">
        <div class="logo-container">
          <div class="logo-icon">🔐</div>
          <div class="logo-text">
            <h1>IPDR TRACKING HUB</h1>
            <p>Delhi Police Cyber Cell - New User Registration</p>
          </div>
        </div>
      </div>

      <!-- Signup Form -->
      <form @submit.prevent="handleSignup" class="signup-form">
        <div class="form-row">
          <div class="form-group">
            <label for="username">
              <span class="label-icon">👤</span>
              Username / Badge Number
            </label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              placeholder="Enter username"
              required
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label for="email">
              <span class="label-icon">📧</span>
              Email Address
            </label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              placeholder="officer@delhipolice.gov.in"
              required
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="full_name">
              <span class="label-icon">👨‍✈️</span>
              Full Name
            </label>
            <input
              id="full_name"
              v-model="formData.full_name"
              type="text"
              placeholder="Enter full name"
              required
              :disabled="loading"
            />
          </div>

          <div class="form-group">
            <label for="badge_number">
              <span class="label-icon">🎖️</span>
              Badge Number
            </label>
            <input
              id="badge_number"
              v-model="formData.badge_number"
              type="text"
              placeholder="Enter badge number"
              :disabled="loading"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="department">
              <span class="label-icon">🏢</span>
              Department
            </label>
            <select
              id="department"
              v-model="formData.department"
              required
              :disabled="loading"
            >
              <option value="">Select Department</option>
              <option value="Cyber Cell">Cyber Cell</option>
              <option value="Crime Branch">Crime Branch</option>
              <option value="Special Cell">Special Cell</option>
              <option value="Intelligence">Intelligence</option>
              <option value="Forensics">Forensics</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div class="form-group">
            <label for="role">
              <span class="label-icon">⚡</span>
              Role
            </label>
            <select
              id="role"
              v-model="formData.role"
              required
              :disabled="loading"
            >
              <option value="">Select Role</option>
              <option value="officer">Officer</option>
              <option value="investigator">Investigator</option>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="password">
              <span class="label-icon">🔑</span>
              Password
            </label>
            <input
              id="password"
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter password (min 8 chars)"
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

          <div class="form-group">
            <label for="confirm_password">
              <span class="label-icon">🔒</span>
              Confirm Password
            </label>
            <input
              id="confirm_password"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Re-enter password"
              required
              :disabled="loading"
            />
          </div>
        </div>

        <!-- Password Requirements -->
        <div class="password-requirements">
          <p class="requirements-title">Password must contain:</p>
          <ul>
            <li :class="{ valid: hasMinLength }">✓ At least 8 characters</li>
            <li :class="{ valid: hasUppercase }">✓ One uppercase letter</li>
            <li :class="{ valid: hasLowercase }">✓ One lowercase letter</li>
            <li :class="{ valid: hasNumber }">✓ One number</li>
            <li :class="{ valid: hasSpecial }">✓ One special character</li>
          </ul>
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

        <!-- Signup Button -->
        <button type="submit" class="signup-button" :disabled="loading || !isPasswordValid">
          <span v-if="!loading" class="button-content">
            <span class="button-icon">🚀</span>
            <span>CREATE ACCOUNT</span>
          </span>
          <span v-else class="button-loading">
            <span class="spinner"></span>
            <span>CREATING ACCOUNT...</span>
          </span>
        </button>

        <!-- Login Link -->
        <div class="login-link">
          <p>Already have an account?</p>
          <NuxtLink to="/login" class="link">Login Here</NuxtLink>
        </div>
      </form>

      <!-- Footer -->
      <div class="signup-footer">
        <p class="footer-text">
          <span class="footer-icon">🔐</span>
          Authorized Personnel Only
        </p>
        <p class="footer-subtext">
          All registrations are monitored and require approval
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { signup } = useAuth()
const router = useRouter()

const formData = ref({
  username: '',
  email: '',
  password: '',
  full_name: '',
  badge_number: '',
  department: '',
  role: ''
})

const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref('')

// Password validation
const hasMinLength = computed(() => formData.value.password.length >= 8)
const hasUppercase = computed(() => /[A-Z]/.test(formData.value.password))
const hasLowercase = computed(() => /[a-z]/.test(formData.value.password))
const hasNumber = computed(() => /[0-9]/.test(formData.value.password))
const hasSpecial = computed(() => /[!@#$%^&*(),.?":{}|<>]/.test(formData.value.password))

const isPasswordValid = computed(() => {
  return hasMinLength.value && 
         hasUppercase.value && 
         hasLowercase.value && 
         hasNumber.value && 
         hasSpecial.value
})

const handleSignup = async () => {
  error.value = ''
  success.value = ''

  // Validate passwords match
  if (formData.value.password !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  // Validate password strength
  if (!isPasswordValid.value) {
    error.value = 'Password does not meet requirements'
    return
  }

  loading.value = true

  try {
    const result = await signup(formData.value)

    if (result.success) {
      success.value = 'Account created successfully! Redirecting to login...'
      
      // Clear form
      formData.value = {
        username: '',
        email: '',
        password: '',
        full_name: '',
        badge_number: '',
        department: '',
        role: ''
      }
      confirmPassword.value = ''

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      error.value = result.message || 'Signup failed'
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred during signup'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.signup-container {
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
  background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.8), transparent);
  animation: scan 3s linear infinite;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

/* Signup Card */
.signup-card {
  background: rgba(10, 10, 10, 0.95);
  border: 2px solid #00ffff;
  border-radius: 12px;
  padding: 3rem;
  max-width: 900px;
  width: 100%;
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.3), inset 0 0 20px rgba(0, 255, 255, 0.05);
  position: relative;
  z-index: 10;
}

/* Header */
.signup-header {
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

/* Form */
.signup-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
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

.form-group input,
.form-group select {
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

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #00ffff;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
  background: rgba(0, 255, 255, 0.1);
}

.form-group input:disabled,
.form-group select:disabled {
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

/* Password Requirements */
.password-requirements {
  padding: 1rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 6px;
}

.requirements-title {
  font-size: 0.875rem;
  color: #00ffff;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.password-requirements li {
  font-size: 0.75rem;
  color: #666;
  transition: color 0.3s;
}

.password-requirements li.valid {
  color: #00ff88;
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

/* Signup Button */
.signup-button {
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

.signup-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 255, 255, 0.5);
}

.signup-button:active:not(:disabled) {
  transform: translateY(0);
}

.signup-button:disabled {
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

/* Login Link */
.login-link {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 255, 255, 0.2);
}

.login-link p {
  color: #888;
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
}

.login-link .link {
  color: #00ffff;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}

.login-link .link:hover {
  color: #00ff88;
}

/* Footer */
.signup-footer {
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

/* Responsive */
@media (max-width: 768px) {
  .signup-container {
    padding: 1rem;
  }

  .signup-card {
    padding: 2rem 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .password-requirements ul {
    grid-template-columns: 1fr;
  }
}
</style>
