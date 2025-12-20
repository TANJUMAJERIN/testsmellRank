import React from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="dashboard-container">
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Test Smell Rank</h1>
          <div className="navbar-right">
            <span className="user-name">Welcome, {user?.full_name}</span>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="welcome-card">
          <h2>Welcome to Test Smell Rank Dashboard</h2>
          <p>Analyze and rank test smells in your codebase</p>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🧪</div>
            <h3>Total Tests</h3>
            <p className="stat-number">0</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <h3>Test Smells</h3>
            <p className="stat-number">0</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <h3>Analysis Done</h3>
            <p className="stat-number">0</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <h3>Issues Fixed</h3>
            <p className="stat-number">0</p>
          </div>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <h3>🔍 Smell Detection</h3>
            <p>Automatically detect test smells in your test suite</p>
            <button className="feature-button">Start Detection</button>
          </div>

          <div className="feature-card">
            <h3>📈 Ranking Analysis</h3>
            <p>Get detailed rankings of test smell severity</p>
            <button className="feature-button">View Rankings</button>
          </div>

          <div className="feature-card">
            <h3>📝 Reports</h3>
            <p>Generate comprehensive test smell reports</p>
            <button className="feature-button">Generate Report</button>
          </div>

          <div className="feature-card">
            <h3>⚙️ Settings</h3>
            <p>Configure detection rules and preferences</p>
            <button className="feature-button">Open Settings</button>
          </div>
        </div>

        <div className="info-section">
          <h3>Detected Test Smells</h3>
          <div className="smell-types">
            <div className="smell-badge">Assertion Roulette</div>
            <div className="smell-badge">Empty Test</div>
            <div className="smell-badge">Magic Number</div>
            <div className="smell-badge">Conditional Test</div>
            <div className="smell-badge">Lazy Test</div>
            <div className="smell-badge">Duplicate Code</div>
            <div className="smell-badge">Resource Optimism</div>
            <div className="smell-badge">Verbose Test</div>
            <div className="smell-badge">Slow Test</div>
            <div className="smell-badge">Flaky Test</div>
            <div className="smell-badge">Exception Handling</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
