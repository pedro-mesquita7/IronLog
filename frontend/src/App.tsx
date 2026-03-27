import { lazy, Suspense } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { TimerProvider } from './context/TimerContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { NavBar } from './components/NavBar';
import { RestTimerOverlay } from './components/RestTimerOverlay';
import { OfflineIndicator } from './components/OfflineIndicator';
import { LoadingSpinner } from './components/LoadingSpinner';
import { LoginPage } from './features/login/LoginPage';
import { SessionStartPage } from './features/sessions/SessionStartPage';

const GuidedSetupPage = lazy(() => import('./features/setup/GuidedSetupPage').then(m => ({ default: m.GuidedSetupPage })));
const EquipmentListPage = lazy(() => import('./features/equipment/EquipmentListPage').then(m => ({ default: m.EquipmentListPage })));
const EquipmentFormPage = lazy(() => import('./features/equipment/EquipmentFormPage').then(m => ({ default: m.EquipmentFormPage })));
const ExerciseListPage = lazy(() => import('./features/exercises/ExerciseListPage').then(m => ({ default: m.ExerciseListPage })));
const ExerciseFormPage = lazy(() => import('./features/exercises/ExerciseFormPage').then(m => ({ default: m.ExerciseFormPage })));
const PlanListPage = lazy(() => import('./features/plans/PlanListPage').then(m => ({ default: m.PlanListPage })));
const PlanDetailPage = lazy(() => import('./features/plans/PlanDetailPage').then(m => ({ default: m.PlanDetailPage })));
const PlanFormPage = lazy(() => import('./features/plans/PlanFormPage').then(m => ({ default: m.PlanFormPage })));
const SessionPage = lazy(() => import('./features/sessions/SessionPage').then(m => ({ default: m.SessionPage })));
const SessionHistoryPage = lazy(() => import('./features/sessions/SessionHistoryPage').then(m => ({ default: m.SessionHistoryPage })));
const AnalyticsDashboardPage = lazy(() => import('./features/analytics/AnalyticsDashboardPage').then(m => ({ default: m.AnalyticsDashboardPage })));
const MorePage = lazy(() => import('./features/more/MorePage').then(m => ({ default: m.MorePage })));

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <OfflineIndicator />
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
          <Route path="/setup" element={<ProtectedRoute><GuidedSetupPage /></ProtectedRoute>} />
          <Route path="/" element={<ProtectedRoute><SessionStartPage /></ProtectedRoute>} />
          <Route path="/equipment" element={<ProtectedRoute><EquipmentListPage /></ProtectedRoute>} />
          <Route path="/equipment/new" element={<ProtectedRoute><EquipmentFormPage /></ProtectedRoute>} />
          <Route path="/equipment/:id/edit" element={<ProtectedRoute><EquipmentFormPage /></ProtectedRoute>} />
          <Route path="/exercises" element={<ProtectedRoute><ExerciseListPage /></ProtectedRoute>} />
          <Route path="/exercises/new" element={<ProtectedRoute><ExerciseFormPage /></ProtectedRoute>} />
          <Route path="/exercises/:id/edit" element={<ProtectedRoute><ExerciseFormPage /></ProtectedRoute>} />
          <Route path="/plans" element={<ProtectedRoute><PlanListPage /></ProtectedRoute>} />
          <Route path="/plans/new" element={<ProtectedRoute><PlanFormPage /></ProtectedRoute>} />
          <Route path="/plans/:id" element={<ProtectedRoute><PlanDetailPage /></ProtectedRoute>} />
          <Route path="/plans/:id/edit" element={<ProtectedRoute><PlanFormPage /></ProtectedRoute>} />
          <Route path="/sessions" element={<ProtectedRoute><SessionHistoryPage /></ProtectedRoute>} />
          <Route path="/sessions/:id" element={<ProtectedRoute><SessionPage /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><AnalyticsDashboardPage /></ProtectedRoute>} />
          <Route path="/more" element={<ProtectedRoute><MorePage /></ProtectedRoute>} />
        </Routes>
      </Suspense>
      {isAuthenticated && <RestTimerOverlay />}
      {isAuthenticated && <NavBar />}
    </>
  );
}

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <TimerProvider>
          <AppRoutes />
        </TimerProvider>
      </AuthProvider>
    </HashRouter>
  );
}
