import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import QuickAnalysis from "./pages/QuickAnalysis";
import Results from "./pages/Results";
import ProjectDetail from "./pages/ProjectDetail";
import Compare from "./pages/Compare";
import Survey from "./pages/Survey";
import QuadrantResults from "./pages/QuadrantResults";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quick-analysis"
            element={
              <ProtectedRoute>
                <QuickAnalysis />
              </ProtectedRoute>
            }
          />
          <Route
            path="/results"
            element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project/:projectId/run/:runId"
            element={
              <ProtectedRoute>
                <Results />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project/:projectId/compare"
            element={
              <ProtectedRoute>
                <Compare />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project/:projectId/runs/:runId/quadrant"
            element={
              <ProtectedRoute>
                <QuadrantResults />
              </ProtectedRoute>
            }
          />
          {/* Public survey page — no auth */}
          <Route path="/survey/:token" element={<Survey />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
