import React, { useState, useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRun } from "../services/api";
import "./Results.css";

const Results = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId, runId } = useParams();

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState(null);
  const [uniqueSmells, setUniqueSmells] = useState([]);
  const [runMeta, setRunMeta] = useState(null);

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
          <button onClick={handleBack} className="back-button">
            ← {projectId ? "Back to Project" : "Back to Dashboard"}
          </button>
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
                        {results.git_metrics.statistics.fault_percentage}%
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
