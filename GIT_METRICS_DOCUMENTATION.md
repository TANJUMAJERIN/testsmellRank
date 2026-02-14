# Git-Based Test Smell Prioritization

## Overview

This feature calculates **Change Proneness (CP)** and **Fault Proneness (FP)** metrics from Git commit history to prioritize test smells for refactoring. The implementation is based on the research paper "Test Smell Prioritization" (ICSME'25).

## Key Concepts

### Change Proneness (CP)

Measures how frequently files with a particular test smell undergo changes:

- **Change Frequency**: Number of commits affecting test files with the smell
- **Change Extent**: Amount of code churn (additions + deletions) in those commits
- **CP Score = Change Frequency + Change Extent**

### Fault Proneness (FP)

Measures how frequently files with a particular test smell are associated with bug fixes:

- **Fault Frequency**: Number of fault-fixing commits affecting test files with the smell
- **Fault Extent**: Amount of code churn in fault-fixing commits
- **FP Score = Fault Frequency + Fault Extent**

### Prioritization Score (PS)

Combined metric for ranking test smells:

- **PS = (CP + FP) / 2**
- Higher scores indicate more critical test smells that should be refactored first

## Implementation Details

### 1. Git History Extraction

**File**: `backend/app/services/git_metrics.py`

**Function**: `extract_git_history(repo_path)`

- Uses `git log --numstat` to extract commit history
- Captures: commit hash, message, timestamp, file changes, code churn
- Identifies fault-fixing commits using keywords: bug, fix, error, defect, issue, fault, crash, patch

**Example Output**:

```python
[
    {
        'hash': 'abc123...',
        'message': 'fix: resolve test flakiness',
        'timestamp': '2024-01-15 10:30:00',
        'files_changed': {
            'tests/test_module.py': {
                'additions': 15,
                'deletions': 8
            }
        },
        'is_faulty': True
    }
]
```

### 2. Metric Calculation

**Function**: `calculate_smell_metrics(smell_instances, commits)`

Steps:

1. Group smells by type
2. Calculate file-level metrics (total changes, churn, faulty changes)
3. Aggregate metrics for test files containing each smell type
4. Normalize by total commits
5. Calculate CP, FP, and PS scores

**Normalization Formula**:

```
ChgFreq = (prod_changes / prod_total_commits) + (test_changes / test_total_commits)
ChgExt = (prod_churn / prod_total_commits) + (test_churn / test_total_commits)
FaultFreq = (prod_faulty_changes / prod_total_commits) + (test_faulty_changes / test_total_commits)
FaultExt = (prod_faulty_churn / prod_total_commits) + (test_faulty_churn / test_total_commits)
```

### 3. Advanced Correlation Analysis

**Function**: `calculate_correlations(smell_instances, file_metrics, all_test_files)`

Uses **Spearman rank correlation** to measure the relationship between smell presence and metrics:

1. Create binary array: 1 if file has smell, 0 otherwise
2. Create metric arrays: change frequency, change extent, fault frequency, fault extent
3. Calculate Spearman's ρ (rho) for each metric
4. Compute CP = ρ(ChgFreq) + ρ(ChgExt)
5. Compute FP = ρ(FaultFreq) + ρ(FaultExt)

### 4. Integration with Smell Detection

**Modified**: `backend/app/services/smell_detection.py`

The main function now accepts `include_git_metrics` parameter:

```python
def detect_smells_for_project(project_path, include_git_metrics=True):
    # ... detect smells ...

    if include_git_metrics:
        git_analysis = analyze_project_with_git(project_path, all_smell_instances)

    return {
        "total_files": ...,
        "total_smells": ...,
        "details": ...,
        "git_metrics": git_analysis
    }
```

## Frontend Visualization

### Prioritization Table

**File**: `frontend/src/pages/Results.jsx`

Displays a ranked table of test smells with:

- Smell type name
- Number of instances
- CP Score with visual bar
- FP Score with visual bar
- Prioritization Score (bold)
- Ranking badge (color-coded)

**Ranking Color Scheme**:

- **Top 3** (Red): High priority - refactor immediately
- **4-6** (Orange): Medium priority - schedule for refactoring
- **7+** (Blue): Low priority - monitor

### Git Statistics Summary

Shows repository-level metrics:

- Total commits analyzed
- Faulty commits detected
- Fault percentage (%)
- Total files in history
- Test files identified

### Metrics Legend

Explains each metric to users:

- CP Score: Likelihood of code changes
- FP Score: Likelihood of bugs
- Priority Score: Overall urgency

## Usage

### Requirements

1. Project must be a Git repository
2. Git must be installed and accessible via command line
3. Repository must have commit history

### Dependencies

Add to `requirements.txt`:

```
scipy==1.11.4
```

Install:

```bash
pip install scipy
```

### API Response Structure

```json
{
  "total_files": 17,
  "total_smells": 112,
  "details": [...],
  "git_metrics": {
    "metrics": {
      "Conditional Test Logic": {
        "change_frequency": 0.2341,
        "change_extent": 1.5678,
        "fault_frequency": 0.1234,
        "fault_extent": 0.8765,
        "cp_score": 1.8019,
        "fp_score": 0.9999,
        "prioritization_score": 1.4009,
        "test_files": ["tests/test_module.py"],
        "instance_count": 15
      }
    },
    "statistics": {
      "total_commits": 150,
      "faulty_commits": 23,
      "fault_percentage": 15.33,
      "total_files": 45,
      "test_files": 17
    }
  }
}
```

### Error Handling

If Git history is unavailable:

```json
{
  "git_metrics": {
    "error": "No git history found or not a git repository"
  }
}
```

Frontend displays a warning message with instructions.

## Benefits

1. **Data-Driven Prioritization**: Focus refactoring efforts on smells that historically correlate with changes and bugs
2. **Risk Assessment**: Identify which test smells pose the greatest risk to code quality
3. **Resource Optimization**: Allocate developer time efficiently based on measurable metrics
4. **Historical Context**: Leverage project history to make informed decisions

## Limitations

1. Requires Git repository (not available for standalone test files)
2. Accuracy depends on commit history quality
3. Keyword-based fault detection may have false positives/negatives
4. Assumes correlation between smells and metrics (may not imply causation)

## Future Enhancements

1. **Machine Learning**: Train models to predict fault-proneness more accurately
2. **Custom Keywords**: Allow users to configure fault-fixing keywords
3. **Time Decay**: Weight recent commits more heavily
4. **Traceability**: Map test files to specific production modules
5. **Benchmark Data**: Compare against industry standards

## References

- Research Paper: "Test Smell Prioritization" (ICSME'25)
- Spearman Rank Correlation: https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient
- Git Log Documentation: https://git-scm.com/docs/git-log
