import React from "react";
import { useNavigate } from "react-router-dom";
import "./Landing.css";

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      {/* Header */}
      <header className="landing-header">
        <h1 className="brand-title">Test Smell Rank</h1>
        <div className="auth-buttons">
          <button 
            className="btn btn-login"
            onClick={() => navigate("/login")}
          >
            Login
          </button>
          <button 
            className="btn btn-register"
            onClick={() => navigate("/register")}
          >
            Register
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="landing-content">
        <div className="hero-section">
          <h2 className="hero-title">Detect Test Smells in Your Code</h2>
          <p className="hero-subtitle">
            Analyze and rank test smells in your Python projects with our advanced detection system
          </p>
          <p className="hero-cta">
            Upload your project or provide a GitHub repository link to get started
          </p>
        </div>

        {/* Features */}
        <div className="features">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3 className="feature-title">Smart Detection</h3>
            <p className="feature-description">
              Automatically detect test smells in Python projects
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">Detailed Analysis</h3>
            <p className="feature-description">
              Get comprehensive reports and rankings
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3 className="feature-title">Fast Processing</h3>
            <p className="feature-description">
              Quick analysis of your entire test suite
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
