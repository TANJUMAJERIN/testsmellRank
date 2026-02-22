# How the System Works — From Input to CP/FP Score

---

## Two Ways to Submit a Project

### Option A — GitHub URL okay thennn

You paste a GitHub repository URL (e.g. `https://github.com/user/myproject`).

What happens behind the scenes:

```
POST /api/upload/github   { "repo_url": "https://github.com/user/myproject" }
         │
         ▼
git clone https://github.com/user/myproject
         │
         ▼
Saved to:  uploaded_projects/user_<userId>/myproject/
```

The cloned folder is a **full git repository** — it contains all code files **and** the `.git/` folder with the complete commit history.

---

### Option B — ZIP File

You upload a `.zip` of your project.

What happens:

```
POST /api/upload/zip   (multipart form, file=myproject.zip)
         │
         ▼
ZIP extracted to:  uploaded_projects/user_<userId>/myproject/
```

> **Important**: A ZIP has **no `.git/` folder**, so git commit history is unavailable.  
> Smell detection still runs, but CP and FP scores will be `0.0` because there are no commits to analyze.

---

## Where the `.git` Folder Lives

After cloning, the directory structure on the server looks like this:

```
uploaded_projects/
└── user_<userId>/
    └── myproject/               ← project root passed to all analysis functions
        ├── .git/                ← full git history lives here
        │   ├── objects/
        │   ├── refs/
        │   └── logs/
        ├── src/
        └── tests/
            ├── test_example.py
            └── test_another.py
```

The path `uploaded_projects/user_<userId>/myproject` is passed directly to:

- `detect_smells_for_project(project_dir)` — smell detection
- `analyze_project_with_git(project_dir, smell_instances)` — git metrics

---

## How Commit History Is Read

Inside `git_metrics.py`, the function `extract_git_history(repo_path)` runs:

```bash
git log --numstat --format="%H|%s|%ai" --no-merges
```

This is executed **as a subprocess** in the `project_dir` (which contains `.git/`).

It outputs something like:

```
abc123|fix: resolve assertion bug|2024-11-01 10:32:00 +0000

3       1       tests/test_login.py
0       2       src/auth.py

def456|feature: add register form|2024-10-28 09:10:00 +0000

5       0       tests/test_register.py
12      0       src/register.py
```

Each entry gives us:
| Field | Meaning |
|-------|---------|
| `abc123` | Commit hash |
| `fix: resolve assertion bug` | Commit message |
| `2024-11-01 ...` | Timestamp |
| `3` / `1` | Lines added / deleted in that file |
| `tests/test_login.py` | File touched in that commit |

**Faulty commit detection**: if the message contains any of these keywords —  
`bug`, `fix`, `error`, `defect`, `issue`, `fault`, `crash`, `patch`, `repair`, `correct`, `resolve` —  
the commit is marked `is_faulty = True`.

---

## From Commits to CP and FP Score

After extracting history, the pipeline has 5 more steps:

### Step 1 — Count stats per file

For every file ever touched:

| Counter          | How it's built                                     |
| ---------------- | -------------------------------------------------- |
| `total_changes`  | How many commits touched this file                 |
| `total_churn`    | Total (additions + deletions) across all commits   |
| `faulty_changes` | Commits that touched this file **and** were faulty |
| `faulty_churn`   | Lines changed in those faulty commits              |

---

### Step 2 — Co-change mapping

For each test file, we find all **production files committed in the same commit**.  
Example: if `test_login.py` and `auth.py` appear together in 8 commits, `auth.py` is a co-change partner of `test_login.py`.

This links "what production code does this test cover based on history?"

---

### Step 3 — Four combined metrics per test file

Let **N** = total commits.

```
ChgFreq(f)  = (prod_changes + test_changes) / N
ChgExt(f)   = (prod_churn   + test_churn)   / N
FaultFreq(f)= (prod_faulty  + test_faulty)  / N
FaultExt(f) = (prod_f_churn + test_f_churn) / N
```

These are computed for **every test file** in the repository.

---

### Step 4 — Spearman correlation

For a given smell type (e.g. _Assertion Roulette_):

1. Build a **presence vector** — one value per test file:

   ```
   presence[f] = 1   if test file f has this smell
   presence[f] = 0   otherwise
   ```

2. Compute **Spearman ρ** between that vector and each of the four metric columns:

| Correlation            | Question it answers                            |
| ---------------------- | ---------------------------------------------- |
| ρ(presence, ChgFreq)   | Do smelly files change more often?             |
| ρ(presence, ChgExt)    | Do smelly files have larger churns?            |
| ρ(presence, FaultFreq) | Do smelly files appear in more bug commits?    |
| ρ(presence, FaultExt)  | Do smelly files have larger bug-commit churns? |

Spearman is rank-based — it handles skewed git data well.

---

### Step 5 — CP, FP, PS

```
CP(smell) = ρ_ChgFreq  + ρ_ChgExt
FP(smell) = ρ_FaultFreq + ρ_FaultExt
PS(smell) = (CP + FP) / 2
```

Smells are then sorted by **PS descending** — rank 1 is the most urgent to fix.

---

## Full Flow Diagram

```
User submits GitHub URL
        │
        ▼
git clone → uploaded_projects/user_<id>/repo/
        │                    │
        │                    └── .git/  ← commit history
        ▼
detect_smells_for_project(project_dir)
        │
        ├─ scan all test_*.py files with AST parser
        │        → list of smell instances [{type, file, line}, ...]
        │
        └─ analyze_project_with_git(project_dir, smell_instances)
                 │
                 ├─ git log --numstat   (reads .git/ folder)
                 ├─ mark faulty commits (keyword match)
                 ├─ count changes/churn per file
                 ├─ build co-change map (test ↔ prod)
                 ├─ compute ChgFreq / ChgExt / FaultFreq / FaultExt per test file
                 ├─ Spearman ρ for each smell type
                 └─ CP / FP / PS → ranked list

        ▼
Response JSON:
{
  "smell_analysis": {
    "total_files": 12,
    "total_smells": 47,
    "details": [...],
    "git_metrics": {
      "ranked_smells": [
        { "smell_type": "Assertion Roulette", "data_rank": 1,
          "cp_score": 0.42, "fp_score": 0.81, "prioritization_score": 0.615 },
        ...
      ],
      "statistics": {
        "total_commits": 234,
        "faulty_commits": 31,
        "fault_commit_pct": 13.25
      }
    }
  }
}
```

---

## What Happens Without a `.git` Folder (ZIP Upload)

| Step              | With `.git`                | Without `.git` (ZIP)                 |
| ----------------- | -------------------------- | ------------------------------------ |
| Smell detection   | ✅ runs                    | ✅ runs                              |
| Commit extraction | ✅ `git log` reads history | ❌ `git rev-parse` fails → 0 commits |
| CP / FP scores    | ✅ computed from history   | `0.0` (no data)                      |
| Ranking           | ✅ meaningful              | All scores equal — order arbitrary   |

To get meaningful CP/FP scores from a ZIP, the ZIP must contain the `.git/` folder (i.e., zip the repository root including the hidden `.git` directory).
