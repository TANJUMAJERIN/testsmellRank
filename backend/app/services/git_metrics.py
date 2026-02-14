# app/services/git_metrics.py

"""
Git-based metrics calculation for test smell prioritization
Calculates Change Proneness (CP) and Fault Proneness (FP) from Git history
Based on research paper methodology
"""

import subprocess
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from scipy.stats import spearmanr
import numpy as np


# =====================================================
# FAULT-FIXING COMMIT IDENTIFICATION
# =====================================================
FAULT_KEYWORDS = [
    'bug', 'fix', 'error', 'defect', 'issue', 'fault', 
    'crash', 'patch', 'repair', 'correct', 'resolve'
]


def is_faulty_commit(commit_message: str) -> bool:
    """Check if a commit message indicates a bug fix"""
    message_lower = commit_message.lower()
    return any(keyword in message_lower for keyword in FAULT_KEYWORDS)


# =====================================================
# GIT HISTORY EXTRACTION
# =====================================================
def extract_git_history(repo_path: Path) -> List[Dict]:
    """
    Extract commit history from a Git repository
    
    Returns list of commits with:
    - hash: commit hash
    - message: commit message
    - timestamp: commit date
    - files_changed: dict of {filename: {'additions': int, 'deletions': int}}
    - is_faulty: whether this is a bug-fix commit
    """
    commits = []
    
    try:
        # Check if it's a git repository
        git_check = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if git_check.returncode != 0:
            print(f"Not a git repository: {repo_path}")
            return []
        
        # Get all commits with numstat (shows file changes)
        result = subprocess.run(
            ['git', 'log', '--numstat', '--format=%H|%s|%ai', '--no-merges'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Git log failed: {result.stderr}")
            return []
        
        # Parse the output
        lines = result.stdout.strip().split('\n')
        current_commit = None
        
        for line in lines:
            if '|' in line and not line.startswith('\t'):
                # This is a commit header line
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split('|')
                if len(parts) >= 3:
                    commit_hash = parts[0]
                    message = parts[1]
                    timestamp = parts[2]
                    
                    current_commit = {
                        'hash': commit_hash,
                        'message': message,
                        'timestamp': timestamp,
                        'files_changed': {},
                        'is_faulty': is_faulty_commit(message)
                    }
            elif line.strip() and current_commit:
                # This is a file change line (numstat format: additions deletions filename)
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    additions = parts[0]
                    deletions = parts[1]
                    filename = parts[2]
                    
                    # Convert to int, handle binary files (marked as '-')
                    add_count = 0 if additions == '-' else int(additions)
                    del_count = 0 if deletions == '-' else int(deletions)
                    
                    current_commit['files_changed'][filename] = {
                        'additions': add_count,
                        'deletions': del_count
                    }
        
        # Add the last commit
        if current_commit:
            commits.append(current_commit)
        
        print(f"Extracted {len(commits)} commits from {repo_path}")
        
    except Exception as e:
        print(f"Error extracting git history: {e}")
        return []
    
    return commits


# =====================================================
# FILE CLASSIFICATION
# =====================================================
def is_test_file(filename: str) -> bool:
    """Check if a file is a test file"""
    filename_lower = filename.lower()
    return (
        'test_' in filename_lower or 
        '_test.' in filename_lower or
        '/tests/' in filename_lower or
        '\\tests\\' in filename_lower or
        filename_lower.startswith('test')
    )


def is_production_file(filename: str) -> bool:
    """Check if a file is a production Python file"""
    return (
        filename.endswith('.py') and 
        not is_test_file(filename) and
        not filename.endswith('__init__.py')
    )


# =====================================================
# METRIC CALCULATION
# =====================================================
def calculate_file_metrics(commits: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate metrics for each file
    
    Returns dict: {
        filename: {
            'total_changes': int,
            'total_churn': int,
            'faulty_changes': int,
            'faulty_churn': int
        }
    }
    """
    file_metrics = defaultdict(lambda: {
        'total_changes': 0,
        'total_churn': 0,
        'faulty_changes': 0,
        'faulty_churn': 0
    })
    
    for commit in commits:
        is_faulty = commit['is_faulty']
        
        for filename, changes in commit['files_changed'].items():
            additions = changes['additions']
            deletions = changes['deletions']
            churn = additions + deletions
            
            # Update metrics
            file_metrics[filename]['total_changes'] += 1
            file_metrics[filename]['total_churn'] += churn
            
            if is_faulty:
                file_metrics[filename]['faulty_changes'] += 1
                file_metrics[filename]['faulty_churn'] += churn
    
    return dict(file_metrics)


def calculate_smell_metrics(
    smell_instances: List[Dict], 
    commits: List[Dict]
) -> Dict[str, Dict]:
    """
    Calculate CP and FP metrics for each smell type
    
    smell_instances format:
    [
        {
            'type': 'Conditional Test Logic',
            'file': 'tests/test_module.py',
            'line': 45,
            // ... other smell data
        }
    ]
    
    Returns:
    {
        'smell_type': {
            'change_frequency': float,
            'change_extent': float,
            'fault_frequency': float,
            'fault_extent': float,
            'cp_score': float,
            'fp_score': float,
            'prioritization_score': float,
            'test_files': [list of test files with this smell],
            'instance_count': int
        }
    }
    """
    # Group smells by type
    smells_by_type = defaultdict(list)
    for smell in smell_instances:
        smells_by_type[smell['type']].append(smell)
    
    # Calculate file metrics from commits
    file_metrics = calculate_file_metrics(commits)
    
    # Separate production and test files
    prod_files = {f for f in file_metrics.keys() if is_production_file(f)}
    test_files = {f for f in file_metrics.keys() if is_test_file(f)}
    
    # Calculate total commits for normalization
    prod_total_commits = sum(file_metrics[f]['total_changes'] for f in prod_files)
    test_total_commits = sum(file_metrics[f]['total_changes'] for f in test_files)
    
    if prod_total_commits == 0 or test_total_commits == 0:
        print("Warning: No production or test commits found")
        return {}
    
    results = {}
    
    for smell_type, instances in smells_by_type.items():
        # Get test files containing this smell
        smell_test_files = set(inst['file'] for inst in instances)
        
        # Calculate metrics for files with this smell
        prod_changes = 0
        prod_churn = 0
        prod_faulty_changes = 0
        prod_faulty_churn = 0
        
        test_changes = 0
        test_churn = 0
        test_faulty_changes = 0
        test_faulty_churn = 0
        
        # Aggregate metrics for test files with this smell
        for test_file in smell_test_files:
            if test_file in file_metrics:
                metrics = file_metrics[test_file]
                test_changes += metrics['total_changes']
                test_churn += metrics['total_churn']
                test_faulty_changes += metrics['faulty_changes']
                test_faulty_churn += metrics['faulty_churn']
        
        # For production files, use all production files (simplified approach)
        # In a more sophisticated version, you'd map test files to their tested modules
        for prod_file in prod_files:
            metrics = file_metrics[prod_file]
            prod_changes += metrics['total_changes']
            prod_churn += metrics['total_churn']
            prod_faulty_changes += metrics['faulty_changes']
            prod_faulty_churn += metrics['faulty_churn']
        
        # Calculate normalized metrics
        change_frequency = (
            (prod_changes / prod_total_commits if prod_total_commits > 0 else 0) +
            (test_changes / test_total_commits if test_total_commits > 0 else 0)
        )
        
        change_extent = (
            (prod_churn / prod_total_commits if prod_total_commits > 0 else 0) +
            (test_churn / test_total_commits if test_total_commits > 0 else 0)
        )
        
        fault_frequency = (
            (prod_faulty_changes / prod_total_commits if prod_total_commits > 0 else 0) +
            (test_faulty_changes / test_total_commits if test_total_commits > 0 else 0)
        )
        
        fault_extent = (
            (prod_faulty_churn / prod_total_commits if prod_total_commits > 0 else 0) +
            (test_faulty_churn / test_total_commits if test_total_commits > 0 else 0)
        )
        
        # For now, use simple sum for CP and FP
        # In full implementation, would calculate Spearman correlation
        cp_score = change_frequency + change_extent
        fp_score = fault_frequency + fault_extent
        prioritization_score = (cp_score + fp_score) / 2
        
        results[smell_type] = {
            'change_frequency': round(change_frequency, 4),
            'change_extent': round(change_extent, 4),
            'fault_frequency': round(fault_frequency, 4),
            'fault_extent': round(fault_extent, 4),
            'cp_score': round(cp_score, 4),
            'fp_score': round(fp_score, 4),
            'prioritization_score': round(prioritization_score, 4),
            'test_files': list(smell_test_files),
            'instance_count': len(instances)
        }
    
    return results


# =====================================================
# ADVANCED CORRELATION-BASED CALCULATION
# =====================================================
def calculate_correlations(
    smell_instances: List[Dict],
    file_metrics: Dict[str, Dict],
    all_test_files: List[str]
) -> Dict[str, Dict]:
    """
    Calculate Spearman correlation between smell presence and metrics
    
    For each smell type, creates binary arrays and calculates correlation
    """
    smells_by_type = defaultdict(list)
    for smell in smell_instances:
        smells_by_type[smell['type']].append(smell)
    
    results = {}
    
    for smell_type, instances in smells_by_type.items():
        smell_files = set(inst['file'] for inst in instances)
        
        # Create binary presence array
        smell_presence = []
        change_freq_values = []
        change_extent_values = []
        fault_freq_values = []
        fault_extent_values = []
        
        for test_file in all_test_files:
            # Smell presence (1 if file has this smell, 0 otherwise)
            smell_presence.append(1 if test_file in smell_files else 0)
            
            # Get metrics for this file
            if test_file in file_metrics:
                metrics = file_metrics[test_file]
                change_freq_values.append(metrics['total_changes'])
                change_extent_values.append(metrics['total_churn'])
                fault_freq_values.append(metrics['faulty_changes'])
                fault_extent_values.append(metrics['faulty_churn'])
            else:
                change_freq_values.append(0)
                change_extent_values.append(0)
                fault_freq_values.append(0)
                fault_extent_values.append(0)
        
        # Calculate Spearman correlations
        try:
            # Check if we have variance (not all zeros/ones)
            if len(set(smell_presence)) > 1 and sum(change_freq_values) > 0:
                rho_cf, p_cf = spearmanr(smell_presence, change_freq_values)
                rho_ce, p_ce = spearmanr(smell_presence, change_extent_values)
                rho_ff, p_ff = spearmanr(smell_presence, fault_freq_values)
                rho_fe, p_fe = spearmanr(smell_presence, fault_extent_values)
                
                cp_score = rho_cf + rho_ce
                fp_score = rho_ff + rho_fe
                ps = (cp_score + fp_score) / 2
                
                results[smell_type] = {
                    'change_frequency_rho': round(rho_cf, 4),
                    'change_extent_rho': round(rho_ce, 4),
                    'fault_frequency_rho': round(rho_ff, 4),
                    'fault_extent_rho': round(rho_fe, 4),
                    'cp_score': round(cp_score, 4),
                    'fp_score': round(fp_score, 4),
                    'prioritization_score': round(ps, 4),
                    'p_values': {
                        'cf': round(p_cf, 4),
                        'ce': round(p_ce, 4),
                        'ff': round(p_ff, 4),
                        'fe': round(p_fe, 4)
                    },
                    'instance_count': len(instances)
                }
            else:
                # Not enough variance for correlation
                results[smell_type] = {
                    'error': 'Insufficient variance for correlation',
                    'instance_count': len(instances)
                }
        except Exception as e:
            results[smell_type] = {
                'error': str(e),
                'instance_count': len(instances)
            }
    
    return results


# =====================================================
# MAIN ANALYSIS FUNCTION
# =====================================================
def analyze_project_with_git(
    project_path: Path,
    smell_instances: List[Dict]
) -> Dict:
    """
    Main function to analyze a project and calculate CP/FP metrics
    
    Args:
        project_path: Path to the git repository
        smell_instances: List of detected smell instances
    
    Returns:
        Dict with metrics for each smell type
    """
    print(f"\n🔍 Analyzing Git history for: {project_path}")
    
    # Extract git history
    commits = extract_git_history(project_path)
    
    if not commits:
        return {
            'error': 'No git history found or not a git repository',
            'metrics': {}
        }
    
    print(f"📊 Analyzing {len(commits)} commits...")
    
    # Calculate simple metrics
    metrics = calculate_smell_metrics(smell_instances, commits)
    
    # Calculate statistics
    faulty_commits = [c for c in commits if c['is_faulty']]
    total_files = len(set(f for c in commits for f in c['files_changed'].keys()))
    test_files_count = len([f for c in commits for f in c['files_changed'].keys() if is_test_file(f)])
    
    return {
        'metrics': metrics,
        'statistics': {
            'total_commits': len(commits),
            'faulty_commits': len(faulty_commits),
            'fault_percentage': round(len(faulty_commits) / len(commits) * 100, 2) if commits else 0,
            'total_files': total_files,
            'test_files': test_files_count
        }
    }
