"""
File-wise Test Smell Detection Summary
Analyzes each test file and lists detected smells with line numbers
"""

import subprocess
import sys
import re
from collections import defaultdict

def analyze_test_smells_by_file():
    """Run pytest-smell and organize results by file"""
    
    print("="*80)
    print("FILE-WISE TEST SMELL DETECTION SUMMARY")
    print("="*80)
    print()
    
    # Run pytest-smell with verbose output
    result = subprocess.run(
        [sys.executable, '-m', 'pytest_smell', 
         '--tests_path', 'tests',
         '--verbose'],
        capture_output=True,
        text=True
    )
    
    output = result.stdout + result.stderr
    
    # Parse output by file
    file_smells = defaultdict(list)
    
    lines = output.split('\n')
    for line in lines:
        if 'suffers from' in line:
            # Extract file name, line number, and smell type
            # Format: Test <test_name> located at File "path/file.py", line <num> suffers from "<smell>"
            
            file_match = re.search(r'File "([^"]+)", line (\d+)', line)
            smell_match = re.search(r'suffers from "([^"]+)"', line)
            test_match = re.search(r'Test (\S+)', line)
            
            if file_match and smell_match:
                file_path = file_match.group(1)
                line_num = file_match.group(2)
                smell_type = smell_match.group(1)
                test_name = test_match.group(1) if test_match else "unknown"
                
                # Extract just the filename
                filename = file_path.split('/')[-1].split('\\')[-1]
                
                file_smells[filename].append({
                    'test': test_name,
                    'line': line_num,
                    'smell': smell_type
                })
    
    # Display results organized by file
    for filename in sorted(file_smells.keys()):
        print(f"\n{'='*80}")
        print(f"FILE: {filename}")
        print(f"{'='*80}")
        
        # Group smells by type for this file
        smell_groups = defaultdict(list)
        for item in file_smells[filename]:
            smell_groups[item['smell']].append(f"line {item['line']} ({item['test']})")
        
        # Display each smell type
        for smell_type in sorted(smell_groups.keys()):
            locations = ', '.join(smell_groups[smell_type])
            print(f"  • {smell_type}: {locations}")
        
        # Show total count
        total = len(file_smells[filename])
        print(f"\n  Total smells in this file: {total}")
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total files analyzed: {len(file_smells)}")
    
    total_smells = sum(len(smells) for smells in file_smells.values())
    print(f"Total smells detected: {total_smells}")
    
    # Count by smell type across all files
    all_smell_types = defaultdict(int)
    for smells in file_smells.values():
        for smell in smells:
            all_smell_types[smell['smell']] += 1
    
    print(f"\nSmell type breakdown:")
    for smell_type in sorted(all_smell_types.keys()):
        print(f"  • {smell_type}: {all_smell_types[smell_type]}")
    
    print()

if __name__ == "__main__":
    analyze_test_smells_by_file()
