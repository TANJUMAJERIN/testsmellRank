# Git Metrics & Prioritization Score — Detailed Explanation

This document explains every step performed by `backend/app/services/git_metrics.py`
to compute the **CP**, **FP**, and **PS (Prioritization Score)** for each detected test smell.

The implementation follows the methodology from:

> _"Prioritizing Test Smells: An Empirical Evaluation of Quality Metrics and Developer Perceptions"_
> — ICSME 2025

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Step 1 — Git History Extraction](#2-step-1--git-history-extraction)
3. [Step 2 — File Classification](#3-step-2--file-classification)
4. [Step 3 — Raw File Metrics](#4-step-3--raw-file-metrics)
5. [Step 4 — Co-Change Mapping](#5-step-4--co-change-mapping)
6. [Step 5 — Combined Metric Vectors](#6-step-5--combined-metric-vectors)
7. [Step 6 — Spearman Correlation → CP / FP / PS](#7-step-6--spearman-correlation--cp--fp--ps)
8. [Step 7 — Ranking](#8-step-7--ranking)
9. [Fault Keywords Reference](#9-fault-keywords-reference)
10. [Complete Formula Summary](#10-complete-formula-summary)
11. [Worked Example](#11-worked-example)

---

## 1. High-Level Overview

The goal is to answer:

> **"Which test smell type is the most important to fix in this project?"**

Instead of answering this with just static code analysis (counting smell instances),
the system uses the **project's entire git history** as evidence.
The core idea: if files containing a certain smell type are frequently changed
and frequently involved in bug fixes, that smell is more urgent to address.

The pipeline has 7 steps:

```
Git Repository
      │
      ▼
[Step 1] Extract all commits (hash, message, files changed, lines added/deleted)
      │
      ▼
[Step 2] Classify each file: test file or production file?
      │
      ▼
[Step 3] Aggregate per-file statistics: how many times changed? how much churn?
         how many times changed in a buggy commit?
      │
      ▼
[Step 4] Co-change mapping: which production files were committed together
         with each test file?
      │
      ▼
[Step 5] Compute 4 combined metric vectors per test file:
         ChgFreq, ChgExt, FaultFreq, FaultExt
      │
      ▼
[Step 6] For each smell type, compute Spearman correlation of smell presence
         against each metric vector → CP, FP, PS scores
      │
      ▼
[Step 7] Rank all smell types by PS descending
```

---

## 2. Step 1 — Git History Extraction

### What command is run?

```bash
git log --numstat --format=%H|%s|%ai --no-merges
```

| Flag                   | Meaning                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| `--numstat`            | For each commit, list every changed file with lines added and deleted                      |
| `--format=%H\|%s\|%ai` | Header line: full commit hash \| subject (first line of message) \| author date (ISO 8601) |
| `--no-merges`          | Skip merge commits — they do not represent real code changes                               |

### What does the raw output look like?

```
abc123def456...|fix: resolve assertion bug|2024-03-15 10:22:01 +0600
3       1       tests/test_login.py
12      4       app/auth.py

9f3e1b2a7c8d...|feat: add new route|2024-03-14 09:00:00 +0600
5       0       app/routes/user.py
```

The parser reads this line by line:

- A line matching the regex `^[0-9a-f]{7,40}\|` is a **commit header**
- A line containing `\t` (tab) is a **numstat file line**

### What is stored per commit?

```python
{
    'hash':          'abc123def456...',
    'message':       'fix: resolve assertion bug',
    'timestamp':     '2024-03-15 10:22:01 +0600',
    'is_faulty':     True,             # determined from message keywords
    'files_changed': {
        'tests/test_login.py': {'additions': 3, 'deletions': 1},
        'app/auth.py':         {'additions': 12, 'deletions': 4},
    }
}
```

### How is `is_faulty` determined?

The commit message is converted to lowercase and checked for any of these
**11 fault-indicating keywords**.
The check is a **case-insensitive substring search** — `fix` matches `fixup`,
`prefix`, `suffix` etc. This is intentionally broad to capture informal messages.

| Keyword   | Intent                    |
| --------- | ------------------------- |
| `bug`     | Direct bug mention        |
| `fix`     | Any kind of fix           |
| `error`   | Error correction          |
| `defect`  | Defect removal            |
| `issue`   | Issue/ticket resolution   |
| `fault`   | Fault correction          |
| `crash`   | Crash fix                 |
| `patch`   | Code patch / hotfix       |
| `repair`  | Repairing broken behavior |
| `correct` | Correctness improvement   |
| `resolve` | Resolving a problem       |

**Examples:**

| Commit Message                   | `is_faulty` | Matched keyword  |
| -------------------------------- | ----------- | ---------------- |
| `fix: resolve test flakiness`    | `True`      | `fix`, `resolve` |
| `bug: correct assertion logic`   | `True`      | `bug`, `correct` |
| `refactor: improve code quality` | `False`     | —                |
| `feature: add new test cases`    | `False`     | —                |
| `patch: security vulnerability`  | `True`      | `patch`          |
| `error handling improvement`     | `True`      | `error`          |

---

## 3. Step 2 — File Classification

Every filename seen in git history is classified into one of two categories.

### Test File

A file is a **test file** if its path (lowercased, forward-slashed) matches any of:

| Pattern              | Example match          |
| -------------------- | ---------------------- |
| Contains `/test_`    | `app/test_auth.py`     |
| Contains `_test.`    | `auth_test.py`         |
| Contains `/tests/`   | `tests/test_login.py`  |
| Starts with `test_`  | `test_utils.py`        |
| Starts with `tests/` | `tests/unit/test_x.py` |

### Production File

A file is a **production file** if:

- It ends with `.py`
- It is NOT a test file
- It is NOT `__init__.py`
- It is NOT `setup.py`

### Path Matching (flexible)

Because the same file can appear with different path prefixes in git vs.
in the smell detector output (e.g. `tests/test_login.py` vs. `./tests/test_login.py`),
a flexible matcher is used. It accepts a match if any of the following hold:

1. Paths are identical after normalisation (lowercase, forward slashes, no leading slash)
2. One path ends with the other (prefix difference)
3. Both filenames are identical **and** start with `test`

---

## 4. Step 3 — Raw File Metrics

For every file ever changed in the git history, four counters are accumulated
by iterating over every commit:

| Field            | How it is computed                                                   |
| ---------------- | -------------------------------------------------------------------- |
| `total_changes`  | +1 for every commit that touched this file                           |
| `total_churn`    | +(additions + deletions) for every commit that touched this file     |
| `faulty_changes` | +1 **only** when the commit is a faulty commit                       |
| `faulty_churn`   | +(additions + deletions) **only** when the commit is a faulty commit |

**Concrete example:**

`tests/test_login.py` appears in 5 commits:

| Commit | Additions | Deletions | Faulty? |
| ------ | --------- | --------- | ------- |
| c1     | 10        | 2         | No      |
| c2     | 3         | 1         | **Yes** |
| c3     | 0         | 5         | No      |
| c4     | 8         | 4         | **Yes** |
| c5     | 2         | 0         | No      |

Result:

```
total_changes  = 5
total_churn    = (12) + (4) + (5) + (12) + (2) = 35
faulty_changes = 2           (c2 and c4)
faulty_churn   = 4 + 12 = 16
```

---

## 5. Step 4 — Co-Change Mapping

This step answers:

> _"Which production files were committed together with each test file?"_

For every commit that contains **both** at least one test file **and** at least
one production file, all those production files are linked to the test file.

**Why is this needed?**

The paper's metrics combine the activity of the test file **and** its associated
production code. This reflects reality: if production code changes frequently
and the test code changes with it, the test is coupled to an unstable part of
the system.

**Example:**

```
Commit A: changed [tests/test_auth.py, app/auth.py, app/models/user.py]
Commit B: changed [tests/test_auth.py, app/views.py]
Commit C: changed [tests/test_api.py, app/api.py]
```

Co-change map:

```
tests/test_auth.py → {app/auth.py, app/models/user.py, app/views.py}
tests/test_api.py  → {app/api.py}
```

Commits where only test files change (no production files present) are skipped
because there is no co-change relationship to record.

---

## 6. Step 5 — Combined Metric Vectors

For each test file, four combined metrics are computed. Let `N` = total number
of commits in the repository.

### Formula 1 — Change Frequency (ChgFreq)

$$ChgFreq(f) = \frac{Prod\_Changes}{N} + \frac{Test\_Changes}{N}$$

Measures **how often** both the test file and its co-changed production files
are modified, normalised by the total commit count.

### Formula 2 — Change Extent (ChgExt)

$$ChgExt(f) = \frac{Prod\_Churn}{N} + \frac{Test\_Churn}{N}$$

Measures **how much** code changes (lines added + deleted) per commit for
the test file and its co-changed production counterparts.

### Formula 3 — Fault Frequency (FaultFreq)

$$FaultFreq(f) = \frac{Prod\_FaultyChanges}{N} + \frac{Test\_FaultyChanges}{N}$$

Same as ChgFreq but **only counting faulty commits** (commits whose messages
contain fault keywords).

### Formula 4 — Fault Extent (FaultExt)

$$FaultExt(f) = \frac{Prod\_FaultyChurn}{N} + \frac{Test\_FaultyChurn}{N}$$

Same as ChgExt but **only counting churn from faulty commits**.

**Note:** `Prod_*` values are the **sum** across all co-changed production files
from Step 4. If a test file has no co-changed production files, those terms are 0.

**Result — each test file gets a 4-element vector:**

```
tests/test_login.py → {
    chg_freq:   0.083,
    chg_ext:    1.250,
    fault_freq: 0.041,
    fault_ext:  0.583
}
```

---

## 7. Step 6 — Spearman Correlation → CP / FP / PS

### What is Spearman Rank Correlation?

Spearman's rho (ρ) measures the **monotonic relationship** between two variables
by comparing their rank orders rather than raw values.

$$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$

where $d_i$ is the rank difference for pair $i$, and $n$ is the number of data points.

| ρ value | Meaning                                 |
| ------- | --------------------------------------- |
| +1      | Perfect positive monotonic relationship |
| 0       | No relationship                         |
| −1      | Perfect negative monotonic relationship |

**Why Spearman instead of Pearson?**
Git history data is inherently skewed (a few files change much more than others).
Spearman is robust to outliers and does not assume linearity or normal distribution.

### Guard Conditions

The system returns `(ρ=0.0, p=1.0)` — meaning no correlation — if:

- Either array has **zero standard deviation** (all values are identical, nothing to correlate)
- There are **fewer than 3 data points** (not statistically meaningful)

### Building the Presence Vector

For each smell type (e.g., "Sleepy Test"), a binary **presence vector** is built
across ALL test files in the project:

```
For each test file:
    presence[i] = 1.0  if the smell was detected in that file
    presence[i] = 0.0  otherwise
```

Example for "Sleepy Test" with 4 test files:

```
test_a.py → 1.0   (has time.sleep())
test_b.py → 0.0
test_c.py → 1.0   (has time.sleep())
test_d.py → 0.0
```

### The 4 Metric Columns

Simultaneously, 4 column vectors are built — one value per test file — from
the combined vectors computed in Step 5:

```
chg_freq_col   = [0.083, 0.020, 0.041, 0.010]
chg_ext_col    = [1.250, 0.100, 0.800, 0.050]
fault_freq_col = [0.041, 0.000, 0.020, 0.000]
fault_ext_col  = [0.583, 0.000, 0.300, 0.000]
```

### Computing CP (Change Proneness Score)

$$CP(S) = \rho(presence,\, ChgFreq) + \rho(presence,\, ChgExt)$$

This answers:

> _"Do the test files that contain smell S tend to be the ones that change more often and more extensively?"_

- `rho_cf` = Spearman(presence_vector, chg_freq_col)
- `rho_ce` = Spearman(presence_vector, chg_ext_col)
- `CP = rho_cf + rho_ce`

**Range:** −2.0 to +2.0

A **high CP** means files with this smell are the most actively changing files
in the project — this smell lives in volatile code.

### Computing FP (Fault Proneness Score)

$$FP(S) = \rho(presence,\, FaultFreq) + \rho(presence,\, FaultExt)$$

This answers:

> _"Do the test files that contain smell S tend to be the ones involved in bug fix commits?"_

- `rho_ff` = Spearman(presence_vector, fault_freq_col)
- `rho_fe` = Spearman(presence_vector, fault_ext_col)
- `FP = rho_ff + rho_fe`

**Range:** −2.0 to +2.0

A **high FP** means files with this smell are disproportionately involved
in fault-related changes — this smell is associated with buggy code.

### Computing PS (Prioritization Score)

$$PS(S) = \frac{CP(S) + FP(S)}{2}$$

The final score is the simple average of CP and FP.

**Range:** −2.0 to +2.0

A **high PS** means the smell is both change-prone AND fault-prone — highest priority to fix.

### Full output stored per smell type

```python
{
    'smell_type':            'Sleepy Test',
    'abbreviation':          'ST',
    'change_frequency_rho':  +0.7071,   # rho_cf
    'change_extent_rho':     +0.6325,   # rho_ce
    'fault_frequency_rho':   +0.8165,   # rho_ff
    'fault_extent_rho':      +0.7746,   # rho_fe
    'p_values': {
        'cf': 0.0312,   # statistical significance of rho_cf
        'ce': 0.0481,
        'ff': 0.0123,
        'fe': 0.0198,
    },
    'significant': {
        'cf': True,    # True if p < 0.05
        'ce': True,
        'ff': True,
        'fe': True,
    },
    'cp_score':             +1.3396,    # rho_cf + rho_ce
    'fp_score':             +1.5911,    # rho_ff + rho_fe
    'prioritization_score': +1.4654,    # (CP + FP) / 2
    'instance_count':       3,          # total smell instances detected
    'affected_test_files':  2,          # number of test files with this smell
    'files_with_smell':     ['tests/test_a.py', 'tests/test_c.py'],
}
```

---

## 8. Step 7 — Ranking

All smell types are sorted by `prioritization_score` descending.
The smell with the highest PS is ranked #1 — it is the most urgent to fix.
A `data_rank` field is added to each entry (1 = highest priority).

**Reading the results table:**

```
Rank  Abbr    PS        CP        FP       Smell
---------------------------------------------------------
1     AR    +0.6120  +0.4230  +0.8010   Assertion Roulette
2     CTL   +0.5340  +0.6120  +0.4560   Conditional Test Logic
3     MNT   +0.2100  +0.1980  +0.2220   Magic Number Test
```

- **Positive PS** → smell correlates with change and fault activity → fix soon
- **Near-zero PS** → smell has little historical evidence of causing problems → lower priority
- **Negative PS** → smell appears in files that are actually _less_ fault-prone

---

## 9. Fault Keywords Reference

| Keyword   | Why it signals a fault commit |
| --------- | ----------------------------- |
| `bug`     | Direct mention of a bug       |
| `fix`     | General fix (most common)     |
| `error`   | Error correction              |
| `defect`  | Formal defect terminology     |
| `issue`   | Issue tracker resolution      |
| `fault`   | Explicit fault correction     |
| `crash`   | Application crash fix         |
| `patch`   | Hotfix / patch release        |
| `repair`  | Repairing broken behavior     |
| `correct` | Correctness improvement       |
| `resolve` | Resolving a known problem     |

**Caution:** Substring matching means `fix` also matches `prefix`, `suffix`, `fixup`.
This broad recall is intentional to avoid missing informal commit messages.

---

## 10. Complete Formula Summary

| Formula          | Expression                                     | What it measures                        |
| ---------------- | ---------------------------------------------- | --------------------------------------- |
| **ChgFreq(f)**   | (Prod_Changes + Test_Changes) / N              | How frequently the file pair is changed |
| **ChgExt(f)**    | (Prod_Churn + Test_Churn) / N                  | Volume of code change per commit        |
| **FaultFreq(f)** | (Prod_FaultyChanges + Test_FaultyChanges) / N  | Frequency of fault-related changes      |
| **FaultExt(f)**  | (Prod_FaultyChurn + Test_FaultyChurn) / N      | Volume of fault-related code churn      |
| **CP(S)**        | ρ(presence, ChgFreq) + ρ(presence, ChgExt)     | Change Proneness of smell S             |
| **FP(S)**        | ρ(presence, FaultFreq) + ρ(presence, FaultExt) | Fault Proneness of smell S              |
| **PS(S)**        | (CP(S) + FP(S)) / 2                            | Final Prioritization Score              |

Where:

- `N` = total number of non-merge commits in the repository
- `ρ` = Spearman rank correlation coefficient (range −1 to +1)
- `presence` = binary vector (1.0/0.0) indicating which test files contain smell S
- `Prod_*` = summed values across all production files that co-changed with the test file

---

## 11. Worked Example

Project: 10 commits total, 4 test files.

### Commit history summary

| Commit | Message                   | Faulty? | Files Changed                        |
| ------ | ------------------------- | ------- | ------------------------------------ |
| c1     | `fix: correct assertion`  | **Yes** | test_a.py (+5/−2), auth.py (+10/−3)  |
| c2     | `feat: add login tests`   | No      | test_a.py (+20/−0), auth.py (+15/−0) |
| c3     | `bug: repair sleep issue` | **Yes** | test_b.py (+2/−1)                    |
| c4     | `refactor: clean up`      | No      | test_c.py (+4/−4), utils.py (+6/−2)  |
| c5     | `fix: patch data error`   | **Yes** | test_a.py (+3/−3), auth.py (+5/−5)   |
| c6–c10 | (other commits)           | No      | (other files only)                   |

### File metrics for test_a.py

```
total_changes  = 3   (c1, c2, c5)
total_churn    = 7 + 20 + 6 = 33
faulty_changes = 2   (c1, c5)
faulty_churn   = 7 + 6 = 13
```

### Co-change map for test_a.py

```
test_a.py → {auth.py}    (appeared together in c1, c2, c5)
```

### auth.py metrics

```
total_changes  = 3,  total_churn  = 38
faulty_changes = 2,  faulty_churn = 23
```

### Combined vectors for test_a.py (N = 10)

```
chg_freq   = (3 + 3) / 10  = 0.60
chg_ext    = (38 + 33) / 10 = 7.10
fault_freq = (2 + 2) / 10  = 0.40
fault_ext  = (23 + 13) / 10 = 3.60
```

### Presence vector for "Sleepy Test"

Suppose Sleepy Test was detected only in test_b.py:

```
test_a.py → 0.0
test_b.py → 1.0
test_c.py → 0.0
test_d.py → 0.0
```

### Spearman computation

Spearman ρ is computed between `[0, 1, 0, 0]` and each metric column:

- `rho_cf` = Spearman([0,1,0,0], [0.60, small, small, small])
- `rho_ce` = Spearman([0,1,0,0], [7.10, small, small, small])
- `rho_ff` = Spearman([0,1,0,0], [0.40, small, small, small])
- `rho_fe` = Spearman([0,1,0,0], [3.60, small, small, small])

### Final scores

```
CP = rho_cf + rho_ce
FP = rho_ff + rho_fe
PS = (CP + FP) / 2   →  used for final ranking
```

Higher PS = fix this smell first.
