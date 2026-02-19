import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { compareRuns } from "../services/api";
import "./Compare.css";

const Compare = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();

  const run1Id = searchParams.get("run1");
  const run2Id = searchParams.get("run2");

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!run1Id || !run2Id) {
      navigate(`/project/${projectId}`);
      return;
    }
    compareRuns(projectId, run1Id, run2Id)
      .then(setData)
      .catch(() => setError("Failed to load comparison data."))
      .finally(() => setLoading(false));
  }, [projectId, run1Id, run2Id]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const formatDate = (ds) =>
    ds
      ? new Date(ds).toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        })
      : "—";

  const renderRankChange = (change) => {
    if (change === null || change === undefined)
      return <span className="rank-neutral">—</span>;
    if (change < 0)
      return (
        <span className="rank-improved">↑ {Math.abs(change)} improved</span>
      );
    if (change > 0)
      return <span className="rank-worsened">↓ {change} worsened</span>;
    return <span className="rank-neutral">→ unchanged</span>;
  };

  const renderScoreChange = (change) => {
    if (change === null || change === undefined) return "—";
    const formatted = change > 0 ? `+${change.toFixed(4)}` : change.toFixed(4);
    const cls =
      change < 0
        ? "score-improved"
        : change > 0
          ? "score-worsened"
          : "score-neutral";
    return <span className={cls}>{formatted}</span>;
  };

  return (
    <div className="compare-container">
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

      <div className="compare-content">
        <div className="compare-header">
          
          <h2>Run Comparison</h2>
        </div>

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading comparison…</p>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {!loading && data && (
          <>
            {/* Run meta row */}
            <div className="run-meta-row">
              <div className="run-meta-card">
                <span className="run-label">Run #{data.run1.run_number}</span>
                <span className="run-meta-date">
                  {formatDate(data.run1.created_at)}
                </span>
                <span className="run-meta-smells">
                  {data.run1.summary?.total_smells ?? "?"} smells
                </span>
              </div>
              <div className="vs-divider">vs</div>
              <div className="run-meta-card">
                <span className="run-label">Run #{data.run2.run_number}</span>
                <span className="run-meta-date">
                  {formatDate(data.run2.created_at)}
                </span>
                <span className="run-meta-smells">
                  {data.run2.summary?.total_smells ?? "?"} smells
                </span>
              </div>
            </div>

            {/* Summary banner */}
            <div className="compare-summary-banner">
              <div className="summary-pill improved">
                ✅ {data.summary.improved} improved
              </div>
              <div className="summary-pill worsened">
                ❌ {data.summary.worsened} worsened
              </div>
              <div className="summary-pill unchanged">
                → {data.summary.unchanged} unchanged
              </div>
            </div>

            {/* Comparison table */}
            {data.comparison.length === 0 ? (
              <div className="empty-state">
                <p>
                  No git-based metrics available for comparison. Ensure the
                  repository has commit history.
                </p>
              </div>
            ) : (
              <div className="compare-table-wrapper">
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th>Smell Type</th>
                      <th>Run #{data.run1.run_number} Rank</th>
                      <th>Run #{data.run2.run_number} Rank</th>
                      <th>Rank Change</th>
                      <th>Run #{data.run1.run_number} Score</th>
                      <th>Run #{data.run2.run_number} Score</th>
                      <th>Score Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.comparison.map((row, i) => {
                      const rowClass =
                        row.rank_change < 0
                          ? "row-improved"
                          : row.rank_change > 0
                            ? "row-worsened"
                            : "";
                      return (
                        <tr key={i} className={rowClass}>
                          <td className="smell-name-cell">{row.smell_type}</td>
                          <td className="rank-cell">
                            {row.run1_rank != null ? (
                              `#${row.run1_rank}`
                            ) : (
                              <span className="new-tag">new</span>
                            )}
                          </td>
                          <td className="rank-cell">
                            {row.run2_rank != null ? (
                              `#${row.run2_rank}`
                            ) : (
                              <span className="new-tag">new</span>
                            )}
                          </td>
                          <td>{renderRankChange(row.rank_change)}</td>
                          <td className="score-cell">
                            {row.run1_score?.toFixed(4) ?? "—"}
                          </td>
                          <td className="score-cell">
                            {row.run2_score?.toFixed(4) ?? "—"}
                          </td>
                          <td>{renderScoreChange(row.score_change)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="compare-legend">
              <h4>Legend</h4>
              <ul>
                <li>
                  <span className="rank-improved">↑ improved</span> — smell
                  moved to a lower priority rank (less urgent)
                </li>
                <li>
                  <span className="rank-worsened">↓ worsened</span> — smell
                  moved to a higher priority rank (more urgent)
                </li>
                <li>
                  Score = prioritization score (average of CP + FP). Lower score
                  = less risky.
                </li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Compare;
