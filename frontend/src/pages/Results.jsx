import React, { useState, useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  getRun,
  getSurveyStatus,
  forceCalculateDds,
  getSurveyResults,
} from "../services/api";
import "./Results.css";

const SMELL_NAMES = {
  CTL:  "Conditional Test Logic",
  AR:   "Assertion Roulette",
  DA:   "Duplicate Assert",
  MNT:  "Magic Number Test",
  OS:   "Obscure In-Line Setup",
  RA:   "Redundant Assertion",
  EH:   "Exception Handling",
  CI:   "Constructor Initialization",
  SA:   "Suboptimal Assert",
  TM:   "Test Maverick",
  RP:   "Redundant Print",
  GF:   "General Fixture",
  ST:   "Sleepy Test",
  ET:   "Empty Test",
  LCTC: "Lack of Cohesion of Test Cases",
};

const Results = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId, runId } = useParams();

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState(null);
  const [uniqueSmells, setUniqueSmells] = useState([]);
  const [runMeta, setRunMeta] = useState(null);

  // Survey state
  const [surveyStatus, setSurveyStatus] = useState(null);
  const [surveyLoading, setSurveyLoading] = useState(false);
  const [ddsResults, setDdsResults] = useState(null);
  const [quadrantResults, setQuadrantResults] = useState(null);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [calculatingDds, setCalculatingDds] = useState(false);
  const [surveyMsg, setSurveyMsg] = useState("");

  const projectData = location.state?.projectData;
  const stateRunData = location.state?.runData;

  useEffect(() => {
    const processAnalysis = (analysis) => {
      const smellMap = new Map();
      analysis.details?.forEach((fileResult) => {
        fileResult.smells?.forEach((smell) => {
          const count = smellMap.get(smell.type) || 0;
          smellMap.set(smell.type, count + 1);
        });
      });
      const uniqueSmellsArray = Array.from(smellMap.entries())
        .map(([type, count]) => ({ type, count }))
        .sort((a, b) => b.count - a.count);
      setUniqueSmells(uniqueSmellsArray);
      setResults(analysis);
      setLoading(false);
    };

    // Case 1: loaded from project run URL (/project/:id/run/:runId)
    if (projectId && runId) {
      // If we have fresh run data in state, use it directly (avoids extra API call)
      if (stateRunData?.smell_analysis) {
        setRunMeta(stateRunData);
        processAnalysis(stateRunData.smell_analysis);
        return;
      }
      // Otherwise fetch from API (e.g. when user revisits the URL)
      getRun(projectId, runId)
        .then((run) => {
          setRunMeta(run);
          if (run.smell_analysis) {
            processAnalysis(run.smell_analysis);
          } else {
            setLoading(false);
          }
        })
        .catch(() => navigate(`/project/${projectId}`));
      return;
    }

    // Case 2: fresh upload via router state (ZIP or one-off GitHub)
    if (projectData?.smell_analysis) {
      processAnalysis(projectData.smell_analysis);
      return;
    }

    navigate("/dashboard");
  }, [projectData, stateRunData, projectId, runId, navigate]);

  // Load survey status whenever a project run is being viewed
  useEffect(() => {
    if (!projectId || !runId) return;
    setSurveyLoading(true);
    getSurveyStatus(projectId, runId)
      .then((data) => {
        setSurveyStatus(data);
        if (data.dds_ready) {
          getSurveyResults(projectId, runId)
            .then((res) => {
              setDdsResults(res.dds_results);
              setQuadrantResults(res.quadrant_results);
            })
            .catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setSurveyLoading(false));
  }, [projectId, runId]);

  // Auto-poll every 10 s while survey is in "sent" state and DDS not yet ready
  useEffect(() => {
    if (!projectId || !runId) return;
    if (!surveyStatus) return;
    if (surveyStatus.survey_status !== "sent") return;
    if (surveyStatus.dds_ready) return;

    const interval = setInterval(async () => {
      try {
        const data = await getSurveyStatus(projectId, runId);
        setSurveyStatus(data);
        if (data.dds_ready) {
          clearInterval(interval);
          const res = await getSurveyResults(projectId, runId);
          setDdsResults(res.dds_results);
          setQuadrantResults(res.quadrant_results);
        }
      } catch (_) {}
    }, 10000);

    return () => clearInterval(interval);
  }, [projectId, runId, surveyStatus?.survey_status, surveyStatus?.dds_ready]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleBack = () => {
    if (projectId) {
      navigate(`/project/${projectId}`);
    } else {
      navigate("/dashboard");
    }
  };

  // ── Survey handlers ──────────────────────────────────────────────────────
  /** Called when the user clicks "See Developer Driven Score" */
  const handleSeeDds = async () => {
    if (surveyStatus?.dds_ready) {
      // DDS already stored — just fetch it
      try {
        const res = await getSurveyResults(projectId, runId);
        setDdsResults(res.dds_results);
        setQuadrantResults(res.quadrant_results);
        setSurveyMsg("");
        setTimeout(() => {
          document.getElementById("dds-section")?.scrollIntoView({ behavior: "smooth" });
        }, 100);
      } catch (err) {
        setSurveyMsg(`❌ ${err?.response?.data?.detail || "Failed to load results."}`);
      }
    } else {
      // Threshold met but not yet calculated — trigger now
      handleForceCalculate();
    }
  };

  const handleRefreshStatus = async () => {
    if (!projectId || !runId) return;
    try {
      const data = await getSurveyStatus(projectId, runId);
      setSurveyStatus(data);
      if (data.dds_ready) {
        const res = await getSurveyResults(projectId, runId);
        setDdsResults(res.dds_results);
        setQuadrantResults(res.quadrant_results);
      }
    } catch (_) {}
  };

  const handleForceCalculate = async () => {
    setCalculatingDds(true);
    setSurveyMsg("");
    try {
      const res = await forceCalculateDds(projectId, runId);
      setDdsResults(res.dds_results);
      setQuadrantResults(res.quadrant_results);
      setSurveyStatus((prev) => ({ ...prev, survey_status: "completed", dds_ready: true }));
      setSurveyMsg("✅ DDS calculated successfully.");
      setTimeout(() => {
        document.getElementById("dds-section")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setSurveyMsg(`❌ ${err?.response?.data?.detail || "Calculation failed."}`);
    } finally {
      setCalculatingDds(false);
    }
  };

  const getSmellColor = (smellCount) => {
    if (smellCount === 0) return "#4caf50"; // green
    if (smellCount <= 3) return "#ff9800"; // orange
    return "#f44336"; // red
  };

  const displayName = runMeta
    ? `Run #${runMeta.run_number}`
    : projectData?.project_name || null;

  return (
    <div className="results-container">
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

      <div className="results-content">
        <div className="results-header">
          
          <h2>Test Smell Detection Results</h2>

          {displayName && (
            <p className="project-name">
              <strong>{displayName}</strong>
            </p>
          )}
        </div>

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Analyzing test smells...</p>
          </div>
        )}

        {!loading && results && (
          <div className="results-summary">
            {/* Summary Cards */}
            <div className="summary-cards">
              <div className="summary-card card-primary">
                <div className="summary-icon">📁</div>
                <div className="summary-info">
                  <h3>{results.total_files}</h3>
                  <p>Test Files Analyzed</p>
                </div>
              </div>

              <div className="summary-card card-warning">
                <div className="summary-icon">⚠️</div>
                <div className="summary-info">
                  <h3>{results.total_smells}</h3>
                  <p>Total Smells Detected</p>
                </div>
              </div>

              <div className="summary-card card-info">
                <div className="summary-icon">🔍</div>
                <div className="summary-info">
                  <h3>{uniqueSmells.length}</h3>
                  <p>Unique Smell Types</p>
                </div>
              </div>

              <div className="summary-card card-success">
                <div className="summary-icon">📊</div>
                <div className="summary-info">
                  <h3>
                    {results.total_files > 0
                      ? (results.total_smells / results.total_files).toFixed(1)
                      : 0}
                  </h3>
                  <p>Avg Smells per File</p>
                </div>
              </div>
            </div>

            {/* Smell Type Breakdown */}
            {uniqueSmells.length > 0 && (
              <div className="smell-breakdown">
                <h3>🧪 Test Smell Type Distribution</h3>
                <div className="smell-types-grid">
                  {uniqueSmells.map((smell, index) => (
                    <div key={index} className="smell-type-card">
                      <div className="smell-type-header">
                        <span className="smell-type-name">{smell.type}</span>
                        <span className="smell-type-badge">{smell.count}</span>
                      </div>
                      <div className="smell-type-bar">
                        <div
                          className="smell-type-fill"
                          style={{
                            width: `${(smell.count / results.total_smells) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="smell-type-percentage">
                        {((smell.count / results.total_smells) * 100).toFixed(
                          1,
                        )}
                        % of total
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Git-based Prioritization Metrics */}
            {results.git_metrics && results.git_metrics.metrics && (
              <div className="git-metrics-section">
                <h3>📈 Test Smell Prioritization (Git-based Metrics)</h3>

                {results.git_metrics.statistics && (
                  <div className="git-stats">
                    <div className="git-stat-item">
                      <span className="stat-label">Total Commits:</span>
                      <span className="stat-value">
                        {results.git_metrics.statistics.total_commits}
                      </span>
                    </div>
                    <div className="git-stat-item">
                      <span className="stat-label">Faulty Commits:</span>
                      <span className="stat-value">
                        {results.git_metrics.statistics.faulty_commits}
                      </span>
                    </div>
                    <div className="git-stat-item">
                      <span className="stat-label">Fault Rate:</span>
                      <span className="stat-value">
                        {results.git_metrics.statistics.fault_commit_pct}%
                      </span>
                    </div>
                  </div>
                )}

                <div className="prioritization-table-container">
                  <table className="prioritization-table">
                    <thead>
                      <tr>
                        <th>Smell Type</th>
                        <th>Instances</th>
                        <th>CP Score</th>
                        <th>FP Score</th>
                        <th>Priority Score</th>
                        <th>Ranking</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(results.git_metrics.metrics)
                        .sort(
                          (a, b) =>
                            b[1].prioritization_score -
                            a[1].prioritization_score,
                        )
                        .map(([smellType, metrics], index) => (
                          <tr
                            key={index}
                            className={index < 3 ? "high-priority" : ""}
                          >
                            <td className="smell-name-cell">{smellType}</td>
                            <td>{metrics.instance_count}</td>
                            <td>
                              <div className="score-cell">
                                <span className="score-value">
                                  {metrics.cp_score}
                                </span>
                                <div className="score-bar cp-bar">
                                  <div
                                    className="score-fill"
                                    style={{
                                      width: `${Math.min(metrics.cp_score * 50, 100)}%`,
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <div className="score-cell">
                                <span className="score-value">
                                  {metrics.fp_score}
                                </span>
                                <div className="score-bar fp-bar">
                                  <div
                                    className="score-fill"
                                    style={{
                                      width: `${Math.min(metrics.fp_score * 50, 100)}%`,
                                    }}
                                  ></div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <div className="priority-score">
                                <strong>{metrics.prioritization_score}</strong>
                              </div>
                            </td>
                            <td>
                              <span
                                className={`rank-badge rank-${index + 1 <= 3 ? "high" : index + 1 <= 6 ? "medium" : "low"}`}
                              >
                                #{index + 1}
                              </span>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>

                <div className="metrics-legend">
                  <h4>📋 Metrics Explanation:</h4>
                  <ul>
                    <li>
                      <strong>CP Score (Change Proneness):</strong> Likelihood
                      of code changes in files with this smell
                    </li>
                    <li>
                      <strong>FP Score (Fault Proneness):</strong> Likelihood of
                      bugs in files with this smell
                    </li>
                    <li>
                      <strong>Priority Score:</strong> Average of CP and FP
                      scores - higher means more urgent
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {results.git_metrics && results.git_metrics.error && (
              <div className="git-metrics-error">
                <h3>⚠️ Git Metrics Not Available</h3>
                <p>{results.git_metrics.error}</p>
                <p className="error-hint">
                  To enable prioritization metrics, ensure your project is a Git
                  repository with commit history.
                </p>
              </div>
            )}

            {/* ── Developer Survey Panel ──────────────────────────────────── */}
            {projectId && runId && (
              <div className="survey-control-strip">
                <div className="survey-strip-header">
                  <h3>👥 Developer Survey</h3>
                  {surveyLoading && !surveyStatus && (
                    <span className="survey-status-badge badge-loading">Loading…</span>
                  )}
                  {surveyStatus && (
                    <span className={`survey-status-badge badge-${surveyStatus.survey_status}`}>
                      {surveyStatus.survey_status === "not_sent" && "📭 Not Sent"}
                      {surveyStatus.survey_status === "sent" && "⏳ Awaiting Responses"}
                      {surveyStatus.survey_status === "completed" && "✓ Complete"}
                    </span>
                  )}
                </div>

                {/* Description / guidance */}
                {surveyStatus?.survey_status === "not_sent" && (
                  <p className="survey-strip-desc">
                    {surveyStatus.total_sent === 0
                      ? "⚠️ No contributor emails were found in this repository's git history. Re-analyse a repo with commit author emails to enable the survey."
                      : "Survey emails were sent automatically to all contributors when the analysis completed."}
                  </p>
                )}
                {surveyStatus?.survey_status === "sent" && (
                  <p className="survey-strip-desc">
                    Survey emails were automatically sent to <strong>{surveyStatus.total_sent}</strong> contributor(s).
                    The page polls every 10 s for new responses.
                    Once ≥50 % respond the <em>Developer Driven Score</em> button appears.
                  </p>
                )}
                {surveyStatus?.survey_status === "completed" && !ddsResults && (
                  <p className="survey-strip-desc">Responses collected. Click below to view the scores.</p>
                )}

                {/* Progress bar */}
                {surveyStatus && surveyStatus.total_sent > 0 && (
                  <div className="survey-progress-wrap">
                    <div className="survey-progress-label">
                      {surveyStatus.total_submitted} / {surveyStatus.total_sent} responses
                      &nbsp;·&nbsp; threshold {surveyStatus.threshold_pct}%
                      {surveyStatus.survey_status === "sent" && (
                        <span className="poll-indicator"> · 🔄 auto-polling</span>
                      )}
                    </div>
                    <div className="survey-progress-bar">
                      <div
                        className="survey-progress-fill"
                        style={{
                          width: `${Math.min(
                            (surveyStatus.total_submitted / surveyStatus.total_sent) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Survey link for manual sharing */}
                {surveyStatus?.survey_url && (
                  <div className="survey-url-box">
                    <span className="survey-url-label">Survey link (share manually):</span>
                    <a
                      href={surveyStatus.survey_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="survey-url-link"
                    >
                      {surveyStatus.survey_url}
                    </a>
                  </div>
                )}

                {/* ── See Developer Driven Score button ── */}
                {(() => {
                  if (!surveyStatus) return null;
                  if (ddsResults) return null; // already displayed below
                  const thresholdMet =
                    surveyStatus.total_sent > 0 &&
                    surveyStatus.total_submitted / surveyStatus.total_sent >= 0.5;
                  if (!surveyStatus.dds_ready && !thresholdMet) return null;
                  return (
                    <div className="see-dds-wrap">
                      <button
                        className="survey-btn see-dds-btn"
                        onClick={handleSeeDds}
                        disabled={calculatingDds}
                      >
                        {calculatingDds ? "Calculating…" : "🎯 See Developer Driven Score"}
                      </button>
                      <p className="see-dds-hint">
                        {surveyStatus.dds_ready
                          ? "Results already calculated — click to display."
                          : `${surveyStatus.total_submitted} of ${surveyStatus.total_sent} contributors responded (≥50%). Click to calculate the DDS.`}
                      </p>
                    </div>
                  );
                })()}

                {surveyMsg && (
                  <p className={`survey-msg ${surveyMsg.startsWith("✅") ? "survey-msg-ok" : "survey-msg-err"}`}>
                    {surveyMsg}
                  </p>
                )}
              </div>
            )}

            {/* ── DDS Score Table ────────────────────────────────────────── */}
            {ddsResults && (
              <div className="dds-section" id="dds-section">
                <h3>📊 Developer-Driven Scores (DDS)</h3>
                <p className="dds-desc">
                  Average developer rating (1–5) per smell across all survey
                  responses. Higher = more urgently perceived as needing
                  refactoring.
                </p>
                <div className="dds-table-wrap">
                  <table className="dds-table">
                    <thead>
                      <tr>
                        <th>Abbr</th>
                        <th>Smell Name</th>
                        <th>DDS Score</th>
                        <th>Scale (1–5)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(ddsResults)
                        .sort((a, b) => b[1] - a[1])
                        .map(([abbr, score]) => (
                          <tr key={abbr}>
                            <td>
                              <span className="dds-abbr">{abbr}</span>
                            </td>
                            <td>{SMELL_NAMES[abbr] || abbr}</td>
                            <td>
                              <strong>{Number(score).toFixed(2)}</strong>
                            </td>
                            <td>
                              <div className="dds-bar-track">
                                <div
                                  className="dds-bar-fill"
                                  style={{ width: `${(score / 5) * 100}%` }}
                                />
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ── Technical Debt Quadrant ────────────────────────────────── */}
            {quadrantResults && quadrantResults.length > 0 && (
              <div className="quadrant-section">
                <h3>🎯 Technical Debt Quadrant Classification</h3>
                <p className="quadrant-desc">
                  Each smell is placed in one of four quadrants based on its
                  mean-centered Priority Score (X-axis: empirical risk) and
                  Developer-Driven Score (Y-axis: developer perception).
                </p>

                {/* 2×2 Grid */}
                <div className="quadrant-grid">
                  {[
                    {
                      key: "Prudent & Deliberate",
                      cls: "q-pd",
                      axes: "High PS · High DDS",
                      label: "HIGH — Refactor Immediately",
                    },
                    {
                      key: "Prudent & Inadvertent",
                      cls: "q-pi",
                      axes: "Low PS · High DDS",
                      label: "MODERATE-LOW — Refactor When Possible",
                    },
                    {
                      key: "Reckless & Deliberate",
                      cls: "q-rd",
                      axes: "High PS · Low DDS",
                      label: "MODERATE-HIGH — Refactor Soon",
                    },
                    {
                      key: "Reckless & Inadvertent",
                      cls: "q-ri",
                      axes: "Low PS · Low DDS",
                      label: "LOW — Monitor / Defer",
                    },
                  ].map(({ key, cls, axes, label }) => {
                    const items = quadrantResults.filter(
                      (r) => r.quadrant === key
                    );
                    return (
                      <div key={key} className={`quadrant-cell ${cls}`}>
                        <div className="qcell-header">
                          <span className="qcell-name">{key}</span>
                          <span className="qcell-axes">{axes}</span>
                        </div>
                        <div className="qcell-priority-label">{label}</div>
                        <div className="qcell-chips">
                          {items.map((r) => (
                            <span
                              key={r.abbreviation}
                              className="qcell-chip"
                              title={r.smellName}
                            >
                              {r.abbreviation}
                            </span>
                          ))}
                          {items.length === 0 && (
                            <span className="qcell-empty">—</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Detailed table */}
                <div className="quadrant-table-wrap">
                  <table className="quadrant-table">
                    <thead>
                      <tr>
                        <th>Smell</th>
                        <th>PS</th>
                        <th>DDS</th>
                        <th>Norm. PS</th>
                        <th>Norm. DDS</th>
                        <th>Quadrant</th>
                        <th>Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quadrantResults.map((r) => (
                        <tr key={r.abbreviation}>
                          <td>
                            <span className="qt-abbr">{r.abbreviation}</span>{" "}
                            <span className="qt-name">{r.smellName}</span>
                          </td>
                          <td>{Number(r.PS).toFixed(4)}</td>
                          <td>{Number(r.DDS).toFixed(2)}</td>
                          <td
                            className={
                              r.normalizedPS >= 0 ? "norm-pos" : "norm-neg"
                            }
                          >
                            {r.normalizedPS >= 0 ? "+" : ""}
                            {Number(r.normalizedPS).toFixed(4)}
                          </td>
                          <td
                            className={
                              r.normalizedDDS >= 0 ? "norm-pos" : "norm-neg"
                            }
                          >
                            {r.normalizedDDS >= 0 ? "+" : ""}
                            {Number(r.normalizedDDS).toFixed(4)}
                          </td>
                          <td>{r.quadrant}</td>
                          <td>
                            <span
                              className={`priority-badge prio-${
                                r.priority.startsWith("HIGH") ? "high" :
                                r.priority.startsWith("MODERATE-HIGH") ? "mod-high" :
                                r.priority.startsWith("MODERATE-LOW") ? "mod-low" :
                                "low"
                              }`}
                            >
                              {r.priority}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Detailed Results Table */}
            {results.details && results.details.length > 0 ? (
              <div className="smell-details">
                <h3>Detailed Results by File</h3>
                <div className="table-container">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>File Name</th>
                        <th>Smell Type</th>
                        <th>Line</th>
                        <th>Message</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.details.map((fileResult, fileIndex) => {
                        if (fileResult.error) {
                          return (
                            <tr key={fileIndex} className="error-row">
                              <td>{fileResult.file}</td>
                              <td colSpan="3" className="error-cell">
                                Error: {fileResult.error}
                              </td>
                              <td>
                                <span className="status-badge error">
                                  Error
                                </span>
                              </td>
                            </tr>
                          );
                        }

                        if (
                          !fileResult.smells ||
                          fileResult.smells.length === 0
                        ) {
                          return (
                            <tr key={fileIndex} className="clean-row">
                              <td>{fileResult.file}</td>
                              <td colSpan="3" className="clean-cell">
                                No test smells detected
                              </td>
                              <td>
                                <span className="status-badge clean">
                                  Clean
                                </span>
                              </td>
                            </tr>
                          );
                        }

                        return fileResult.smells.map((smell, smellIndex) => (
                          <tr key={`${fileIndex}-${smellIndex}`}>
                            {smellIndex === 0 && (
                              <td
                                rowSpan={fileResult.smells.length}
                                className="file-cell"
                              >
                                📄 {fileResult.file}
                              </td>
                            )}
                            <td className="smell-type-cell">{smell.type}</td>
                            <td className="line-cell">
                              {smell.line > 0 ? smell.line : "-"}
                            </td>
                            <td className="message-cell">
                              {smell.message || "-"}
                            </td>
                            {smellIndex === 0 && (
                              <td
                                rowSpan={fileResult.smells.length}
                                className="status-cell"
                              >
                                <span
                                  className="status-badge warning"
                                  style={{
                                    backgroundColor: getSmellColor(
                                      fileResult.smell_count,
                                    ),
                                  }}
                                >
                                  {fileResult.smell_count} smell
                                  {fileResult.smell_count !== 1 ? "s" : ""}
                                </span>
                              </td>
                            )}
                          </tr>
                        ));
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="no-results">
                <div className="no-results-icon">🎉</div>
                <h3>Great Job!</h3>
                <p>No test smells detected in your project.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Results;
