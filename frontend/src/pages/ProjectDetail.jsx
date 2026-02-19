import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listRuns, triggerRun, deleteRun } from "../services/api";
import "./ProjectDetail.css";

const ProjectDetail = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { projectId } = useParams();
  const location = useLocation();

  const projectName = location.state?.projectName || "Project";
  const repoUrl = location.state?.repoUrl || "";

  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");
  const [selectedRuns, setSelectedRuns] = useState([]); // max 2 run IDs for comparison
  const [deleteRunConfirm, setDeleteRunConfirm] = useState(null); // run id pending delete

  useEffect(() => {
    fetchRuns();
  }, [projectId]);

  const fetchRuns = async () => {
    try {
      const data = await listRuns(projectId);
      setRuns(data);
      // Derive project name from state if available (passed via navigate)
    } catch {
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    setRunning(true);
    setRunError("");
    try {
      const run = await triggerRun(projectId);
      // Navigate directly to results of the new run
      navigate(`/project/${projectId}/run/${run.id}`, {
        state: { runData: run },
      });
    } catch (err) {
      setRunError(
        err.response?.data?.detail || "Analysis failed. Please try again.",
      );
      setRunning(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const toggleSelectRun = (runId) => {
    setSelectedRuns((prev) => {
      if (prev.includes(runId)) return prev.filter((id) => id !== runId);
      if (prev.length >= 2) return [prev[1], runId]; // shift out oldest
      return [...prev, runId];
    });
  };

  const handleDeleteRun = async (runId) => {
    try {
      await deleteRun(projectId, runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
      setSelectedRuns((prev) => prev.filter((id) => id !== runId));
    } catch {
      // silent
    } finally {
      setDeleteRunConfirm(null);
    }
  };

  const handleCompare = () => {
    if (selectedRuns.length !== 2) return;
    navigate(
      `/project/${projectId}/compare?run1=${selectedRuns[0]}&run2=${selectedRuns[1]}`,
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const statusChip = (status) => {
    const map = {
      completed: { label: "Completed", cls: "status-completed" },
      pending: { label: "Pending", cls: "status-pending" },
      failed: { label: "Failed", cls: "status-failed" },
    };
    const s = map[status] || { label: status, cls: "" };
    return <span className={`status-chip ${s.cls}`}>{s.label}</span>;
  };

  return (
    <div className="pd-container">
      {/* Navbar */}
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
        {/* Header */}
        <div className="pd-header">
          <button
            className="back-button"
            onClick={() => navigate("/dashboard")}
          >
            ← Back to Dashboard
          </button>
          <div className="pd-title-row">
            <div>
              <h2 className="pd-title">{projectName}</h2>
              {repoUrl && <p className="project-card-url">{repoUrl}</p>}
              <p className="pd-subtitle">
                Re-run the analysis to track how smell rankings change over time
              </p>
            </div>
            <button
              className="run-btn"
              onClick={handleRunAnalysis}
              disabled={running}
            >
              {running ? (
                <>
                  <span className="btn-spinner"></span> Analyzing…
                </>
              ) : (
                "🔄 Run Analysis"
              )}
            </button>
          </div>
          {running && (
            <div className="run-progress">
              <div className="spinner"></div>
              <p>
                Cloning repository and analyzing test smells… this may take a
                minute.
              </p>
            </div>
          )}
          {runError && <div className="error-message">{runError}</div>}
        </div>

        {/* Comparison bar */}
        {selectedRuns.length > 0 && (
          <div className="compare-bar">
            <span>
              {selectedRuns.length === 1
                ? "Select one more run to compare"
                : `Comparing Run #${runs.find((r) => r.id === selectedRuns[0])?.run_number} vs Run #${runs.find((r) => r.id === selectedRuns[1])?.run_number}`}
            </span>
            <div className="compare-bar-actions">
              {selectedRuns.length === 2 && (
                <button className="compare-btn" onClick={handleCompare}>
                  ⚖️ Compare
                </button>
              )}
              <button className="clear-btn" onClick={() => setSelectedRuns([])}>
                Clear
              </button>
            </div>
          </div>
        )}

        {/* Runs table */}
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading runs…</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <h3>No runs yet</h3>
            <p>
              Click "Run Analysis" to perform the first analysis of this
              repository.
            </p>
          </div>
        ) : (
          <div className="runs-table-wrapper">
            <p className="compare-hint">
              Tick two checkboxes to compare runs side by side.
            </p>
            <table className="runs-table">
              <thead>
                <tr>
                  <th>Compare</th>
                  <th>Run</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Files</th>
                  <th>Smells</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    className={
                      selectedRuns.includes(run.id) ? "row-selected" : ""
                    }
                  >
                    <td>
                      {run.status === "completed" && (
                        <input
                          type="checkbox"
                          className="run-checkbox"
                          checked={selectedRuns.includes(run.id)}
                          onChange={() => toggleSelectRun(run.id)}
                        />
                      )}
                    </td>
                    <td>
                      <span className="run-number">#{run.run_number}</span>
                    </td>
                    <td className="run-date">{formatDate(run.created_at)}</td>
                    <td>{statusChip(run.status)}</td>
                    <td>{run.summary?.total_files ?? "—"}</td>
                    <td>{run.summary?.total_smells ?? "—"}</td>
                    <td className="action-cell">
                      {run.status === "completed" && (
                        <button
                          className="view-btn"
                          onClick={() =>
                            navigate(`/project/${projectId}/run/${run.id}`)
                          }
                        >
                          View Results
                        </button>
                      )}
                      {run.status === "failed" && (
                        <span className="error-hint" title={run.error}>
                          Failed
                        </span>
                      )}
                      <button
                        className="del-run-btn"
                        title="Delete run"
                        onClick={() => setDeleteRunConfirm(run.id)}
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
      </div>
      {/* ── Delete Run Confirmation ───────────────────────────────── */}
      {deleteRunConfirm && (
        <div
          className="modal-overlay"
          onClick={() => setDeleteRunConfirm(null)}
        >
          <div
            className="modal-box confirm-box"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Delete Run?</h3>
            <p>This will permanently delete this run and its results.</p>
            <div className="confirm-actions">
              <button
                className="btn-danger"
                onClick={() => handleDeleteRun(deleteRunConfirm)}
              >
                Delete
              </button>
              <button
                className="btn-secondary"
                onClick={() => setDeleteRunConfirm(null)}
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

export default ProjectDetail;
