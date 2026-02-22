import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { createProject, listProjects, deleteProject } from "../services/api";
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

  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch {
      // ignore
    } finally {
      setProjectsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

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
      {/* ── Top Navbar ─────────────────────────────────────────── */}
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
        {/* ── Sidebar ──────────────────────────────────────────── */}
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <button
              className="sidebar-item active"
              onClick={() => navigate("/dashboard")}
            >
              <span className="sidebar-icon">🏠</span>
              <span>Dashboard</span>
            </button>
            <button
              className="sidebar-item"
              onClick={() => navigate("/quick-analysis")}
            >
              <span className="sidebar-icon">⚡</span>
              <span>Quick Analysis</span>
            </button>
          </nav>
        </aside>

        {/* ── Main content ─────────────────────────────────────── */}
        <main className="main-content">
          <div className="content-header">
            <div>
              <h2 className="content-title">My Projects</h2>
              <p className="content-subtitle">
                Track GitHub repositories across multiple analysis runs
              </p>
            </div>
            <button
              className="new-project-btn"
              onClick={() => {
                setShowModal(true);
                setModalError("");
              }}
            >
              + New Project
            </button>
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
                className="new-project-btn"
                style={{ marginTop: 16 }}
                onClick={() => setShowModal(true)}
              >
                + Create First Project
              </button>
            </div>
          ) : (
            <div className="table-card">
              <table className="projects-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Project Name</th>
                    <th>Repository</th>
                    <th>Runs</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((project, idx) => (
                    <tr key={project.id}>
                      <td className="col-index">{idx + 1}</td>
                      <td className="col-name">
                        <span className="project-name-cell">
                          {project.name}
                        </span>
                      </td>
                      <td className="col-repo">
                        <a
                          href={project.repo_url}
                          target="_blank"
                          rel="noreferrer"
                          className="repo-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {project.repo_url.replace("https://github.com/", "")}
                        </a>
                      </td>
                      <td className="col-runs">
                        <span className="run-count-badge">
                          {project.run_count} run
                          {project.run_count !== 1 ? "s" : ""}
                        </span>
                      </td>
                      <td className="col-date">
                        {formatDate(project.created_at)}
                      </td>
                      <td className="col-actions">
                        <button
                          className="action-btn view-btn"
                          title="View project"
                          onClick={() =>
                            navigate(`/project/${project.id}`, {
                              state: {
                                projectName: project.name,
                                repoUrl: project.repo_url,
                              },
                            })
                          }
                        >
                          👁
                        </button>
                        <button
                          className="action-btn del-btn"
                          title="Delete project"
                          onClick={() => setDeleteConfirm(project.id)}
                        >
                          🗑
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
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
