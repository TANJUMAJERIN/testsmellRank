import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { uploadZipFile, uploadGithubRepo } from "../services/api";
import "./Dashboard.css";

const QuickAnalysis = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [quickMode, setQuickMode] = useState("zip"); // "zip" | "github"

  // ZIP state
  const [zipFile, setZipFile] = useState(null);
  const [zipLoading, setZipLoading] = useState(false);
  const [zipError, setZipError] = useState("");

  // GitHub state
  const [quickGithubUrl, setQuickGithubUrl] = useState("");
  const [quickGithubLoading, setQuickGithubLoading] = useState(false);
  const [quickGithubError, setQuickGithubError] = useState("");

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleZipSubmit = async (e) => {
    e.preventDefault();
    if (!zipFile) {
      setZipError("Please select a ZIP file");
      return;
    }
    setZipLoading(true);
    setZipError("");
    try {
      const response = await uploadZipFile(zipFile);
      setZipFile(null);
      e.target.reset();
      navigate("/results", { state: { projectData: response } });
    } catch (err) {
      setZipError(err.response?.data?.detail || "Failed to upload ZIP file");
    } finally {
      setZipLoading(false);
    }
  };

  const handleQuickGithubSubmit = async (e) => {
    e.preventDefault();
    if (!quickGithubUrl.trim()) {
      setQuickGithubError("Please enter a GitHub URL");
      return;
    }
    setQuickGithubLoading(true);
    setQuickGithubError("");
    try {
      const response = await uploadGithubRepo(quickGithubUrl.trim());
      setQuickGithubUrl("");
      navigate("/results", { state: { projectData: response } });
    } catch (err) {
      setQuickGithubError(
        err.response?.data?.detail || "Failed to analyse repository",
      );
    } finally {
      setQuickGithubLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      {/* ── Navbar ─────────────────────────────────────────────── */}
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Test Smell Rank</h1>
          <div className="navbar-right">
            <span className="user-name">Welcome, {user?.full_name}!</span>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-layout">
        {/* ── Sidebar ───────────────────────────────────────────── */}
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <button
              className="sidebar-item"
              onClick={() => navigate("/dashboard")}
            >
              <span className="sidebar-icon">🏠</span>
              <span>Dashboard</span>
            </button>
            <button className="sidebar-item active">
              <span className="sidebar-icon">⚡</span>
              <span>Quick Analysis</span>
            </button>
          </nav>
        </aside>

        {/* ── Main content ──────────────────────────────────────── */}
        <main className="main-content">
          <div className="content-header">
            <div>
              <h2 className="content-title">Quick Analysis</h2>
              <p className="content-subtitle">
                One-off analysis — results are not saved to history
              </p>
            </div>
          </div>

          {/* Mode toggle */}
          <div className="quick-mode-toggle">
            <button
              className={`quick-mode-btn ${quickMode === "zip" ? "active" : ""}`}
              onClick={() => {
                setQuickMode("zip");
                setZipError("");
                setQuickGithubError("");
              }}
            >
              📦 ZIP File
            </button>
            <button
              className={`quick-mode-btn ${quickMode === "github" ? "active" : ""}`}
              onClick={() => {
                setQuickMode("github");
                setZipError("");
                setQuickGithubError("");
              }}
            >
              🔗 GitHub URL
            </button>
          </div>

          {quickMode === "zip" && (
            <div className="quick-card">
              <div className="quick-card-icon">📦</div>
              <h3>Upload a ZIP File</h3>
              <p className="quick-card-desc">
                Upload a ZIP containing your Python project. Test smells will be
                detected and ranked immediately. Results won't be stored — use{" "}
                <strong>Projects</strong> for tracked history.
              </p>

              {zipError && <div className="error-message">{zipError}</div>}

              <form onSubmit={handleZipSubmit} className="quick-form">
                <div className="file-drop-area">
                  <input
                    type="file"
                    id="zip-input"
                    className="file-input-hidden"
                    accept=".zip"
                    onChange={(e) => setZipFile(e.target.files[0])}
                    disabled={zipLoading}
                  />
                  <label htmlFor="zip-input" className="file-label">
                    {zipFile ? (
                      <>
                        <span className="file-chosen-icon">✅</span>{" "}
                        {zipFile.name}
                      </>
                    ) : (
                      <>
                        <span className="file-chosen-icon">📁</span> Click to
                        choose a .zip file
                      </>
                    )}
                  </label>
                </div>
                <button
                  type="submit"
                  className="upload-button"
                  disabled={zipLoading || !zipFile}
                >
                  {zipLoading ? (
                    <>
                      <span className="btn-spinner-white"></span> Analyzing…
                    </>
                  ) : (
                    "⚡ Run Analysis"
                  )}
                </button>
              </form>
            </div>
          )}

          {quickMode === "github" && (
            <div className="quick-card">
              <div className="quick-card-icon">🔗</div>
              <h3>Analyse a GitHub Repository</h3>
              <p className="quick-card-desc">
                Enter a public GitHub repository URL. Test smells will be
                detected and ranked immediately. Results won't be stored — use{" "}
                <strong>Projects</strong> for tracked history.
              </p>

              {quickGithubError && (
                <div className="error-message">{quickGithubError}</div>
              )}

              <form onSubmit={handleQuickGithubSubmit} className="quick-form">
                <input
                  type="text"
                  className="upload-input"
                  placeholder="https://github.com/username/repository"
                  value={quickGithubUrl}
                  onChange={(e) => setQuickGithubUrl(e.target.value)}
                  disabled={quickGithubLoading}
                  style={{ width: "100%" }}
                />
                <button
                  type="submit"
                  className="upload-button"
                  disabled={quickGithubLoading || !quickGithubUrl.trim()}
                >
                  {quickGithubLoading ? (
                    <>
                      <span className="btn-spinner-white"></span> Analyzing…
                    </>
                  ) : (
                    "⚡ Run Analysis"
                  )}
                </button>
              </form>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default QuickAnalysis;
