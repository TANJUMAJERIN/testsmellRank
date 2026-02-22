import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { projectsAPI } from "../services/api";
import "./ProjectDetail.css";

const ProjectDetail = () => {
  const { projectId } = useParams();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [project, setProject] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runLoading, setRunLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedRuns, setSelectedRuns] = useState([]);
  const [deleteRunConfirm, setDeleteRunConfirm] = useState(null);
  const [surveyPanelRunId, setSurveyPanelRunId] = useState(null);
  const [surveyData, setSurveyData] = useState({}); // { runId: surveyDoc }
  const [surveyLoading, setSurveyLoading] = useState({}); // { runId: bool }

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
    setRunLoading(true);
    setError("");
    try {
      const run = await projectsAPI.triggerRun(projectId);
      setRuns((prev) => [run, ...prev]);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Analysis failed. Please try again.",
      );
    } finally {
      setRunLoading(false);
    }
  };

  const handleDeleteRun = async (runId) => {
    try {
      await projectsAPI.deleteRun(projectId, runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
      setSelectedRuns((prev) => prev.filter((id) => id !== runId));
    } catch {
      setError("Failed to delete run");
    } finally {
      setDeleteRunConfirm(null);
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

  const toggleSelectRun = (runId) => {
    setSelectedRuns((prev) => {
      if (prev.includes(runId)) return prev.filter((id) => id !== runId);
      if (prev.length >= 2) return [prev[1], runId];
      return [...prev, runId];
    });
  };

  const handleCompare = () => {
    if (selectedRuns.length !== 2) return;
    navigate(
      `/project/${projectId}/compare?run1=${selectedRuns[0]}&run2=${selectedRuns[1]}`,
    );
  };

  const handleToggleSurveyPanel = async (runId) => {
    if (surveyPanelRunId === runId) {
      setSurveyPanelRunId(null);
      return;
    }
    setSurveyPanelRunId(runId);
    // Load existing survey status if not already loaded
    if (!surveyData[runId]) {
      setSurveyLoading((prev) => ({ ...prev, [runId]: true }));
      try {
        const data = await projectsAPI.getSurveyStatus(projectId, runId);
        // exists:false means no survey started yet — leave surveyData null so panel shows Send button
        if (data.exists !== false) {
          setSurveyData((prev) => ({ ...prev, [runId]: data }));
        }
      } catch {
        // network error — ignore, panel will show Send button
      } finally {
        setSurveyLoading((prev) => ({ ...prev, [runId]: false }));
      }
    }
  };

  const handleStartSurvey = async (runId) => {
    setSurveyLoading((prev) => ({ ...prev, [runId]: true }));
    try {
      const data = await projectsAPI.startSurvey(projectId, runId);
      setSurveyData((prev) => ({ ...prev, [runId]: data }));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start survey");
    } finally {
      setSurveyLoading((prev) => ({ ...prev, [runId]: false }));
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
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

  const projectName = project?.name || location.state?.projectName || "Project";
  const repoUrl = project?.repo_url || location.state?.repoUrl || "";

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
          <button
            className="back-button"
            onClick={() => navigate("/dashboard")}
          >
            Back to Dashboard
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
              onClick={handleTriggerRun}
              disabled={runLoading}
            >
              {runLoading ? (
                <>
                  <span className="btn-spinner"></span> Analyzing
                </>
              ) : (
                "Run Analysis"
              )}
            </button>
          </div>
          {runLoading && (
            <div className="run-progress">
              <div className="spinner"></div>
              <p>
                Cloning repository and analyzing test smells this may take a
                minute.
              </p>
            </div>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>

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
                  Compare
                </button>
              )}
              <button className="clear-btn" onClick={() => setSelectedRuns([])}>
                Clear
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading runs</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"></div>
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
                  <th>Survey</th>
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
                    <td>{run.summary?.total_files ?? ""}</td>
                    <td>{run.summary?.total_smells ?? ""}</td>
                    <td className="action-cell">
                      {run.status === "completed" && (
                        <button
                          className="view-btn"
                          onClick={() => handleViewRun(run.id)}
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
                        Delete
                      </button>
                    </td>
                    <td>
                      {run.status === "completed" && (
                        <button
                          className="view-btn"
                          style={{
                            background:
                              surveyPanelRunId === run.id
                                ? "#764ba2"
                                : undefined,
                          }}
                          onClick={() => handleToggleSurveyPanel(run.id)}
                        >
                          {surveyPanelRunId === run.id
                            ? "Hide Survey"
                            : "Survey"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Survey Panel — shown when a run's Survey button is clicked ── */}
        {surveyPanelRunId && (
          <SurveyPanel
            projectId={projectId}
            runId={surveyPanelRunId}
            survey={surveyData[surveyPanelRunId] || null}
            loading={surveyLoading[surveyPanelRunId] || false}
            onStart={() => handleStartSurvey(surveyPanelRunId)}
            onViewQuadrant={() =>
              navigate(
                `/project/${projectId}/runs/${surveyPanelRunId}/quadrant`,
              )
            }
          />
        )}
      </div>
      {/* end pd-content */}

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

// ── Survey Panel ─────────────────────────────────────────────────────────────
const SurveyPanel = ({
  projectId,
  runId,
  survey,
  loading,
  onStart,
  onViewQuadrant,
}) => {
  const submitted = survey?.submitted_count ?? 0;
  const total = survey?.total ?? 0;
  const hasSurvey = !!survey;
  const hasDDS = !!survey?.dds;
  const dispatchInfo = survey?.email_dispatch;

  return (
    <div
      style={{
        margin: "20px 0 4px",
        background: "#f8f7ff",
        border: "1.5px solid #d0caf5",
        borderRadius: "12px",
        padding: "24px",
      }}
    >
      <h3 style={{ margin: "0 0 6px", color: "#4a3fa0", fontSize: "1rem" }}>
        🧑‍💻 Developer Survey
      </h3>
      <p style={{ margin: "0 0 16px", color: "#777", fontSize: "0.85rem" }}>
        Send a perception survey to contributors extracted from this run's git
        history. Their 1–5 Likert ratings produce a Developer-Driven Score (DDS)
        combined with the empirical Prioritization Score (PS) to classify smells
        into the Technical Debt Quadrant.
      </p>

      {loading && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            color: "#667eea",
          }}
        >
          <span
            style={{
              width: 20,
              height: 20,
              border: "3px solid #e0e0e0",
              borderTopColor: "#667eea",
              borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.75s linear infinite",
            }}
          />
          Loading survey status…
        </div>
      )}

      {!loading && (
        <>
          {/* No survey yet */}
          {!hasSurvey && (
            <button
              onClick={onStart}
              style={{
                background: "linear-gradient(135deg, #667eea, #764ba2)",
                color: "white",
                border: "none",
                padding: "10px 24px",
                borderRadius: "8px",
                fontWeight: 700,
                fontSize: "0.9rem",
                cursor: "pointer",
              }}
            >
              📧 Send Survey to Contributors
            </button>
          )}

          {/* Survey already exists */}
          {hasSurvey && (
            <div>
              {/* Email dispatch result */}
              {dispatchInfo && (
                <div
                  style={{
                    background: dispatchInfo.skipped ? "#fff8e1" : "#e8f5e9",
                    border: `1px solid ${dispatchInfo.skipped ? "#ffe082" : "#a5d6a7"}`,
                    borderRadius: 8,
                    padding: "10px 14px",
                    marginBottom: 14,
                    fontSize: "0.85rem",
                    color: dispatchInfo.skipped ? "#795548" : "#2e7d32",
                  }}
                >
                  {dispatchInfo.skipped
                    ? "⚠️ Email credentials not configured — survey links were created but emails were not sent. Configure MAIL_USERNAME / MAIL_PASSWORD in .env to enable sending."
                    : `✅ ${dispatchInfo.sent} email(s) sent · ${dispatchInfo.failed} failed`}
                </div>
              )}

              {/* Contributors */}
              <div style={{ marginBottom: 16 }}>
                <div
                  style={{
                    fontWeight: 700,
                    color: "#444",
                    marginBottom: 8,
                    fontSize: "0.88rem",
                  }}
                >
                  Contributors ({total}) — {submitted} submitted /{" "}
                  {total - submitted} pending
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {(survey.contributors || []).map((c) => (
                    <span
                      key={c.email}
                      style={{
                        background: c.submitted ? "#e8f5e9" : "#f5f5f5",
                        border: `1px solid ${c.submitted ? "#a5d6a7" : "#ddd"}`,
                        borderRadius: 20,
                        padding: "4px 12px",
                        fontSize: "0.8rem",
                        color: c.submitted ? "#2e7d32" : "#666",
                      }}
                    >
                      {c.submitted ? "✓ " : "⏳ "}
                      {c.name}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button
                  onClick={onStart}
                  style={{
                    background: "white",
                    border: "1.5px solid #667eea",
                    color: "#667eea",
                    padding: "8px 18px",
                    borderRadius: 8,
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  🔄 Re-send Survey
                </button>
                {hasDDS && (
                  <button
                    onClick={onViewQuadrant}
                    style={{
                      background: "linear-gradient(135deg, #667eea, #764ba2)",
                      border: "none",
                      color: "white",
                      padding: "8px 18px",
                      borderRadius: 8,
                      fontWeight: 700,
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    📊 View Quadrant Results
                  </button>
                )}
                {!hasDDS && (
                  <span
                    style={{
                      fontSize: "0.82rem",
                      color: "#aaa",
                      alignSelf: "center",
                    }}
                  >
                    Quadrant results will appear after the first submission
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
