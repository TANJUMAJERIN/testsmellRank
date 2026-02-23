import React, { useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { projectsAPI } from "../services/api";
import "./Compare.css";

const Compare = () => {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const run1Id = searchParams.get("run1");
  const run2Id = searchParams.get("run2");

  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!run1Id || !run2Id) {
      setError("Two run IDs are required for comparison.");
      setLoading(false);
      return;
    }
    fetchComparison();
  }, [projectId, run1Id, run2Id]);

  const fetchComparison = async () => {
    try {
      setLoading(true);
      const data = await projectsAPI.compare(projectId, run1Id, run2Id);
      setComparison(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load comparison.");
    } finally {
      setLoading(false);
    }
  };

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
      : "";

  const renderRankChange = (change) => {
    if (change === null || change === undefined)
      return <span className="rank-neutral"></span>;
    if (change < 0)
      return <span className="rank-improved"> {Math.abs(change)} improved</span>;
    if (change > 0)
      return <span className="rank-worsened"> {change} worsened</span>;
    return <span className="rank-neutral"> unchanged</span>;
  };

  const renderScoreChange = (change) => {
    if (change === null || change === undefined) return "";
    const formatted = change > 0 ? `+${change.toFixed(4)}` : change.toFixed(4);
    const cls =
      change < 0 ? "score-improved" : change > 0 ? "score-worsened" : "score-neutral";
    return <span className={cls}>{formatted}</span>;
  };

  return (
    <div className="cmp-container">
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

      <div className="cmp-content">
        <div className="cmp-header">
          <button
            className="back-button"
            onClick={() => navigate(`/project/${projectId}`)}
          >
             Back to Project
          </button>
          <h2>Run Comparison</h2>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading comparison</p>
          </div>
        ) : comparison ? (
          <>
            <div className="run-meta-cards">
              <div className="run-meta-card run-meta-1">
                <h3>Run #{comparison.run1?.run_number}</h3>
                <p>{formatDate(comparison.run1?.created_at)}</p>
                <p>
                  <strong>{comparison.run1?.summary?.total_smells ?? "-"}</strong> smells
                </p>
              </div>
              <div className="vs-divider">VS</div>
              <div className="run-meta-card run-meta-2">
                <h3>Run #{comparison.run2?.run_number}</h3>
                <p>{formatDate(comparison.run2?.created_at)}</p>
                <p>
                  <strong>{comparison.run2?.summary?.total_smells ?? "-"}</strong> smells
                </p>
              </div>
            </div>

            {comparison.summary && (
              <div className="cmp-summary">
                <div className="summary-badge improved">
                   Improved: {comparison.summary.improved}
                </div>
                <div className="summary-badge worsened">
                   Worsened: {comparison.summary.worsened}
                </div>
                <div className="summary-badge unchanged">
                   Unchanged: {comparison.summary.unchanged}
                </div>
              </div>
            )}

            {comparison.comparison && comparison.comparison.length > 0 ? (
              <div className="cmp-table-container">
                <table className="cmp-table">
                  <thead>
                    <tr>
                      <th>Smell Type</th>
                      <th>Run #{comparison.run1?.run_number} Rank</th>
                      <th>Run #{comparison.run2?.run_number} Rank</th>
                      <th>Rank Change</th>
                      <th>Score (Run 1)</th>
                      <th>Score (Run 2)</th>
                      <th>Score Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.comparison.map((row, i) => {
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
                            {row.run1_rank != null ? `#${row.run1_rank}` : <span className="new-tag">new</span>}
                          </td>
                          <td className="rank-cell">
                            {row.run2_rank != null ? `#${row.run2_rank}` : <span className="new-tag">new</span>}
                          </td>
                          <td className="change-cell">{renderRankChange(row.rank_change)}</td>
                          <td className="cmp-score-cell">{row.run1_score?.toFixed(4) ?? ""}</td>
                          <td className="cmp-score-cell">{row.run2_score?.toFixed(4) ?? ""}</td>
                          <td className="change-cell">{renderScoreChange(row.score_change)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="no-data">No comparison data available.</p>
            )}

            <div className="compare-legend">
              <h4>Legend</h4>
              <ul>
                <li><span className="rank-improved"> improved</span>  smell moved to a lower priority rank (less urgent)</li>
                <li><span className="rank-worsened"> worsened</span>  smell moved to a higher priority rank (more urgent)</li>
                <li>Score = prioritization score (average of CP + FP). Lower score = less risky.</li>
              </ul>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

export default Compare;