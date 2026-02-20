import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { projectsAPI } from "../services/api";
import "./ProjectDetail.css";

const ProjectDetail = () => {
  const { projectId } = useParams();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runLoading, setRunLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedRuns, setSelectedRuns] = useState([]);

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [projectsData, runsData] = await Promise.all([
        projectsAPI.list(),
        projectsAPI.listRuns(projectId),
      ]);
      const proj = projectsData.find((p) => p.id === projectId);
      setProject(proj || null);
      setRuns(runsData);
    } catch (err) {
      setError("Failed to load project data");
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerRun = async () => {
    try {
      setRunLoading(true);
      setError("");
      const newRun = await projectsAPI.triggerRun(projectId);
      setRuns((prev) => [newRun, ...prev]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to trigger run");
    } finally {
      setRunLoading(false);
    }
  };

  const handleDeleteRun = async (runId) => {
    if (!window.confirm("Delete this run?")) return;
    try {
      await projectsAPI.deleteRun(projectId, runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
      setSelectedRuns((prev) => prev.filter((id) => id !== runId));
    } catch (err) {
      setError("Failed to delete run");
    }
  };

  const handleViewRun = async (runId) => {
    try {
      const run = await projectsAPI.getRun(projectId, runId);
      navigate("/results", {
        state: {
          projectData: {
            ...run,
            smell_analysis: run.smell_analysis,
            project_name: project?.name,
          },
        },
      });
    } catch (err) {
      setError("Failed to load run details");
    }
  };

  const handleSelectRun = (runId) => {
    setSelectedRuns((prev) => {
      if (prev.includes(runId)) return prev.filter((id) => id !== runId);
      if (prev.length >= 2) return [prev[1], runId];
      return [...prev, runId];
    });
  };

  const handleCompare = () => {
    if (selectedRuns.length !== 2) return;
    navigate(
      `/project/${projectId}/compare?run1=${selectedRuns[0]}&run2=${selectedRuns[1]}`
    );
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString();
  };

  const statusBadge = (status) => {
    const cls =
      status === "completed"
        ? "badge-success"
        : status === "failed"
        ? "badge-error"
        : "badge-pending";
    return <span className={`run-badge ${cls}`}>{status}</span>;
  };

  return (
    <div className="pd-container">
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

      <div className="pd-content">
        <div className="pd-header">
          <button className="back-button" onClick={() => navigate("/dashboard")}>
            ← Back to Dashboard
          </button>

          {project && (
            <div className="pd-project-info">
              <h2>{project.name}</h2>
              <a
                href={project.repo_url}
                target="_blank"
                rel="noreferrer"
                className="repo-link"
              >
                {project.repo_url}
              </a>
            </div>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="pd-actions">
          <button
            className="run-button"
            onClick={handleTriggerRun}
            disabled={runLoading}
          >
            {runLoading ? "⏳ Running analysis…" : "▶ Run New Analysis"}
          </button>

          {selectedRuns.length === 2 && (
            <button className="compare-button" onClick={handleCompare}>
              🔀 Compare Selected Runs
            </button>
          )}

          {selectedRuns.length > 0 && selectedRuns.length < 2 && (
            <span className="select-hint">
              Select one more run to compare ({2 - selectedRuns.length} needed)
            </span>
          )}
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading runs…</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="no-runs">
            <p>No runs yet. Click <strong>Run New Analysis</strong> to start.</p>
          </div>
        ) : (
          <div className="runs-table-container">
            <table className="runs-table">
              <thead>
                <tr>
                  <th>Select</th>
                  <th>Run #</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Files</th>
                  <th>Smells</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    className={selectedRuns.includes(run.id) ? "row-selected" : ""}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedRuns.includes(run.id)}
                        onChange={() => handleSelectRun(run.id)}
                        disabled={run.status !== "completed"}
                      />
                    </td>
                    <td>#{run.run_number}</td>
                    <td>{formatDate(run.created_at)}</td>
                    <td>{statusBadge(run.status)}</td>
                    <td>{run.summary?.total_files ?? "-"}</td>
                    <td>{run.summary?.total_smells ?? "-"}</td>
                    <td className="action-cell">
                      {run.status === "completed" && (
                        <button
                          className="view-btn"
                          onClick={() => handleViewRun(run.id)}
                        >
                          View
                        </button>
                      )}
                      <button
                        className="del-btn"
                        onClick={() => handleDeleteRun(run.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectDetail;
