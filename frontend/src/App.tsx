import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { ErrorBoundary } from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import IpLookupPage from './pages/IpLookupPage'
import IpListPage from './pages/IpListPage'
import AnalyticsPage from './pages/AnalyticsPage'
import MapPage from './pages/MapPage'
import FirDetailsPage from './pages/FirDetailsPage'
import MultiFileUploadPage from './pages/MultiFileUploadPage'
import ReportCreationPage from './pages/ReportCreationPage'
import IspLettersCatalogPage from './pages/IspLettersCatalogPage'
import TemplateBuilderPage from './pages/TemplateBuilderPage'
import AdminUsersPage from './pages/AdminUsersPage'
import PlaceholderPage from './pages/PlaceholderPage'

function HomeRedirect() {
  const { isAuthenticated } = useAuth()
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
}

function ProtectedLayout({ children }: { children: JSX.Element }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  )
}

function AdminLayout({ children }: { children: JSX.Element }) {
  const { user } = useAuth()
  if (user && user.role !== 'admin') return <Navigate to="/dashboard" replace />
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
        <Route path="/upload" element={<ProtectedLayout><UploadPage /></ProtectedLayout>} />
        <Route path="/ip-lookup" element={<ProtectedLayout><IpLookupPage /></ProtectedLayout>} />
        <Route path="/ip-list" element={<ProtectedLayout><IpListPage /></ProtectedLayout>} />
        <Route path="/analytics" element={<ProtectedLayout><AnalyticsPage /></ProtectedLayout>} />
        <Route path="/map" element={<ProtectedLayout><MapPage /></ProtectedLayout>} />
        <Route path="/fir/:firNumber" element={<ProtectedLayout><FirDetailsPage /></ProtectedLayout>} />

        <Route path="/multi-file-upload" element={<ProtectedLayout><MultiFileUploadPage /></ProtectedLayout>} />
        <Route path="/report-creation" element={<ProtectedLayout><ReportCreationPage /></ProtectedLayout>} />
        <Route path="/isp-letters" element={<ProtectedLayout><IspLettersCatalogPage /></ProtectedLayout>} />
        <Route path="/isp-letters/templates" element={<ProtectedLayout><TemplateBuilderPage /></ProtectedLayout>} />
        <Route path="/admin/users" element={<AdminLayout><AdminUsersPage /></AdminLayout>} />
        <Route path="/profile" element={<ProtectedLayout><PlaceholderPage title="Profile" /></ProtectedLayout>} />
        <Route path="/settings" element={<ProtectedLayout><PlaceholderPage title="Settings" /></ProtectedLayout>} />
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </ErrorBoundary>
  )
}
