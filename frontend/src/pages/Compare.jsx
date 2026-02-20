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

  const rankChangeIcon = (change) => {
    if (change > 0) return <span className="rank-up">↑ {change}</span>;
    if (change < 0) return <span className="rank-down">↓ {Math.abs(change)}</span>;
    return <span className="rank-neutral">→ 0</span>;
  };

  const scoreChangeIcon = (change) => {
    const formatted = change !== null && change !== undefined ? change.toFixed(4) : "-";
    if (change > 0) return <span className="score-up">+ {formatted}</span>;
    if (change < 0) return <span className="score-down">{formatted}</span>;
    return <span className="score-neutral">{formatted}</span>;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString();
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
            ← Back to Project
          </button>
          <h2>Run Comparison</h2>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading comparison…</p>
          </div>
        ) : comparison ? (
          <>
            {/* Run metadata */}
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

            {/* Summary */}
            {comparison.summary && (
              <div className="cmp-summary">
                <div className="summary-badge improved">
                  ↑ Improved: {comparison.summary.improved}
                </div>
                <div className="summary-badge worsened">
                  ↓ Worsened: {comparison.summary.worsened}
                </div>
                <div className="summary-badge unchanged">
                  → Unchanged: {comparison.summary.unchanged}
                </div>
              </div>
            )}

            {/* Comparison table */}
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
                    {comparison.comparison.map((row) => (
                      <tr
                        key={row.smell_type}
                        className={
                          row.rank_change > 0
                            ? "row-improved"
                            : row.rank_change < 0
                            ? "row-worsened"
                            : ""
                        }
                      >
                        <td className="smell-name-cell">{row.smell_type}</td>
                        <td className="rank-cell">#{row.run1_rank}</td>
                        <td className="rank-cell">#{row.run2_rank}</td>
                        <td className="change-cell">
                          {rankChangeIcon(row.rank_change)}
                        </td>
                        <td className="score-cell">
                          {row.run1_score !== null && row.run1_score !== undefined
                            ? row.run1_score.toFixed(4)
                            : "-"}
                        </td>
                        <td className="score-cell">
                          {row.run2_score !== null && row.run2_score !== undefined
                            ? row.run2_score.toFixed(4)
                            : "-"}
                        </td>
                        <td className="change-cell">
                          {scoreChangeIcon(row.score_change)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="no-data">No comparison data available.</p>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
};

export default Compare;
