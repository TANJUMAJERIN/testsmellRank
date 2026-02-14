import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { uploadGithubRepo, uploadZipFile } from "../services/api";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [githubUrl, setGithubUrl] = useState("");
  const [zipFile, setZipFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleGithubSubmit = async (e) => {
    e.preventDefault();

    if (!githubUrl) {
      setError("Please enter a GitHub repository URL");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await uploadGithubRepo(githubUrl);

      setMessage(response.message || "Repository uploaded successfully!");
      setGithubUrl("");

      // Directly navigate with backend response
      navigate("/results", { state: { projectData: response } });

    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to upload repository"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleZipSubmit = async (e) => {
    e.preventDefault();

    if (!zipFile) {
      setError("Please select a ZIP file");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await uploadZipFile(zipFile);

      setMessage(response.message || "ZIP file uploaded successfully!");
      setZipFile(null);
      e.target.reset();

      // Directly navigate with backend response
      navigate("/results", { state: { projectData: response } });

    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to upload ZIP file"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Test Smell Rank</h1>
          <div className="navbar-right">
            <span className="user-name">
              Welcome, {user?.full_name}!
            </span>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="welcome-message">
          <h2>👋 Welcome back, {user?.full_name}!</h2>
          <p>Upload your Python project to analyze test smells</p>
        </div>

        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}

        <div className="upload-section">

          {/* GitHub Upload */}
          <div className="upload-card">
            <div className="upload-header">
              <span className="upload-icon">🔗</span>
              <h3>Upload from GitHub</h3>
            </div>

            <p className="upload-description">
              Provide a GitHub repository URL to analyze
            </p>

            <form onSubmit={handleGithubSubmit}>
              <input
                type="text"
                className="upload-input"
                placeholder="https://github.com/username/repository"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="upload-button"
                disabled={loading}
              >
                {loading ? "Uploading..." : "Upload Repository"}
              </button>
            </form>
          </div>

          {/* ZIP Upload */}
          <div className="upload-card">
            <div className="upload-header">
              <span className="upload-icon">📦</span>
              <h3>Upload ZIP File</h3>
            </div>

            <p className="upload-description">
              Upload a ZIP file containing your Python project
            </p>

            <form onSubmit={handleZipSubmit}>
              <input
                type="file"
                className="upload-input file-input"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files[0])}
                disabled={loading}
              />
              <button
                type="submit"
                className="upload-button"
                disabled={loading}
              >
                {loading ? "Uploading..." : "Upload ZIP File"}
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
