import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import "./Survey.css";

const LIKERT_LABELS = ["Not Important", "", "Neutral", "", "Critical"];

const Survey = () => {
  const { token } = useParams();

  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(null);
  const [ratings, setRatings] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [alreadyDone, setAlreadyDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchForm = async () => {
      try {
        const res = await axios.get(`/api/survey/${token}`);
        if (res.data.already_submitted) {
          setAlreadyDone(true);
        } else {
          setFormData(res.data);
        }
      } catch (err) {
        setError(
          err.response?.data?.detail || "Invalid or expired survey link.",
        );
      } finally {
        setLoading(false);
      }
    };
    fetchForm();
  }, [token]);

  const handleRate = (abbr, value) => {
    setRatings((prev) => ({ ...prev, [abbr]: value }));
  };

  const answered = Object.keys(ratings).length;
  const total = formData?.smells?.length || 0;

  const handleSubmit = async () => {
    if (answered < total) {
      setError(`Please rate all ${total} smells before submitting.`);
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await axios.post(`/api/survey/${token}/submit`, { ratings });
      setSubmitted(true);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Submission failed. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  // ── loading ──
  if (loading) {
    return (
      <div className="survey-page">
        <div className="survey-center-state">
          <div className="state-icon">⏳</div>
          <h2>Loading Survey…</h2>
        </div>
      </div>
    );
  }

  // ── invalid link ──
  if (error && !formData) {
    return (
      <div className="survey-page">
        <div className="survey-center-state">
          <div className="state-icon">🔗</div>
          <h2>Invalid Survey Link</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  // ── already submitted ──
  if (alreadyDone) {
    return (
      <div className="survey-page">
        <div className="survey-center-state">
          <div className="state-icon">✅</div>
          <h2>Already Submitted</h2>
          <p>
            You have already completed the survey for{" "}
            <strong>{formData?.project_name || "this project"}</strong>.
            <br />
            Thank you for your contribution!
          </p>
        </div>
      </div>
    );
  }

  // ── success ──
  if (submitted) {
    return (
      <div className="survey-page">
        <div className="survey-center-state">
          <div className="state-icon">🎉</div>
          <h2>Thank You!</h2>
          <p>
            Your responses for <strong>{formData?.project_name}</strong> have
            been recorded.
            <br />
            Your feedback helps prioritize which test smells to fix first.
          </p>
        </div>
      </div>
    );
  }

  // ── survey form ──
  return (
    <div className="survey-page">
      <div className="survey-header">
        <h1>Test Smell Rank</h1>
        <p>Developer Perception Survey</p>
      </div>

      <div className="survey-card">
        <div className="survey-intro">
          <h2>{formData.project_name} — Developer Survey</h2>
          <p>
            Hi <strong>{formData.contributor_name}</strong>! Please rate how
            important it is to fix each type of test smell in this project.
            There are no right or wrong answers — we want your honest developer
            perspective.
          </p>
          <div className="scale-guide">
            {[
              "1 – Not Important",
              "2 – Slightly",
              "3 – Neutral",
              "4 – Important",
              "5 – Critical",
            ].map((l) => (
              <span className="scale-pill" key={l}>
                {l}
              </span>
            ))}
          </div>
        </div>

        <div className="smell-list">
          {formData.smells.map((smell) => {
            const selected = ratings[smell.abbreviation];
            return (
              <div
                key={smell.abbreviation}
                className={`smell-item${selected ? " answered" : ""}`}
              >
                <div className="smell-item-header">
                  <span className="smell-abbr-badge">{smell.abbreviation}</span>
                  <div className="smell-text">
                    <h4>{smell.name}</h4>
                    <p>{smell.description}</p>
                  </div>
                </div>

                <div className="likert-row">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      className={`likert-btn${selected === val ? ` selected-${val}` : ""}`}
                      onClick={() => handleRate(smell.abbreviation, val)}
                    >
                      {val}
                    </button>
                  ))}
                </div>
                <div className="likert-labels">
                  <span>Not Important</span>
                  <span>Critical</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress */}
        <div className="survey-progress">
          <div className="progress-label">
            <span>Progress</span>
            <span>
              {answered} / {total} rated
            </span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${(answered / total) * 100}%` }}
            />
          </div>
        </div>

        {error && <div className="survey-error">{error}</div>}

        <div className="survey-submit-section">
          <button
            className="btn-submit-survey"
            onClick={handleSubmit}
            disabled={submitting || answered < total}
          >
            {submitting ? "Submitting…" : "Submit Survey"}
          </button>
          {answered < total && (
            <span className="submit-hint">
              {total - answered} smell{total - answered !== 1 ? "s" : ""} left
              to rate
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Survey;
