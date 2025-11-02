<template>
  <div class="fir-details-page">
    <NuxtLink to="/dashboard" class="back-btn">← Back to Dashboard</NuxtLink>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading FIR details...</p>
    </div>

    <div v-else-if="firDetails" class="fir-content">
      <!-- Header -->
      <div class="fir-header">
        <div>
          <h1>{{ firDetails.fir_number }}</h1>
          <p>{{ firDetails.case_title }}</p>
        </div>
        <div class="badges">
          <span class="badge" :class="firDetails.status">{{ firDetails.status }}</span>
          <span class="badge" :class="firDetails.priority">{{ firDetails.priority }}</span>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">🌐</div>
          <div>
            <div class="stat-value">{{ statistics.total_ips || 0 }}</div>
            <div class="stat-label">Total IPs</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🗺️</div>
          <div>
            <div class="stat-value">{{ statistics.total_countries || 0 }}</div>
            <div class="stat-label">Countries</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📡</div>
          <div>
            <div class="stat-value">{{ statistics.total_isps || 0 }}</div>
            <div class="stat-label">ISPs</div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id" :class="{ active: activeTab === tab.id }">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Overview -->
        <div v-if="activeTab === 'overview'" class="tab-panel">
          <div class="info-card">
            <h3>Case Information</h3>
            <div class="info-grid">
              <div><strong>FIR Number:</strong> {{ firDetails.fir_number }}</div>
              <div><strong>Officer:</strong> {{ firDetails.investigating_officer }}</div>
              <div><strong>Department:</strong> {{ firDetails.department }}</div>
              <div><strong>Created:</strong> {{ formatDate(firDetails.created_at) }}</div>
            </div>
            <div class="description">
              <strong>Description:</strong>
              <p>{{ firDetails.case_description || 'No description' }}</p>
            </div>
          </div>
        </div>

        <!-- IP Lookups -->
        <div v-if="activeTab === 'ips'" class="tab-panel">
          <div class="table-actions">
            <input v-model="searchQuery" placeholder="Search IPs, cities, countries..." class="search-input" />
            <button @click="exportData" class="btn-export">📥 Export CSV</button>
          </div>
          <div class="table-wrapper">
            <table class="ip-table">
              <thead>
                <tr>
                  <th>IP Address</th>
                  <th>Country</th>
                  <th>City</th>
                  <th>ISP</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="ip in filteredIPs" :key="ip.ip_address">
                  <td><code>{{ ip.ip_address }}</code></td>
                  <td>{{ ip.country }}</td>
                  <td>{{ ip.city || 'Unknown' }}</td>
                  <td>{{ ip.isp || 'Unknown' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="filteredIPs.length === 0" class="empty">No IP records found</div>
        </div>

        <!-- Analytics -->
        <div v-if="activeTab === 'analytics'" class="tab-panel">
          <div class="charts-grid">
            <div class="chart-card">
              <h3>Top Countries</h3>
              <div v-for="country in topCountries" :key="country.name" class="bar-item">
                <div class="bar-label">
                  <span>{{ country.name }}</span>
                  <span>{{ country.count }}</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: (country.count / maxCountryCount * 100) + '%' }"></div>
                </div>
              </div>
            </div>
            <div class="chart-card">
              <h3>Top ISPs</h3>
              <div v-for="isp in topISPs" :key="isp.name" class="bar-item">
                <div class="bar-label">
                  <span>{{ isp.name }}</span>
                  <span>{{ isp.count }}</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill isp" :style="{ width: (isp.count / maxISPCount * 100) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Timeline -->
        <div v-if="activeTab === 'timeline'" class="tab-panel">
          <div class="timeline">
            <div v-for="(event, i) in timeline" :key="i" class="timeline-item">
              <div class="timeline-marker"></div>
              <div class="timeline-content">
                <h4>{{ event.event_title }}</h4>
                <p>{{ event.event_description }}</p>
                <small>{{ formatDateTime(event.timestamp) }} • {{ event.performed_by }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const route = useRoute()
const firId = route.params.id

const loading = ref(true)
const firDetails = ref(null)
const statistics = ref({})
const ipLookups = ref([])
const timeline = ref([])
const activeTab = ref('overview')
const searchQuery = ref('')

const tabs = [
  { id: 'overview', label: 'Overview', icon: '📋' },
  { id: 'ips', label: 'IP Lookups', icon: '🌐' },
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'timeline', label: 'Timeline', icon: '⏱️' }
]

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const baseURL = 'http://localhost:8000'
    
    // Load FIR details
    const detailsRes = await fetch(`${baseURL}/api/fir/${firId}`)
    if (detailsRes.ok) firDetails.value = await detailsRes.json()

    // Load statistics
    const statsRes = await fetch(`${baseURL}/api/fir/${firId}/statistics`)
    if (statsRes.ok) statistics.value = await statsRes.json()

    // Load IP lookups
    const ipsRes = await fetch(`${baseURL}/api/fir/${firId}/ip-lookups?limit=1000`)
    if (ipsRes.ok) {
      const data = await ipsRes.json()
      ipLookups.value = data.results || []
    }

    // Load timeline
    const timelineRes = await fetch(`${baseURL}/api/fir/${firId}/timeline`)
    if (timelineRes.ok) {
      const data = await timelineRes.json()
      timeline.value = data.events || []
    }
  } catch (error) {
    console.error('Error loading FIR data:', error)
  } finally {
    loading.value = false
  }
}

const filteredIPs = computed(() => {
  if (!searchQuery.value) return ipLookups.value
  const q = searchQuery.value.toLowerCase()
  return ipLookups.value.filter(ip => 
    ip.ip_address?.toLowerCase().includes(q) ||
    ip.country?.toLowerCase().includes(q) ||
    ip.city?.toLowerCase().includes(q) ||
    ip.isp?.toLowerCase().includes(q)
  )
})

const topCountries = computed(() => {
  const counts = {}
  ipLookups.value.forEach(ip => {
    const country = ip.country || 'Unknown'
    counts[country] = (counts[country] || 0) + 1
  })
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const topISPs = computed(() => {
  const counts = {}
  ipLookups.value.forEach(ip => {
    const isp = ip.isp || 'Unknown'
    counts[isp] = (counts[isp] || 0) + 1
  })
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const maxCountryCount = computed(() => Math.max(...topCountries.value.map(c => c.count), 1))
const maxISPCount = computed(() => Math.max(...topISPs.value.map(i => i.count), 1))

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('en-IN')
}

const exportData = () => {
  const csv = [
    ['IP Address', 'Country', 'City', 'Region', 'ISP'],
    ...ipLookups.value.map(ip => [ip.ip_address, ip.country, ip.city, ip.region, ip.isp])
  ].map(row => row.join(',')).join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${firId}_ip_lookups.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.fir-details-page {
  min-height: 100vh;
  background: #0a0a0a;
  padding: 2rem;
  color: #fff;
}

.back-btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: rgba(0, 255, 255, 0.1);
  border: 1px solid #00ffff;
  border-radius: 6px;
  color: #00ffff;
  text-decoration: none;
  margin-bottom: 2rem;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(0, 255, 255, 0.2);
  transform: translateX(-4px);
}

.loading {
  text-align: center;
  padding: 4rem;
  color: #666;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 255, 255, 0.2);
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fir-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  margin-bottom: 2rem;
}

.fir-header h1 {
  font-size: 2rem;
  color: #00ffff;
  margin: 0 0 0.5rem 0;
  font-family: 'Courier New', monospace;
}

.fir-header p {
  color: #fff;
  margin: 0;
}

.badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.active {
  background: rgba(0, 255, 136, 0.2);
  border: 1px solid #00ff88;
  color: #00ff88;
}

.badge.high {
  background: rgba(255, 0, 0, 0.2);
  border: 1px solid #ff0000;
  color: #ff6b6b;
}

.badge.medium {
  background: rgba(255, 165, 0, 0.2);
  border: 1px solid #ffaa00;
  color: #ffaa00;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #00ffff;
  font-family: 'Courier New', monospace;
}

.stat-label {
  font-size: 0.875rem;
  color: #888;
  text-transform: uppercase;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid rgba(0, 255, 255, 0.2);
  margin-bottom: 2rem;
}

.tabs button {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #888;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: -2px;
}

.tabs button:hover {
  color: #00ffff;
  background: rgba(0, 255, 255, 0.05);
}

.tabs button.active {
  color: #00ffff;
  border-bottom-color: #00ffff;
}

.tab-content {
  background: rgba(10, 10, 10, 0.95);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 12px;
  padding: 2rem;
}

.info-card {
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 1.5rem;
}

.info-card h3 {
  color: #00ffff;
  margin: 0 0 1rem 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.info-grid div {
  padding: 0.75rem;
  background: rgba(0, 255, 255, 0.05);
  border-radius: 6px;
}

.description {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 255, 255, 0.1);
}

.description p {
  margin: 0.5rem 0 0 0;
  line-height: 1.6;
}

.table-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 6px;
  color: #fff;
  font-family: 'Courier New', monospace;
}

.search-input:focus {
  outline: none;
  border-color: #00ffff;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.btn-export {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #00ffff, #00ff88);
  border: none;
  border-radius: 6px;
  color: #000;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.4);
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 255, 0.2);
}

.ip-table {
  width: 100%;
  border-collapse: collapse;
}

.ip-table thead {
  background: rgba(0, 255, 255, 0.1);
}

.ip-table th {
  padding: 1rem;
  text-align: left;
  color: #00ffff;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.ip-table tbody tr {
  border-bottom: 1px solid rgba(0, 255, 255, 0.1);
  transition: background 0.2s;
}

.ip-table tbody tr:hover {
  background: rgba(0, 255, 255, 0.05);
}

.ip-table td {
  padding: 1rem;
}

.ip-table code {
  background: rgba(0, 255, 255, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  color: #00ffff;
}

.charts-grid {
  display: grid;
  gap: 2rem;
}

.chart-card {
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 1.5rem;
}

.chart-card h3 {
  color: #00ffff;
  margin: 0 0 1.5rem 0;
}

.bar-item {
  margin-bottom: 1rem;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.bar-label span:last-child {
  color: #00ffff;
  font-weight: 600;
}

.bar-track {
  height: 8px;
  background: rgba(0, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ffff, #00ff88);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-fill.isp {
  background: linear-gradient(90deg, #ff00ff, #ff0088);
}

.timeline {
  position: relative;
  padding-left: 2rem;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 0.5rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(0, 255, 255, 0.3);
}

.timeline-item {
  position: relative;
  margin-bottom: 2rem;
}

.timeline-marker {
  position: absolute;
  left: -1.75rem;
  top: 0.25rem;
  width: 12px;
  height: 12px;
  background: #00ffff;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.timeline-content {
  background: rgba(0, 255, 255, 0.03);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  padding: 1rem;
}

.timeline-content h4 {
  color: #00ffff;
  margin: 0 0 0.5rem 0;
}

.timeline-content p {
  margin: 0 0 0.5rem 0;
}

.timeline-content small {
  color: #666;
  font-size: 0.75rem;
}

.empty {
  text-align: center;
  padding: 3rem;
  color: #666;
}
</style>
