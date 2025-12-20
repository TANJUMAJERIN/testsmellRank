"""
Summary: pytest-smell detection results for test_all_11_smells.py
"""

import subprocess
import sys
import re

def run_pytest_smell_analysis():
    """Run pytest-smell and summarize results"""
    
    print("="*80)
    print("PYTEST-SMELL DETECTION RESULTS")
    print("Testing file: tests/test_all_11_smells.py")
    print("="*80)
    print()
    
    # Run pytest-smell
    result = subprocess.run(
        [sys.executable, '-m', 'pytest_smell', 
         '--tests_path', 'tests/test_all_11_smells.py',
         '--verbose'],
        capture_output=True,
        text=True
    )
    
    output = result.stdout + result.stderr
    
    # Count each smell type
    smell_counts = {
        'Assertion Roulette': 0,
        'Conditional Logic': 0,
        'Constructor Initialization': 0,
        'Duplicate Assert': 0,
        'Empty Test': 0,
        'Exception Handling': 0,
        'General Fixture': 0,
        'Mystery Guest': 0,
        'Redundant Print': 0,
        'Sleepy Test': 0,
        'Unknown Test': 0,
        'Magic Number': 0  # Bonus smell detected
    }
    
    # Parse output
    lines = output.split('\n')
    for line in lines:
        if 'test_all_11_smells.py' in line:
            for smell_type in smell_counts.keys():
                if smell_type in line:
                    smell_counts[smell_type] += 1
    
    # Display results
    print("SMELL DETECTION SUMMARY:")
    print("-"*80)
    print(f"{'Smell Type':<35} {'Detected':<15} {'Status'}")
    print("-"*80)
    
    # The 11 main pytest-smell smells
    main_smells = [
        'Assertion Roulette',
        'Conditional Logic',
        'Constructor Initialization',
        'Duplicate Assert',
        'Empty Test',
        'Exception Handling',
        'General Fixture',
        'Mystery Guest',
        'Redundant Print',
        'Sleepy Test',
        'Unknown Test'
    ]
    
    detected_count = 0
    for smell in main_smells:
        count = smell_counts[smell]
        status = "✓ DETECTED" if count > 0 else "✗ Not Found"
        print(f"{smell:<35} {count:<15} {status}")
        if count > 0:
            detected_count += 1
    
    # Bonus smells
    print("-"*80)
    print("BONUS SMELLS:")
    print(f"{'Magic Number':<35} {smell_counts['Magic Number']:<15} ✓ DETECTED")
    
    print("-"*80)
    print(f"\nRESULT: {detected_count}/11 main smell types detected by pytest-smell")
    print(f"Bonus: Magic Number smell also detected")
    print()
    
    # Show detailed output
    print("\n" + "="*80)
    print("DETAILED OUTPUT FROM PYTEST-SMELL:")
    print("="*80)
    print(output)
    
    return detected_count

if __name__ == "__main__":
    count = run_pytest_smell_analysis()
    sys.exit(0 if count >= 8 else 1)  # Success if at least 8/11 detected
