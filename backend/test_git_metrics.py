# Test script for Git metrics functionality
# Run this from the backend directory

from pathlib import Path
from app.services.git_metrics import (
    extract_git_history,
    is_faulty_commit,
    calculate_file_metrics,
    analyze_project_with_git
)

# Test 1: Faulty commit identification
print("=" * 60)
print("TEST 1: Faulty Commit Identification")
print("=" * 60)

test_messages = [
    ("fix: resolve test flakiness", True),
    ("bug: correct assertion logic", True),
    ("refactor: improve code quality", False),
    ("feature: add new test cases", False),
    ("patch: security vulnerability", True),
    ("error handling improvement", True)
]

for message, expected in test_messages:
    result = is_faulty_commit(message)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{message}' -> {result} (expected: {expected})")

# Test 2: Git history extraction
print("\n" + "=" * 60)
print("TEST 2: Git History Extraction")
print("=" * 60)

# Test on the current repository
project_path = Path(__file__).parent.parent
print(f"Repository: {project_path}")

commits = extract_git_history(project_path)
if commits:
    print(f"✓ Successfully extracted {len(commits)} commits")
    print(f"  - Faulty commits: {sum(1 for c in commits if c['is_faulty'])}")
    print(f"  - Non-faulty commits: {sum(1 for c in commits if not c['is_faulty'])}")
    
    # Show first commit as example
    if len(commits) > 0:
        first_commit = commits[0]
        print(f"\n  Example commit:")
        print(f"  - Hash: {first_commit['hash'][:10]}...")
        print(f"  - Message: {first_commit['message'][:50]}...")
        print(f"  - Faulty: {first_commit['is_faulty']}")
        print(f"  - Files changed: {len(first_commit['files_changed'])}")
else:
    print("✗ No commits found or not a git repository")

# Test 3: File metrics calculation
print("\n" + "=" * 60)
print("TEST 3: File Metrics Calculation")
print("=" * 60)

if commits:
    file_metrics = calculate_file_metrics(commits)
    
    # Show metrics for test files
    test_file_metrics = {k: v for k, v in file_metrics.items() 
                         if 'test' in k.lower()}
    
    print(f"✓ Calculated metrics for {len(file_metrics)} files")
    print(f"  - Test files: {len(test_file_metrics)}")
    
    if test_file_metrics:
        print(f"\n  Example test file metrics:")
        example_file = list(test_file_metrics.items())[0]
        print(f"  File: {example_file[0]}")
        print(f"  - Total changes: {example_file[1]['total_changes']}")
        print(f"  - Total churn: {example_file[1]['total_churn']}")
        print(f"  - Faulty changes: {example_file[1]['faulty_changes']}")
        print(f"  - Faulty churn: {example_file[1]['faulty_churn']}")

# Test 4: Full analysis with mock smell data
print("\n" + "=" * 60)
print("TEST 4: Full Analysis with Mock Smell Data")
print("=" * 60)

# Create mock smell instances
mock_smells = [
    {
        'type': 'Conditional Test Logic',
        'file': 'tests/test_example.py',
        'line': 45,
        'message': 'Test contains conditional logic'
    },
    {
        'type': 'Assertion Roulette',
        'file': 'tests/test_example.py',
        'line': 52,
        'message': 'Multiple assertions without messages'
    },
    {
        'type': 'Conditional Test Logic',
        'file': 'tests/test_another.py',
        'line': 30,
        'message': 'Test contains if statement'
    }
]

if commits:
    result = analyze_project_with_git(project_path, mock_smells)
    
    if 'error' not in result:
        print("✓ Successfully calculated prioritization metrics")
        print(f"\n  Statistics:")
        stats = result['statistics']
        print(f"  - Total commits: {stats['total_commits']}")
        print(f"  - Faulty commits: {stats['faulty_commits']}")
        print(f"  - Fault percentage: {stats['fault_percentage']}%")
        
        if result['metrics']:
            print(f"\n  Smell Prioritization:")
            for smell_type, metrics in result['metrics'].items():
                print(f"\n  {smell_type}:")
                print(f"    - Instances: {metrics['instance_count']}")
                print(f"    - CP Score: {metrics['cp_score']}")
                print(f"    - FP Score: {metrics['fp_score']}")
                print(f"    - Priority Score: {metrics['prioritization_score']}")
    else:
        print(f"✗ Analysis failed: {result['error']}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
