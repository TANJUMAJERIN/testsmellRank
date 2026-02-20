# How CP, FP, and Priority Score Are Calculated

This tool ranks test smells using a methodology from the ICSME 2025 paper:
**"Prioritizing Test Smells: An Empirical Evaluation of Quality Metrics and Developer Perceptions"**

---

## The Big Picture

For every type of test smell (e.g., _Assertion Roulette_, _Magic Number Test_), we ask two questions:

1. **CP — Change Proneness**: Do test files that have this smell get changed more often than clean files?
2. **FP — Fault Proneness**: Do test files that have this smell appear more often in bug-fix commits?

A smell that scores high on both is the most urgent to fix — it shows up in files that change frequently _and_ in files linked to real bugs.

---

## Step-by-Step Pipeline

### Step 1 — Extract Git History

We run `git log --numstat` on the repository and collect every commit:

- **Is it a faulty commit?** — We check the commit message for keywords like `fix`, `bug`, `error`, `defect`, `crash`, `patch`, etc.
- **Which files changed?** — We record every file touched, plus how many lines were added/deleted (the _churn_).

---

### Step 2 — Classify Files

Each file in the git history is labelled as either a **test file** or a **production file**:

| Type            | Rule                                                      |
| --------------- | --------------------------------------------------------- |
| Test file       | Path contains `/test_`, `/tests/`, or starts with `test_` |
| Production file | Ends in `.py`, is not a test file, not `__init__.py`      |

---

### Step 3 — Build Raw Metrics Per File

For every file we compute four counters from the full commit history:

| Counter          | Meaning                                                 |
| ---------------- | ------------------------------------------------------- |
| `total_changes`  | How many commits touched this file                      |
| `total_churn`    | Total lines added + deleted across all commits          |
| `faulty_changes` | How many of those commits were faulty (bug-fix) commits |
| `faulty_churn`   | Lines changed in faulty commits only                    |

---

### Step 4 — Co-Change Mapping

A test file often does not break on its own — it breaks because the production code it tests changed.

For every test file we find all **production files that were committed together with it** (in the same commit). This gives us a co-change partner list.

---

### Step 5 — Compute Four Combined Metrics Per Test File

Let **N** = total number of commits in the repository.

For each test file we combine its own stats with its co-changed production files' stats:

$$\text{ChgFreq}(f) = \frac{\text{Prod\_Changes}}{N} + \frac{\text{Test\_Changes}}{N}$$

$$\text{ChgExt}(f) = \frac{\text{Prod\_Churn}}{N} + \frac{\text{Test\_Churn}}{N}$$

$$\text{FaultFreq}(f) = \frac{\text{Prod\_FaultyChanges}}{N} + \frac{\text{Test\_FaultyChanges}}{N}$$

$$\text{FaultExt}(f) = \frac{\text{Prod\_FaultyChurn}}{N} + \frac{\text{Test\_FaultyChurn}}{N}$$

These four numbers summarise how active and how fault-prone a test file is.

---

### Step 6 — Spearman Correlation → CP and FP

This is the core of the algorithm.

For a given smell type (e.g., _Assertion Roulette_) we build a **presence vector** over all test files:

```
presence[f] = 1  if file f contains this smell
presence[f] = 0  if it does not
```

We then compute the **Spearman rank correlation** (ρ) between that presence vector and each of the four metric columns (one value per test file):

| Correlation            | Meaning                                                   |
| ---------------------- | --------------------------------------------------------- |
| ρ(presence, ChgFreq)   | Does the smell appear in frequently-changed files?        |
| ρ(presence, ChgExt)    | Does the smell appear in files with large churns?         |
| ρ(presence, FaultFreq) | Does the smell appear in files linked to many bug fixes?  |
| ρ(presence, FaultExt)  | Does the smell appear in files with large bug-fix churns? |

> **Why Spearman?**  
> Spearman does not assume a linear relationship. It only looks at the _ranking order_, making it robust to outliers and skewed distributions — common in git history data.

---

### Step 7 — Combine into CP, FP, and PS

$$\text{CP}(S) = \rho(\text{presence},\, \text{ChgFreq}) + \rho(\text{presence},\, \text{ChgExt})$$

$$\text{FP}(S) = \rho(\text{presence},\, \text{FaultFreq}) + \rho(\text{presence},\, \text{FaultExt})$$

$$\text{PS}(S) = \frac{\text{CP}(S) + \text{FP}(S)}{2}$$

| Score | Range        | Interpretation                                         |
| ----- | ------------ | ------------------------------------------------------ |
| CP    | −2.0 to +2.0 | How strongly the smell correlates with change activity |
| FP    | −2.0 to +2.0 | How strongly the smell correlates with fault activity  |
| PS    | −2.0 to +2.0 | Overall prioritization score — **higher = fix first**  |

---

## Reading the Results Table

```
Rank  Abbr    PS        CP        FP       Smell
---------------------------------------------------------
1     AR    +0.6120  +0.4230  +0.8010   Assertion Roulette
2     CTL   +0.5340  +0.6120  +0.4560   Conditional Test Logic
3     MNT   +0.2100  +0.1980  +0.2220   Magic Number Test
...
```

- **Rank 1** = highest PS = most urgent smell to address
- A **positive PS** means the smell is genuinely correlated with changes and faults
- A **near-zero or negative PS** means the smell has little correlation with project health

---

## Quick Summary

```
Git History
    │
    ├─ Count changes & churn per file  ──────────────────────────────────┐
    │                                                                     │
    └─ Find which commits are bug fixes ─────────────────────────────────┤
                                                                          │
                                              Four metrics per test file  │
                                         (ChgFreq, ChgExt, FaultFreq, FaultExt)
                                                                          │
For each smell type:                                                      │
    Build presence vector (1/0 per test file)                            │
    Spearman ρ with each metric column  ──────────────────────────────────┘
        │
        ├─ CP = ρ_ChgFreq + ρ_ChgExt
        ├─ FP = ρ_FaultFreq + ρ_FaultExt
        └─ PS = (CP + FP) / 2  →  RANK
```
