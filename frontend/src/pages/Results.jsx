// import React, { useState, useEffect } from "react";
// import { useLocation, useNavigate } from "react-router-dom";
// import { useAuth } from "../context/AuthContext";
// import "./Results.css";

// const Results = () => {
//   const { user, logout } = useAuth();
//   const navigate = useNavigate();
//   const location = useLocation();

//   const [loading, setLoading] = useState(true);
//   const [results, setResults] = useState(null);

//   const projectData = location.state?.projectData;

//   useEffect(() => {
//     if (!projectData || !projectData.smell_analysis) {
//       navigate("/dashboard");
//       return;
//     }

//     setResults(projectData.smell_analysis);
//     setLoading(false);
//   }, [projectData, navigate]);

//   const handleLogout = () => {
//     logout();
//     navigate("/login");
//   };

//   const handleBackToDashboard = () => {
//     navigate("/dashboard");
//   };

//   const getSmellColor = (smellCount) => {
//     if (smellCount === 0) return "#4caf50"; // green
//     if (smellCount <= 3) return "#ff9800"; // orange
//     return "#f44336"; // red
//   };

//   return (
//     <div className="results-container">
//       <nav className="navbar">
//         <div className="navbar-content">
//           <h1 className="navbar-title">Test Smell Rank</h1>
//           <div className="navbar-right">
//             <span className="user-name">Welcome, {user?.full_name}!</span>
//             <button onClick={handleLogout} className="logout-button">
//               Logout
//             </button>
//           </div>
//         </div>
//       </nav>

//       <div className="results-content">
//         <div className="results-header">
//           <button onClick={handleBackToDashboard} className="back-button">
//             ← Back to Dashboard
//           </button>
//           <h2>Test Smell Detection Results</h2>

//           {projectData?.project_name && (
//             <p className="project-name">
//               Project: <strong>{projectData.project_name}</strong>
//             </p>
//           )}
//         </div>

//         {loading && (
//           <div className="loading-container">
//             <div className="spinner"></div>
//             <p>Analyzing test smells...</p>
//           </div>
//         )}

//         {!loading && results && (
//           <div className="results-summary">
//             {/* Summary Cards */}
//             <div className="summary-cards">
//               <div className="summary-card">
//                 <div className="summary-icon">📁</div>
//                 <div className="summary-info">
//                   <h3>{results.total_files}</h3>
//                   <p>Test Files Analyzed</p>
//                 </div>
//               </div>

//               <div className="summary-card">
//                 <div className="summary-icon">⚠️</div>
//                 <div className="summary-info">
//                   <h3>{results.total_smells}</h3>
//                   <p>Total Smells Detected</p>
//                 </div>
//               </div>

//               <div className="summary-card">
//                 <div className="summary-icon">📊</div>
//                 <div className="summary-info">
//                   <h3>
//                     {results.total_files > 0
//                       ? (results.total_smells / results.total_files).toFixed(1)
//                       : 0}
//                   </h3>
//                   <p>Avg Smells per File</p>
//                 </div>
//               </div>
//             </div>

//             {/* Detailed Results */}
//             {results.details && results.details.length > 0 ? (
//               <div className="smell-details">
//                 <h3>Detailed Results by File</h3>

//                 {results.details.map((fileResult, index) => (
//                   <div key={index} className="file-result">
//                     <div className="file-header">
//                       <div className="file-info">
//                         <span className="file-icon">📄</span>
//                         <span className="file-name">{fileResult.file}</span>
//                       </div>

//                       <div
//                         className="smell-badge"
//                         style={{
//                           backgroundColor: getSmellColor(
//                             fileResult.smell_count
//                           ),
//                         }}
//                       >
//                         {fileResult.smell_count} smell
//                         {fileResult.smell_count !== 1 ? "s" : ""}
//                       </div>
//                     </div>

//                     {fileResult.error ? (
//                       <div className="file-error">
//                         <p>Error: {fileResult.error}</p>
//                       </div>
//                     ) : fileResult.smells &&
//                       fileResult.smells.length > 0 ? (
//                       <ul className="smell-list">
//                         {fileResult.smells.map((smell, smellIndex) => (
//                           <li key={smellIndex} className="smell-item">
//                             <strong>{smell.type}</strong>
//                             {smell.line && ` (Line ${smell.line})`}
//                             {smell.message && `: ${smell.message}`}
//                           </li>
//                         ))}
//                       </ul>
//                     ) : (
//                       <div className="no-smells">
//                         <p>✅ No test smells detected in this file!</p>
//                       </div>
//                     )}
//                   </div>
//                 ))}
//               </div>
//             ) : (
//               <div className="no-results">
//                 <div className="no-results-icon">🎉</div>
//                 <h3>Great Job!</h3>
//                 <p>No test smells detected in your project.</p>
//               </div>
//             )}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// };

// export default Results;


import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Results.css";

const Results = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState(null);

  const projectData = location.state?.projectData;

  useEffect(() => {
    if (!projectData || !projectData.smell_analysis) {
      navigate("/dashboard");
      return;
    }

    setResults(projectData.smell_analysis);
    setLoading(false);
  }, [projectData, navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleBackToDashboard = () => {
    navigate("/dashboard");
  };

  const getSmellColor = (smellCount) => {
    if (smellCount === 0) return "#4caf50"; // green
    if (smellCount <= 3) return "#ff9800"; // orange
    return "#f44336"; // red
  };

  return (
    <div className="results-container">
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Test Smell Rank</h1>
          <div className="navbar-right">
            <span className="user-name">
              Welcome, {user?.full_name}!
            </span>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="results-content">
        <div className="results-header">
          <button onClick={handleBackToDashboard} className="back-button">
            ← Back to Dashboard
          </button>
          <h2>Test Smell Detection Results</h2>

          {projectData?.project_name && (
            <p className="project-name">
              Project: <strong>{projectData.project_name}</strong>
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

            {/* ===== SUMMARY CARDS ===== */}
            <div className="summary-cards">
              <div className="summary-card">
                <div className="summary-icon">📁</div>
                <div className="summary-info">
                  <h3>{results.total_files}</h3>
                  <p>Test Files Analyzed</p>
                </div>
              </div>

              <div className="summary-card">
                <div className="summary-icon">⚠️</div>
                <div className="summary-info">
                  <h3>{results.total_smells}</h3>
                  <p>Total Smells Detected</p>
                </div>
              </div>

              <div className="summary-card">
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

            {/* ===== DETAILED RESULTS ===== */}
            {results.details && results.details.length > 0 ? (
              <div className="smell-details">
                <h3>Detailed Results by File</h3>

                {results.details.map((fileResult, index) => (
                  <div key={index} className="file-result">

                    {/* File Header */}
                    <div className="file-header">
                      <div className="file-info">
                        <span className="file-icon">📄</span>
                        <span className="file-name">
                          {fileResult.file}
                        </span>
                      </div>

                      <div
                        className="smell-badge"
                        style={{
                          backgroundColor: getSmellColor(
                            fileResult.smell_count
                          ),
                        }}
                      >
                        {fileResult.smell_count} smell
                        {fileResult.smell_count !== 1 ? "s" : ""}
                      </div>
                    </div>

                    {/* Error Handling */}
                    {fileResult.error ? (
                      <div className="file-error">
                        <p>Error: {fileResult.error}</p>
                      </div>
                    ) : fileResult.smells &&
                      fileResult.smells.length > 0 ? (

                      <ul className="smell-list">
                        {fileResult.smells.map((smell, smellIndex) => (
                          <li key={smellIndex} className="smell-item">

                            <div className="smell-type">
                              🔎 <strong>{smell.type}</strong>
                            </div>

                            {smell.line > 0 && (
                              <div className="smell-line">
                                📍 Line: {smell.line}
                              </div>
                            )}

                            {smell.message && (
                              <div className="smell-message">
                                💬 {smell.message}
                              </div>
                            )}

                          </li>
                        ))}
                      </ul>

                    ) : (
                      <div className="no-smells">
                        <p>✅ No test smells detected in this file!</p>
                      </div>
                    )}
                  </div>
                ))}
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
