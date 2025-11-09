<template>
  <div class="dashboard-container">
    <!-- Page Title Only (Navigation is in app.vue) -->
    <div class="page-title-section">
      <h1 class="page-title">
        <span class="title-icon">📊</span>
        COMMAND CENTER
      </h1>
      <p class="page-subtitle">Delhi Police Cyber Cell - IPDR Tracking Hub</p>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card active-cases">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <p class="stat-label">Active Cases</p>
          <p class="stat-value">{{ stats.totalCases }}</p>
          <p class="stat-change positive">+{{ stats.newCases }} this week</p>
        </div>
      </div>

      <div class="stat-card total-ips">
        <div class="stat-icon">🌐</div>
        <div class="stat-content">
          <p class="stat-label">IPs Tracked</p>
          <p class="stat-value">{{ stats.totalIPs }}</p>
          <p class="stat-change">Across all cases</p>
        </div>
      </div>

      <div class="stat-card countries">
        <div class="stat-icon">🗺️</div>
        <div class="stat-content">
          <p class="stat-label">Countries</p>
          <p class="stat-value">{{ stats.totalCountries }}</p>
          <p class="stat-change">Geographic spread</p>
        </div>
      </div>

      <div class="stat-card success-rate">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <p class="stat-label">Success Rate</p>
          <p class="stat-value">{{ stats.successRate }}%</p>
          <p class="stat-change positive">Excellent</p>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Recent FIR Cases -->
      <div class="content-card fir-list">
        <div class="card-header">
          <h2 class="card-title">
            <span class="card-icon">📋</span>
            Recent FIR Cases
          </h2>
          <NuxtLink to="/upload" class="action-btn">
            <span>➕</span>
            <span>New Case</span>
          </NuxtLink>
        </div>
        
        <div class="card-body">
          <div v-if="loading" class="loading-state">
            <div class="spinner-large"></div>
            <p>Loading cases...</p>
          </div>

          <div v-else-if="firCases.length === 0" class="empty-state">
            <p class="empty-icon">📂</p>
            <p class="empty-text">No FIR cases yet</p>
            <NuxtLink to="/upload" class="empty-action">Create your first case</NuxtLink>
          </div>

          <div v-else class="fir-table">
            <div 
              v-for="fir in firCases" 
              :key="fir.fir_number"
              class="fir-row"
              @click="viewFir(fir.fir_number)"
            >
              <div class="fir-info">
                <p class="fir-number">{{ fir.fir_number }}</p>
                <p class="fir-title">{{ fir.case_title }}</p>
              </div>
              <div class="fir-meta">
                <span class="fir-status" :class="fir.status">{{ fir.status }}</span>
                <span class="fir-priority" :class="fir.priority">{{ fir.priority }}</span>
              </div>
              <div class="fir-stats">
                <span class="fir-stat">
                  <span class="stat-icon-small">🌐</span>
                  {{ fir.total_ips || 0 }} IPs
                </span>
                <span class="fir-date">{{ formatDate(fir.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="content-card quick-actions">
        <div class="card-header">
          <h2 class="card-title">
            <span class="card-icon">⚡</span>
            Quick Actions
          </h2>
        </div>
        
        <div class="card-body">
          <NuxtLink to="/upload" class="action-card">
            <div class="action-icon upload">📤</div>
            <div class="action-content">
              <p class="action-title">Upload & Extract</p>
              <p class="action-desc">Upload HTML and extract IPs</p>
            </div>
          </NuxtLink>

          <NuxtLink to="/ip-lookup" class="action-card">
            <div class="action-icon lookup">🔍</div>
            <div class="action-content">
              <p class="action-title">IP Lookup</p>
              <p class="action-desc">Unlimited IP geolocation</p>
            </div>
          </NuxtLink>

          <button @click="showCreateFir = true" class="action-card">
            <div class="action-icon create">➕</div>
            <div class="action-content">
              <p class="action-title">Create FIR</p>
              <p class="action-desc">Start new investigation</p>
            </div>
          </button>

          <NuxtLink to="/reports" class="action-card">
            <div class="action-icon reports">📊</div>
            <div class="action-content">
              <p class="action-title">Reports</p>
              <p class="action-desc">View analytics & insights</p>
            </div>
          </NuxtLink>
        </div>
      </div>

      <!-- Activity Feed -->
      <div class="content-card activity-feed">
        <div class="card-header">
          <h2 class="card-title">
            <span class="card-icon">📡</span>
            Recent Activity
          </h2>
        </div>
        
        <div class="card-body">
          <div class="activity-list">
            <div v-for="(activity, index) in recentActivity" :key="index" class="activity-item">
              <div class="activity-icon" :class="activity.type">{{ activity.icon }}</div>
              <div class="activity-content">
                <p class="activity-text">{{ activity.text }}</p>
                <p class="activity-time">{{ activity.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create FIR Modal -->
    <div v-if="showCreateFir" class="modal-overlay" @click="showCreateFir = false">
      <div class="modal-card" @click.stop>
        <div class="modal-header">
          <h3>Create New FIR Case</h3>
          <button @click="showCreateFir = false" class="modal-close">✕</button>
        </div>
        <form @submit.prevent="createFir" class="modal-body">
          <div class="form-group">
            <label>FIR Number</label>
            <input v-model="newFir.fir_number" type="text" placeholder="FIR/2025/CC/001" required />
          </div>
          <div class="form-group">
            <label>Case Title</label>
            <input v-model="newFir.case_title" type="text" placeholder="Brief case description" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newFir.case_description" placeholder="Detailed case information" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>Priority</label>
            <select v-model="newFir.priority">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showCreateFir = false" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="creatingFir">
              {{ creatingFir ? 'Creating...' : 'Create FIR' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { user } = useAuth()
const { fir } = useApi()
const router = useRouter()

const loading = ref(true)
const firCases = ref<any[]>([])
const showCreateFir = ref(false)
const creatingFir = ref(false)

const stats = ref({
  totalCases: 0,
  newCases: 0,
  totalIPs: 0,
  totalCountries: 0,
  successRate: 100
})

const newFir = ref({
  fir_number: '',
  case_title: '',
  case_description: '',
  priority: 'medium'
})

const recentActivity = ref([
  { icon: '📁', type: 'create', text: 'New FIR case created', time: '2 minutes ago' },
  { icon: '🔍', type: 'lookup', text: 'IP lookup completed for 57 IPs', time: '15 minutes ago' },
  { icon: '📤', type: 'upload', text: 'HTML file uploaded and processed', time: '30 minutes ago' },
  { icon: '✅', type: 'success', text: 'Results stored in database', time: '1 hour ago' }
])

onMounted(async () => {
  await loadFirCases()
})

const loadFirCases = async () => {
  loading.value = true
  try {
    const result = await fir.list()
    if (result.success) {
      firCases.value = result.data.cases || []
      calculateStats()
    }
  } catch (error) {
    console.error('Error loading FIR cases:', error)
  } finally {
    loading.value = false
  }
}

const calculateStats = () => {
  stats.value.totalCases = firCases.value.length
  stats.value.totalIPs = firCases.value.reduce((sum, fir) => sum + (fir.total_ips || 0), 0)
  stats.value.newCases = firCases.value.filter(fir => {
    const created = new Date(fir.created_at)
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)
    return created > weekAgo
  }).length
}

const createFir = async () => {
  creatingFir.value = true
  try {
    const result = await fir.create(newFir.value)
    if (result.success) {
      showCreateFir.value = false
      await loadFirCases()
      newFir.value = { fir_number: '', case_title: '', case_description: '', priority: 'medium' }
    }
  } catch (error) {
    console.error('Error creating FIR:', error)
  } finally {
    creatingFir.value = false
  }
}

const viewFir = (firNumber: string) => {
  router.push(`/fir/${encodeURIComponent(firNumber)}`)
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #0a0a0a;
  padding: 2rem;
}

/* Page Title Section */
.page-title-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid rgba(14, 165, 233, 0.3);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #0ea5e9;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 20px rgba(14, 165, 233, 0.5);
  animation: titleGlow 2s ease-in-out infinite;
}

@keyframes titleGlow {
  0%, 100% { text-shadow: 0 0 20px rgba(14, 165, 233, 0.5); }
  50% { text-shadow: 0 0 30px rgba(14, 165, 233, 0.8); }
}

.page-subtitle {
  color: #10b981;
  margin: 0.5rem 0 0 0;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 255, 255, 0.2);
  border-color: #00ffff;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-label {
  color: #888;
  font-size: 0.875rem;
  margin: 0 0 0.25rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  color: #00ffff;
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.stat-change {
  color: #666;
  font-size: 0.75rem;
  margin: 0.25rem 0 0 0;
}

.stat-change.positive {
  color: #00ff88;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.content-card {
  background: rgba(10, 10, 10, 0.95);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #00ffff;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  border: none;
  border-radius: 6px;
  color: #000000;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.4);
}

.card-body {
  padding: 1.5rem;
}

/* FIR List */
.fir-table {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.fir-row {
  padding: 1rem;
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1rem;
  align-items: center;
}

.fir-row:hover {
  background: rgba(0, 255, 255, 0.08);
  border-color: #00ffff;
  transform: translateX(4px);
}

.fir-number {
  color: #00ffff;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  font-family: 'Courier New', monospace;
}

.fir-title {
  color: #ffffff;
  margin: 0;
  font-size: 0.875rem;
}

.fir-meta {
  display: flex;
  gap: 0.5rem;
}

.fir-status,
.fir-priority {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.fir-status.active {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.fir-priority.high {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
}

.fir-priority.medium {
  background: rgba(255, 165, 0, 0.2);
  color: #ffaa00;
}

.fir-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
}

.fir-stat {
  color: #00ffff;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.fir-date {
  color: #666;
}

/* Quick Actions */
.quick-actions .card-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s ease;
}

.action-card:hover {
  background: rgba(0, 255, 255, 0.08);
  border-color: #00ffff;
  transform: translateX(4px);
}

.action-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 1.5rem;
}

.action-icon.upload {
  background: rgba(0, 255, 255, 0.1);
}

.action-icon.lookup {
  background: rgba(0, 255, 136, 0.1);
}

.action-icon.create {
  background: rgba(255, 165, 0, 0.1);
}

.action-icon.reports {
  background: rgba(138, 43, 226, 0.1);
}

.action-title {
  color: #ffffff;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.action-desc {
  color: #888;
  font-size: 0.75rem;
  margin: 0;
}

/* Activity Feed */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.activity-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 1.25rem;
  background: rgba(0, 255, 255, 0.1);
}

.activity-text {
  color: #ffffff;
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
}

.activity-time {
  color: #666;
  font-size: 0.75rem;
  margin: 0;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 255, 255, 0.2);
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-text {
  color: #888;
  margin-bottom: 1rem;
}

.empty-action {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 6px;
  color: #00ffff;
  text-decoration: none;
  transition: all 0.3s ease;
}

.empty-action:hover {
  background: rgba(0, 255, 255, 0.2);
  transform: translateY(-2px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-card {
  background: #0a0a0a;
  border: 2px solid #00ffff;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  color: #00ffff;
  margin: 0;
  font-size: 1.25rem;
}

.modal-close {
  background: none;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  transition: color 0.2s;
}

.modal-close:hover {
  color: #ff6b6b;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #00ffff;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 6px;
  color: #ffffff;
  font-family: 'Courier New', monospace;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #00ffff;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.btn-primary {
  background: linear-gradient(135deg, #00ffff 0%, #00ff88 100%);
  border: none;
  color: #000000;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .fir-row {
    grid-template-columns: 1fr;
  }
}
</style>
