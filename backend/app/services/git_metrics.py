# app/services/git_metrics.py

"""
Git-based metrics calculation for test smell prioritization.

Implements EXACTLY the methodology from:
"Prioritizing Test Smells: An Empirical Evaluation of Quality Metrics
and Developer Perceptions" (ICSME 2025)

Metrics computed:
  ChgFreq  = (Prod_Changes / Prod_TotalCommits) + (Test_Changes / Test_TotalCommits)
  ChgExt   = (Prod_CodeChurn / Prod_TotalCommits) + (Test_CodeChurn / Test_TotalCommits)
  FaultFreq = (Prod_FaultyChanges / Prod_TotalCommits) + (Test_FaultyChanges / Test_TotalCommits)
  FaultExt  = (Prod_FaultyChurn / Prod_TotalCommits) + (Test_FaultyChurn / Test_TotalCommits)

  CP(S) = rho(smell_presence, ChgFreq)  + rho(smell_presence, ChgExt)
  FP(S) = rho(smell_presence, FaultFreq) + rho(smell_presence, FaultExt)
  PS(S) = (CP(S) + FP(S)) / 2

Where rho is Spearman rank correlation coefficient, computed across all
test files in the repository (one data point per file).
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr


# =====================================================
# CONSTANTS
# =====================================================

FAULT_KEYWORDS = [
    'bug', 'fix', 'error', 'defect', 'issue', 'fault',
    'crash', 'patch', 'repair', 'correct', 'resolve',
]


# =====================================================
# STEP 1 - GIT HISTORY EXTRACTION
# =====================================================

def extract_git_history(repo_path: Path) -> List[Dict]:
    """
    Extract full commit history from a Git repository using --numstat.

    Each commit dict:
    {
        'hash':          str,
        'message':       str,
        'timestamp':     str,
        'is_faulty':     bool,
        'files_changed': { filename: {'additions': int, 'deletions': int} }
    }
    """
    commits = []

    try:
        check = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        if check.returncode != 0:
            print(f"[ERROR] Not a git repository: {repo_path}")
            return []

        result = subprocess.run(
            ['git', 'log', '--numstat', '--format=%H|%s|%ai', '--no-merges'],
            cwd=repo_path, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"[ERROR] git log failed: {result.stderr}")
            return []

        current_commit: Optional[Dict] = None

        for line in result.stdout.strip().split('\n'):
            line = line.rstrip()

            # Commit header line: "HASH|subject|date"
            if '|' in line and len(line) > 40 and re.match(r'^[0-9a-f]{7,40}\|', line):
                if current_commit:
                    commits.append(current_commit)
                parts = line.split('|', 2)
                if len(parts) == 3:
                    current_commit = {
                        'hash':          parts[0].strip(),
                        'message':       parts[1].strip(),
                        'timestamp':     parts[2].strip(),
                        'is_faulty':     _is_faulty_commit(parts[1]),
                        'files_changed': {},
                    }

            # Numstat file line: "additions<TAB>deletions<TAB>filename"
            elif line and current_commit and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 3:
                    add_str, del_str, filename = parts
                    additions = 0 if add_str == '-' else int(add_str)
                    deletions = 0 if del_str == '-' else int(del_str)
                    current_commit['files_changed'][filename] = {
                        'additions': additions,
                        'deletions': deletions,
                    }

        if current_commit:
            commits.append(current_commit)

    except Exception as exc:
        print(f"[ERROR] extract_git_history: {exc}")
        return []

    print(f"[GIT] Extracted {len(commits)} commits from {repo_path.name}")
    return commits


def _is_faulty_commit(message: str) -> bool:
    """Return True if the commit message indicates a bug fix."""
    msg = message.lower()
    return any(kw in msg for kw in FAULT_KEYWORDS)


# =====================================================
# STEP 2 - FILE CLASSIFICATION
# =====================================================

def is_test_file(filename: str) -> bool:
    """Return True if filename looks like a test file."""
    f = filename.lower().replace('\\', '/')
    return (
        '/test_'   in f or
        '_test.'   in f or
        '/tests/'  in f or
        f.startswith('test_') or
        f.startswith('tests/')
    )


def is_production_file(filename: str) -> bool:
    """Return True if filename is a non-test Python source file."""
    f = filename.lower()
    return (
        f.endswith('.py') and
        not is_test_file(f) and
        not f.endswith('__init__.py') and
        'setup.py' not in f
    )


def _normalize(path: str) -> str:
    return path.replace('\\', '/').lower().strip('/')


def paths_match(smell_path: str, git_path: str) -> bool:
    """Flexible path matcher handling different root prefixes."""
    a = _normalize(smell_path)
    b = _normalize(git_path)
    if a == b:
        return True
    if a.endswith(b) or b.endswith(a):
        return True
    fa, fb = a.split('/')[-1], b.split('/')[-1]
    return fa == fb and fa.startswith('test')


# =====================================================
# STEP 3 - RAW FILE METRICS FROM GIT
# =====================================================

def _build_file_metrics(commits: List[Dict]) -> Dict[str, Dict]:
    """
    Aggregate per-file commit statistics from the full history.

    Returns:
        { filename: {
            'total_changes':  int,
            'total_churn':    int,
            'faulty_changes': int,
            'faulty_churn':   int,
        }}
    """
    metrics: Dict[str, Dict] = defaultdict(lambda: {
        'total_changes':  0,
        'total_churn':    0,
        'faulty_changes': 0,
        'faulty_churn':   0,
    })

    for commit in commits:
        for filename, change in commit['files_changed'].items():
            churn = change['additions'] + change['deletions']
            metrics[filename]['total_changes']  += 1
            metrics[filename]['total_churn']    += churn
            if commit['is_faulty']:
                metrics[filename]['faulty_changes'] += 1
                metrics[filename]['faulty_churn']   += churn

    return dict(metrics)


# =====================================================
# STEP 4 - CO-CHANGE MAPPING (test file -> production files)
# =====================================================

def _build_cochange_map(
    test_files: List[str],
    commits: List[Dict],
) -> Dict[str, Set[str]]:
    """
    For each test file, find all production files committed together with it
    (co-change pattern from the paper).

    Returns:
        { test_file: set(prod_file, ...) }
    """
    cochange: Dict[str, Set[str]] = defaultdict(set)

    for commit in commits:
        changed = list(commit['files_changed'].keys())
        changed_test = [f for f in changed if is_test_file(f)]
        changed_prod = [f for f in changed if is_production_file(f)]

        if not changed_test or not changed_prod:
            continue

        for tf in changed_test:
            for canonical_tf in test_files:
                if paths_match(canonical_tf, tf):
                    for pf in changed_prod:
                        cochange[canonical_tf].add(pf)
                    break

    return dict(cochange)


# =====================================================
# STEP 5 - COMBINED METRIC VECTORS (paper formulas 1-4)
# =====================================================

def _build_combined_vectors(
    test_files: List[str],
    file_metrics: Dict[str, Dict],
    cochange_map: Dict[str, Set[str]],
    total_commits: int,
) -> Dict[str, Dict[str, float]]:
    """
    For every test file compute the four combined metrics (equations 1-4):

    ChgFreq(file)  = Prod_Changes/Prod_Total + Test_Changes/Test_Total
    ChgExt(file)   = Prod_Churn/Prod_Total   + Test_Churn/Test_Total
    FaultFreq(file)= Prod_Faulty/Prod_Total  + Test_Faulty/Test_Total
    FaultExt(file) = Prod_FChurn/Prod_Total  + Test_FChurn/Test_Total

    Where:
      Prod_Total = sum of total_changes across ALL production files in the project
      Test_Total = sum of total_changes across ALL test files in the project
    """
    # Separate denominators as specified in the paper (not a single total_commits)
    prod_total = sum(
        m['total_changes'] for f, m in file_metrics.items() if is_production_file(f)
    ) or 1
    test_total = sum(
        m['total_changes'] for f, m in file_metrics.items() if is_test_file(f)
    ) or 1

    vectors: Dict[str, Dict[str, float]] = {}

    for tf in test_files:
        tm = file_metrics.get(tf, {})
        if not tm:
            for git_path, m in file_metrics.items():
                if paths_match(tf, git_path):
                    tm = m
                    break

        test_changes = tm.get('total_changes',  0)
        test_churn   = tm.get('total_churn',    0)
        test_faulty  = tm.get('faulty_changes', 0)
        test_f_churn = tm.get('faulty_churn',   0)

        prod_files = cochange_map.get(tf, set())
        prod_changes = prod_churn = prod_faulty = prod_f_churn = 0

        for pf in prod_files:
            pm = file_metrics.get(pf, {})
            if not pm:
                for git_path, m in file_metrics.items():
                    if paths_match(pf, git_path):
                        pm = m
                        break
            prod_changes += pm.get('total_changes',  0)
            prod_churn   += pm.get('total_churn',    0)
            prod_faulty  += pm.get('faulty_changes', 0)
            prod_f_churn += pm.get('faulty_churn',   0)

        vectors[tf] = {
            'chg_freq':   (prod_changes / prod_total) + (test_changes / test_total),
            'chg_ext':    (prod_churn   / prod_total) + (test_churn   / test_total),
            'fault_freq': (prod_faulty  / prod_total) + (test_faulty  / test_total),
            'fault_ext':  (prod_f_churn / prod_total) + (test_f_churn / test_total),
        }

    return vectors


# =====================================================
# STEP 6 - SPEARMAN CORRELATION -> CP / FP / PS
# =====================================================

SMELL_ABBREVIATIONS = {
    'Conditional Test Logic':          'CTL',
    'Assertion Roulette':              'AR',
    'Duplicate Assert':                'DA',
    'Magic Number Test':               'MNT',
    'Obscure In-Line Setup':           'OS',
    'Redundant Assertion':             'RA',
    'Exception Handling':              'EH',
    'Constructor Initialization':      'CI',
    'Suboptimal Assert':               'SA',
    'Test Maverick':                   'TM',
    'Redundant Print':                 'RP',
    'General Fixture':                 'GF',
    'Sleepy Test':                     'ST',
    'Empty Test':                      'ET',
    'Lack of Cohesion of Test Cases':  'LCTC',
}


def _spearman(x: List[float], y: List[float]) -> tuple:
    """Compute Spearman rho. Returns (0.0, 1.0) if insufficient variance."""
    arr_x = np.array(x, dtype=float)
    arr_y = np.array(y, dtype=float)

    if arr_x.std() == 0 or arr_y.std() == 0:
        return 0.0, 1.0
    if len(arr_x) < 3:
        return 0.0, 1.0

    rho, p = spearmanr(arr_x, arr_y)
    return float(rho), float(p)


def calculate_spearman_metrics(
    smell_instances: List[Dict],
    combined_vectors: Dict[str, Dict[str, float]],
    all_test_files: List[str],
) -> Dict[str, Dict]:
    """
    Core calculation - implements paper equations (1)-(5):

    CP(S) = rho(presence, chg_freq) + rho(presence, chg_ext)
    FP(S) = rho(presence, fault_freq) + rho(presence, fault_ext)
    PS(S) = (CP(S) + FP(S)) / 2
    """
    smells_by_type: Dict[str, List[Dict]] = defaultdict(list)
    for inst in smell_instances:
        smells_by_type[inst['type']].append(inst)

    chg_freq_col   = [combined_vectors.get(tf, {}).get('chg_freq',   0.0) for tf in all_test_files]
    chg_ext_col    = [combined_vectors.get(tf, {}).get('chg_ext',    0.0) for tf in all_test_files]
    fault_freq_col = [combined_vectors.get(tf, {}).get('fault_freq', 0.0) for tf in all_test_files]
    fault_ext_col  = [combined_vectors.get(tf, {}).get('fault_ext',  0.0) for tf in all_test_files]

    results: Dict[str, Dict] = {}

    for smell_type, instances in smells_by_type.items():
        abbr = SMELL_ABBREVIATIONS.get(smell_type, smell_type[:4].upper())
        smell_files: Set[str] = set(inst['file'] for inst in instances)

        presence: List[float] = [
            1.0 if any(paths_match(tf, sf) for sf in smell_files) else 0.0
            for tf in all_test_files
        ]

        rho_cf, p_cf = _spearman(presence, chg_freq_col)
        rho_ce, p_ce = _spearman(presence, chg_ext_col)
        rho_ff, p_ff = _spearman(presence, fault_freq_col)
        rho_fe, p_fe = _spearman(presence, fault_ext_col)

        cp_score = rho_cf + rho_ce
        fp_score = rho_ff + rho_fe
        ps_score = (cp_score + fp_score) / 2

        results[smell_type] = {
            'smell_type':   smell_type,
            'abbreviation': abbr,
            'change_frequency_rho':  round(rho_cf, 4),
            'change_extent_rho':     round(rho_ce, 4),
            'fault_frequency_rho':   round(rho_ff, 4),
            'fault_extent_rho':      round(rho_fe, 4),
            'p_values': {
                'cf': round(p_cf, 4),
                'ce': round(p_ce, 4),
                'ff': round(p_ff, 4),
                'fe': round(p_fe, 4),
            },
            'significant': {
                'cf': p_cf < 0.05,
                'ce': p_ce < 0.05,
                'ff': p_ff < 0.05,
                'fe': p_fe < 0.05,
            },
            'cp_score':             round(cp_score, 4),
            'fp_score':             round(fp_score, 4),
            'prioritization_score': round(ps_score, 4),
            'instance_count':       len(instances),
            'affected_test_files':  len(smell_files),
            'files_with_smell':     list(smell_files),
        }

        print(
            f"  [{abbr:4}] CF={rho_cf:+.4f} CE={rho_ce:+.4f} | "
            f"FF={rho_ff:+.4f} FE={rho_fe:+.4f} | "
            f"CP={cp_score:+.4f} FP={fp_score:+.4f} | "
            f"PS={ps_score:+.4f}  ({len(instances)} instances)"
        )

    return results


# =====================================================
# STEP 7 - RANKING (paper Section III-D)
# =====================================================

def rank_smells(metrics: Dict[str, Dict]) -> List[Dict]:
    """Sort smells by Prioritization Score descending."""
    ranked = sorted(
        metrics.values(),
        key=lambda x: x.get('prioritization_score', 0.0),
        reverse=True,
    )
    for i, entry in enumerate(ranked, start=1):
        entry['data_rank'] = i
    return ranked


# =====================================================
# MAIN ENTRY POINT
# =====================================================

def analyze_project_with_git(
    project_path: Path,
    smell_instances: List[Dict],
) -> Dict:
    """
    Full pipeline - call this from the service/API layer.

    Returns:
        {
            'ranked_smells': [...sorted by PS desc...],
            'metrics':       { smell_type: {...} },
            'statistics':    { total_commits, faulty_commits, ... },
        }
    """
    print(f"\n{'='*60}")
    print(f"  Analyzing: {project_path.name}")
    print(f"{'='*60}")

    commits = extract_git_history(project_path)
    if not commits:
        return {'error': 'No git history found or not a git repository.', 'metrics': {}}

    total_commits  = len(commits)
    faulty_commits = [c for c in commits if c['is_faulty']]

    print(f"[GIT] Total commits : {total_commits}")
    print(f"[GIT] Faulty commits: {len(faulty_commits)} "
          f"({100*len(faulty_commits)/total_commits:.1f}%)")

    file_metrics       = _build_file_metrics(commits)
    all_git_test_files = sorted(f for f in file_metrics if is_test_file(f))
    all_git_prod_files = sorted(f for f in file_metrics if is_production_file(f))

    print(f"[GIT] Test files in history  : {len(all_git_test_files)}")
    print(f"[GIT] Prod files in history  : {len(all_git_prod_files)}")

    smell_test_files: Set[str] = set(inst['file'] for inst in smell_instances)
    all_test_files: List[str]  = sorted(smell_test_files | set(all_git_test_files))

    print(f"[SMELL] Test files with smells: {len(smell_test_files)}")
    print(f"[TOTAL] Test file population  : {len(all_test_files)}")

    if not all_test_files:
        return {'error': 'No test files found in git history or smell instances.', 'metrics': {}}

    print("\n[STEP 4] Building co-change map...")
    cochange_map = _build_cochange_map(all_test_files, commits)
    mapped = sum(1 for v in cochange_map.values() if v)
    print(f"[COCHANGE] {mapped}/{len(all_test_files)} test files "
          f"have co-changed production files")

    print("\n[STEP 5] Computing combined metric vectors...")
    combined_vectors = _build_combined_vectors(
        all_test_files, file_metrics, cochange_map, total_commits
    )

    print("\n[STEP 6] Computing Spearman correlations (CP / FP / PS)...")
    metrics = calculate_spearman_metrics(smell_instances, combined_vectors, all_test_files)

    if not metrics:
        return {'error': 'No metrics could be computed. Check smell instances.', 'metrics': {}}

    print("\n[STEP 7] Ranking smells by Prioritization Score...")
    ranked = rank_smells(metrics)

    print("\n[RESULTS] Final Ranking:")
    print(f"  {'Rank':<5} {'Abbr':<6} {'PS':>7}  {'CP':>7}  {'FP':>7}  Smell")
    print(f"  {'-'*60}")
    for entry in ranked:
        print(
            f"  {entry['data_rank']:<5} "
            f"{entry['abbreviation']:<6} "
            f"{entry['prioritization_score']:>+7.4f}  "
            f"{entry['cp_score']:>+7.4f}  "
            f"{entry['fp_score']:>+7.4f}  "
            f"{entry['smell_type']}"
        )

    statistics = {
        'total_commits':         total_commits,
        'faulty_commits':        len(faulty_commits),
        'fault_commit_pct':      round(100 * len(faulty_commits) / total_commits, 2),
        'total_test_files':      len(all_test_files),
        'total_prod_files':      len(all_git_prod_files),
        'smell_types_analyzed':  len(metrics),
        'total_smell_instances': len(smell_instances),
    }

    return {
        'ranked_smells': ranked,
        'metrics':       metrics,
        'statistics':    statistics,
    }
