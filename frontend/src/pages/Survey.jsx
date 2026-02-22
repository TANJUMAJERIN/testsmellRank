import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getSurveyData, submitSurvey } from "../services/api";
import "./Survey.css";

const LABELS = {
  1: "Very Low",
  2: "Low",
  3: "Moderate",
  4: "High",
  5: "Very High",
};

const Survey = () => {
  const { runId } = useParams();

  const [state, setState] = useState("loading"); // loading | open | submitted | closed | error
  const [surveyData, setSurveyData] = useState(null);
  const [ratings, setRatings] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // ── Load survey on mount ──────────────────────────────────────────────────
  useEffect(() => {
    getSurveyData(runId)
      .then((data) => {
        if (!data.survey_open) {
          setState("closed");
          return;
        }
        setSurveyData(data);
        // Pre-initialise all ratings to null (unanswered)
        const initial = {};
        data.smell_list.forEach((s) => {
          initial[s.abbr] = null;
        });
        setRatings(initial);
        setState("open");
      })
      .catch((err) => {
        const detail =
          err?.response?.data?.detail || "Unable to load the survey.";
        if (detail.includes("not been opened")) {
          setState("closed");
        } else {
          setErrorMsg(detail);
          setState("error");
        }
      });
  }, [runId]);

  // ── Rating change ─────────────────────────────────────────────────────────
  const handleRating = (abbr, value) => {
    setRatings((prev) => ({ ...prev, [abbr]: value }));
  };

  // ── All 15 answered? ─────────────────────────────────────────────────────
  const allAnswered =
    surveyData &&
    surveyData.smell_list.every((s) => ratings[s.abbr] !== null);

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!allAnswered) return;

    setSubmitting(true);
    try {
      // Convert null-safe object to { abbr: int }
      const responses = {};
      Object.entries(ratings).forEach(([k, v]) => {
        responses[k] = v;
      });

      await submitSurvey(runId, responses);
      setState("submitted");
    } catch (err) {
      setErrorMsg(
        err?.response?.data?.detail ||
          "Submission failed. Please try again."
      );
      setSubmitting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="survey-page">
      <div className="survey-header">
        <div className="survey-logo">🧪 TestSmellRank</div>
        <h1>Developer Survey</h1>
        {surveyData && (
          <p className="survey-project-name">
            Project: <strong>{surveyData.project_name}</strong>
          </p>
        )}
      </div>

      {/* ── Loading ── */}
      {state === "loading" && (
        <div className="survey-status-box">
          <div className="survey-spinner" />
          <p>Loading survey…</p>
        </div>
      )}

      {/* ── Closed / not sent ── */}
      {state === "closed" && (
        <div className="survey-status-box survey-closed">
          <div className="survey-status-icon">🔒</div>
          <h2>Survey Not Available</h2>
          <p>This survey has not been opened yet or the link is invalid.</p>
        </div>
      )}

      {/* ── Already submitted ── */}
      {state === "submitted" && (
        <div className="survey-status-box survey-success">
          <div className="survey-status-icon">✅</div>
          <h2>Thank You!</h2>
          <p>
            Your response has been recorded. Your ratings will help
            prioritize test smell refactoring more accurately.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {state === "error" && (
        <div className="survey-status-box survey-error">
          <div className="survey-status-icon">❌</div>
          <h2>Something Went Wrong</h2>
          <p>{errorMsg}</p>
        </div>
      )}

      {/* ── Survey form ── */}
      {state === "open" && surveyData && (
        <form className="survey-form" onSubmit={handleSubmit}>
          <div className="survey-instructions">
            <p>
              Rate how urgently each test smell below should be{" "}
              <strong>refactored</strong> in your project.
            </p>
            <div className="scale-guide">
              <span className="scale-low">1 — Very Low Priority</span>
              <span className="scale-arrow">→</span>
              <span className="scale-high">5 — Very High Priority</span>
            </div>
          </div>

          <div className="smell-list">
            {surveyData.smell_list.map((smell, idx) => (
              <div
                key={smell.abbr}
                className={`smell-row ${ratings[smell.abbr] !== null ? "answered" : ""}`}
              >
                <div className="smell-row-left">
                  <div className="smell-row-title">
                    <span className="smell-abbr-badge">{smell.abbr}</span>
                    <span className="smell-full-name">{smell.name}</span>
                    <span className="smell-idx">{idx + 1}/15</span>
                  </div>
                  <p className="smell-description">{smell.description}</p>
                </div>

                <div className="likert-row">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <label
                      key={val}
                      className={`likert-option ${ratings[smell.abbr] === val ? "selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name={smell.abbr}
                        value={val}
                        checked={ratings[smell.abbr] === val}
                        onChange={() => handleRating(smell.abbr, val)}
                      />
                      <span className="likert-num">{val}</span>
                      <span className="likert-label">{LABELS[val]}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="survey-footer">
            <p className="answered-count">
              {Object.values(ratings).filter((v) => v !== null).length} / 15
              answered
            </p>
            {errorMsg && <p className="submit-error">{errorMsg}</p>}
            <button
              type="submit"
              className="submit-btn"
              disabled={!allAnswered || submitting}
            >
              {submitting ? "Submitting…" : "Submit Survey"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default Survey;
