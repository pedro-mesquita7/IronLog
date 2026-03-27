import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { TimerProvider } from './context/TimerContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { NavBar } from './components/NavBar';
import { RestTimerOverlay } from './components/RestTimerOverlay';
import { OfflineIndicator } from './components/OfflineIndicator';
import { LoginPage } from './features/login/LoginPage';
import { GuidedSetupPage } from './features/setup/GuidedSetupPage';
import { EquipmentListPage } from './features/equipment/EquipmentListPage';
import { EquipmentFormPage } from './features/equipment/EquipmentFormPage';
import { ExerciseListPage } from './features/exercises/ExerciseListPage';
import { ExerciseFormPage } from './features/exercises/ExerciseFormPage';
import { PlanListPage } from './features/plans/PlanListPage';
import { PlanDetailPage } from './features/plans/PlanDetailPage';
import { PlanFormPage } from './features/plans/PlanFormPage';
import { SessionStartPage } from './features/sessions/SessionStartPage';
import { SessionPage } from './features/sessions/SessionPage';
import { SessionHistoryPage } from './features/sessions/SessionHistoryPage';
import { AnalyticsDashboardPage } from './features/analytics/AnalyticsDashboardPage';

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <OfflineIndicator />
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
      </Routes>
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
