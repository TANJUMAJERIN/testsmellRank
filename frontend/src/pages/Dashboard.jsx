import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import {
  uploadZipFile,
  createProject,
  listProjects,
  deleteProject,
} from "../services/api";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Project list state
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);

  // New project modal state
  const [showModal, setShowModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");

  // ZIP one-off state
  const [zipFile, setZipFile] = useState(null);
  const [zipLoading, setZipLoading] = useState(false);
  const [zipError, setZipError] = useState("");

  const [deleteConfirm, setDeleteConfirm] = useState(null); // project id awaiting confirm

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch {
      // ignore — user will see empty state
    } finally {
      setProjectsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // ── Create new project ──────────────────────────────────────────
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) {
      setModalError("Project name is required");
      return;
    }
    if (!newRepoUrl.trim()) {
      setModalError("GitHub URL is required");
      return;
    }

    setModalLoading(true);
    setModalError("");
    try {
      const project = await createProject(
        newProjectName.trim(),
        newRepoUrl.trim(),
      );
      setProjects((prev) => [project, ...prev]);
      setShowModal(false);
      setNewProjectName("");
      setNewRepoUrl("");
      navigate(`/project/${project.id}`, {
        state: { projectName: project.name, repoUrl: project.repo_url },
      });
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to create project");
    } finally {
      setModalLoading(false);
    }
  };

  // ── Delete project ──────────────────────────────────────────────
  const handleDelete = async (projectId) => {
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch {
      // silent
    } finally {
      setDeleteConfirm(null);
    }
  };

  // ── ZIP one-off upload ──────────────────────────────────────────
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

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="dashboard-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Test Smell Rank</h1>
          <div className="navbar-right">
            <span className="user-name">Welcome, {user?.full_name}!</span>
            <button
              className="new-project-btn"
              onClick={() => {
                setShowModal(true);
                setModalError("");
              }}
            >
              ➕ New Project
            </button>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-content">
        {/* ── Projects Section ─────────────────────────────────── */}
        <div className="section-header">
          <h2>My Projects</h2>
          <p className="section-subtitle">
            Each project tracks a GitHub repository across multiple analysis
            runs
          </p>
        </div>

        {projectsLoading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading projects…</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🧪</div>
            <h3>No projects yet</h3>
            <p>
              Create your first project to start tracking test smell rankings
              over time.
            </p>
            <button
              className="new-project-btn large"
              onClick={() => setShowModal(true)}
            >
              ➕ Create First Project
            </button>
          </div>
        ) : (
          <div className="projects-grid">
            {projects.map((project) => (
              <div
                key={project.id}
                className="project-card"
                onClick={() =>
                  navigate(`/project/${project.id}`, {
                    state: {
                      projectName: project.name,
                      repoUrl: project.repo_url,
                    },
                  })
                }
              >
                <div className="project-card-header">
                  <span className="source-badge github">🔗 GitHub</span>
                  <button
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteConfirm(project.id);
                    }}
                    title="Delete project"
                  >
                    🗑
                  </button>
                </div>
                <h3 className="project-card-name">{project.name}</h3>
                <p className="project-card-url" title={project.repo_url}>
                  {project.repo_url.replace("https://github.com/", "")}
                </p>
                <div className="project-card-footer">
                  <span className="run-count-badge">
                    {project.run_count} run{project.run_count !== 1 ? "s" : ""}
                  </span>
                  <span className="project-date">
                    {formatDate(project.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── ZIP Quick Analysis ────────────────────────────────── */}
        <div className="zip-section">
          <div className="zip-card">
            <div className="upload-header">
              <span className="upload-icon">📦</span>
              <div>
                <h3>Quick Analysis — ZIP File</h3>
                <p className="upload-description">
                  One-off analysis without saving history
                </p>
              </div>
            </div>
            {zipError && <div className="error-message">{zipError}</div>}
            <form onSubmit={handleZipSubmit} className="zip-form">
              <input
                type="file"
                className="upload-input file-input"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files[0])}
                disabled={zipLoading}
              />
              <button
                type="submit"
                className="upload-button"
                disabled={zipLoading}
              >
                {zipLoading ? "Uploading…" : "Analyze ZIP"}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* ── New Project Modal ─────────────────────────────────── */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Project</h3>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>
            {modalError && <div className="error-message">{modalError}</div>}
            <form onSubmit={handleCreateProject} className="modal-form">
              <label>Project Name</label>
              <input
                type="text"
                className="upload-input"
                placeholder="e.g. Flask Repository"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                disabled={modalLoading}
                autoFocus
              />
              <label>GitHub Repository URL</label>
              <input
                type="text"
                className="upload-input"
                placeholder="https://github.com/username/repository"
                value={newRepoUrl}
                onChange={(e) => setNewRepoUrl(e.target.value)}
                disabled={modalLoading}
              />
              <button
                type="submit"
                className="upload-button"
                disabled={modalLoading}
              >
                {modalLoading ? "Creating…" : "Create Project"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation ───────────────────────────────── */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div
            className="modal-box confirm-box"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Delete Project?</h3>
            <p>
              This will permanently delete the project and all its run history.
            </p>
            <div className="confirm-actions">
              <button
                className="btn-danger"
                onClick={() => handleDelete(deleteConfirm)}
              >
                Delete
              </button>
              <button
                className="btn-secondary"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
