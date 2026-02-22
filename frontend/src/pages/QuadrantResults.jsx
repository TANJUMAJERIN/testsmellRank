import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { projectsAPI } from "../services/api";
import "./QuadrantResults.css";

// ── helpers ────────────────────────────────────────────────────────────────
const QUADRANT_CONFIG = {
  "Prudent & Deliberate": {
    cls: "q-high",
    badgeCls: "badge-high",
    position: "top-right", // High PS, High DDS
    desc: "High PS · High DDS",
  },
  "Reckless & Deliberate": {
    cls: "q-mod-high",
    badgeCls: "badge-mod-high",
    position: "bottom-right", // High PS, Low DDS
    desc: "High PS · Low DDS",
  },
  "Prudent & Inadvertent": {
    cls: "q-mod-low",
    badgeCls: "badge-mod-low",
    position: "top-left", // Low PS, High DDS
    desc: "Low PS · High DDS",
  },
  "Reckless & Inadvertent": {
    cls: "q-low",
    badgeCls: "badge-low",
    position: "bottom-left", // Low PS, Low DDS
    desc: "Low PS · Low DDS",
  },
};

const priorityBadgeCls = (priority) => {
  if (priority?.startsWith("HIGH —")) return "badge-high";
  if (priority?.startsWith("MODERATE-HIGH")) return "badge-mod-high";
  if (priority?.startsWith("MODERATE-LOW")) return "badge-mod-low";
  return "badge-low";
};

const formatScore = (v) =>
  v !== undefined && v !== null ? Number(v).toFixed(4) : "—";

const NormVal = ({ v }) => {
  if (v === undefined || v === null) return <span>—</span>;
  const n = Number(v);
  const cls = n >= 0 ? "pos" : "neg";
  return (
    <span className={`norm-val ${cls}`}>
      {n >= 0 ? "+" : ""}
      {n.toFixed(4)}
    </span>
  );
};

// ── component ──────────────────────────────────────────────────────────────
const QuadrantResults = () => {
  const { projectId, runId } = useParams();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [survey, setSurvey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSurvey = async () => {
      try {
        const data = await projectsAPI.getSurveyStatus(projectId, runId);
        setSurvey(data);
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to load quadrant results.",
        );
      } finally {
        setLoading(false);
      }
    };
    fetchSurvey();
  }, [projectId, runId]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const results = survey?.quadrant_results || [];

  // Group by quadrant for the 2×2 grid
  const byQuadrant = {};
  Object.keys(QUADRANT_CONFIG).forEach((q) => {
    byQuadrant[q] = [];
  });
  results.forEach((r) => {
    if (byQuadrant[r.quadrant] !== undefined) {
      byQuadrant[r.quadrant].push(r);
    }
  });

  // Summary counts
  const counts = {
    high: byQuadrant["Prudent & Deliberate"].length,
    modHigh: byQuadrant["Reckless & Deliberate"].length,
    modLow: byQuadrant["Prudent & Inadvertent"].length,
    low: byQuadrant["Reckless & Inadvertent"].length,
  };

  // For bar widths: normalise PS (0..1) across visible range
  const psValues = results.map((r) => r.PS);
  const ddsValues = results.map((r) => r.DDS);
  const maxPS = Math.max(...psValues, 0.0001);
  const maxDDS = Math.max(...ddsValues, 0.0001);

  // ── 2×2 grid cells (row-major: top-left, top-right, bottom-left, bottom-right) ──
  const gridOrder = [
    ["Prudent & Inadvertent", "Prudent & Deliberate"],
    ["Reckless & Inadvertent", "Reckless & Deliberate"],
  ];

  return (
    <div className="qr-container">
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

      <div className="qr-content">
        <div className="qr-top-bar">
          <button
            className="back-button"
            onClick={() => navigate(`/project/${projectId}`)}
          >
            ← Back to Project
          </button>
        </div>

        <h2 className="qr-title">📊 Technical Debt Quadrant Analysis</h2>
        <p className="qr-subtitle">
          Combined empirical metrics (PS) × developer perception (DDS) — Run #
          {survey?.run_id ? "…" : ""}
        </p>

        {/* ── Loading ── */}
        {loading && (
          <div className="qr-loading">
            <div className="spinner" />
            <span>Loading quadrant results…</span>
          </div>
        )}

        {/* ── Error ── */}
        {!loading && error && (
          <div className="qr-empty">
            <div className="qr-empty-icon">⚠️</div>
            <h3>Not Available</h3>
            <p>{error}</p>
          </div>
        )}

        {/* ── No results yet ── */}
        {!loading && !error && results.length === 0 && (
          <div className="qr-empty">
            <div className="qr-empty-icon">📭</div>
            <h3>No Quadrant Data Yet</h3>
            <p>
              Survey responses are needed to calculate DDS.
              <br />
              Return here once at least one contributor has submitted the
              survey.
            </p>
          </div>
        )}

        {!loading && !error && results.length > 0 && (
          <>
            {/* ── Stat cards ── */}
            <div className="qr-stats-row">
              <div className="qr-stat-card c-red">
                <div className="stat-num">{counts.high}</div>
                <div className="stat-lbl">HIGH — Refactor Immediately</div>
              </div>
              <div className="qr-stat-card c-orange">
                <div className="stat-num">{counts.modHigh}</div>
                <div className="stat-lbl">MODERATE-HIGH — Refactor Soon</div>
              </div>
              <div className="qr-stat-card c-blue">
                <div className="stat-num">{counts.modLow}</div>
                <div className="stat-lbl">MODERATE-LOW — When Possible</div>
              </div>
              <div className="qr-stat-card c-grey">
                <div className="stat-num">{counts.low}</div>
                <div className="stat-lbl">LOW — Monitor / Defer</div>
              </div>
            </div>

            {/* ── 2×2 Quadrant Grid ── */}
            <div className="quadrant-grid-wrapper">
              <h3 className="section-title">🗺️ Technical Debt Quadrant Map</h3>
              <p
                style={{
                  color: "#888",
                  fontSize: "0.85rem",
                  marginBottom: 20,
                  marginTop: -8,
                }}
              >
                X-axis = Empirical risk (PS) · Y-axis = Developer severity (DDS)
              </p>

              {/* top row labels */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  marginBottom: 4,
                }}
              >
                <div
                  style={{
                    textAlign: "center",
                    fontSize: "0.75rem",
                    color: "#888",
                  }}
                >
                  ← Low PS
                </div>
                <div
                  style={{
                    textAlign: "center",
                    fontSize: "0.75rem",
                    color: "#888",
                  }}
                >
                  High PS →
                </div>
              </div>

              <div className="quadrant-layout">
                {gridOrder.map((row, ri) => (
                  <div className="quadrant-row" key={ri}>
                    {row.map((quadrant) => {
                      const cfg = QUADRANT_CONFIG[quadrant];
                      const items = byQuadrant[quadrant];
                      return (
                        <div
                          key={quadrant}
                          className={`quadrant-cell ${cfg.cls}`}
                        >
                          <div className="quadrant-cell-header">
                            <div className="q-name">{quadrant}</div>
                            <div className="q-priority-text">{cfg.desc}</div>
                          </div>
                          <div className="q-chips">
                            {items.length === 0 ? (
                              <span className="q-empty">No smells</span>
                            ) : (
                              items.map((r) => (
                                <span
                                  key={r.abbreviation}
                                  className="q-chip"
                                  title={`${r.smellName}\nPS: ${formatScore(r.PS)} · DDS: ${formatScore(r.DDS)}`}
                                >
                                  {r.abbreviation}
                                </span>
                              ))
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>

              <div className="axis-x-label">
                ← Low Empirical Risk (PS) ·················· High Empirical Risk
                (PS) →
              </div>
            </div>

            {/* ── Scores legend ── */}
            <div className="scores-legend">
              <span>
                <span className="dot-ps" /> PS = Prioritization Score
                (empirical: CP + FP)
              </span>
              <span>
                <span className="dot-dds" /> DDS = Developer-Driven Score
                (survey average 1–5 Likert)
              </span>
              <span>
                Normalization: mean-centred (value − mean across all 15 smells)
              </span>
            </div>

            {/* ── Detail Table ── */}
            <div className="qr-table-wrapper">
              <h3 className="section-title">📋 Detailed Results per Smell</h3>
              <table className="qr-table">
                <thead>
                  <tr>
                    <th>Smell</th>
                    <th>Full Name</th>
                    <th>PS</th>
                    <th>DDS</th>
                    <th>Norm. PS</th>
                    <th>Norm. DDS</th>
                    <th>Quadrant</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.abbreviation}>
                      <td>
                        <span className="smell-abbr-col">{r.abbreviation}</span>
                      </td>
                      <td>{r.smellName}</td>
                      <td>
                        <div className="score-bar-mini">
                          <span style={{ minWidth: 46 }}>
                            {formatScore(r.PS)}
                          </span>
                          <div className="bar-track">
                            <div
                              className="bar-fill-ps"
                              style={{
                                width: `${Math.min((r.PS / maxPS) * 100, 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="score-bar-mini">
                          <span style={{ minWidth: 46 }}>
                            {formatScore(r.DDS)}
                          </span>
                          <div className="bar-track">
                            <div
                              className="bar-fill-dds"
                              style={{
                                width: `${Math.min((r.DDS / maxDDS) * 100, 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        <NormVal v={r.normalizedPS} />
                      </td>
                      <td>
                        <NormVal v={r.normalizedDDS} />
                      </td>
                      <td style={{ fontSize: "0.82rem" }}>{r.quadrant}</td>
                      <td>
                        <span
                          className={`priority-badge ${priorityBadgeCls(r.priority)}`}
                        >
                          {r.priority}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ── Legend ── */}
            <div className="qr-legend">
              <h3>📖 Quadrant Explanation</h3>
              <div className="legend-grid">
                <div className="legend-item l-high">
                  <strong>🔴 Prudent &amp; Deliberate — HIGH</strong>
                  High empirical risk AND developers see it as severe. Refactor
                  immediately.
                </div>
                <div className="legend-item l-mod-high">
                  <strong>🟠 Reckless &amp; Deliberate — MODERATE-HIGH</strong>
                  High empirical risk but developers underestimate severity.
                  Still refactor soon.
                </div>
                <div className="legend-item l-mod-low">
                  <strong>🔵 Prudent &amp; Inadvertent — MODERATE-LOW</strong>
                  Low empirical risk but developers perceive high severity.
                  Refactor when possible.
                </div>
                <div className="legend-item l-low">
                  <strong>⚪ Reckless &amp; Inadvertent — LOW</strong>
                  Low empirical risk and developers consider it unimportant.
                  Monitor and defer.
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QuadrantResults;
