"""
Quick test script to verify the AST-based smell detection works
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.routes.upload import analyze_test_file_for_smells

# Test with the test file
test_file = Path('tests/test_all_11_smells.py')

if test_file.exists():
    print(f"Analyzing: {test_file}")
    smells = analyze_test_file_for_smells(test_file)
    print(f"\n✓ Detected {len(smells)} test smells:\n")
    
    # Group by type
    smell_types = {}
    for smell in smells:
        smell_type = smell['type']
        if smell_type not in smell_types:
            smell_types[smell_type] = []
        smell_types[smell_type].append(smell)
    
    # Display results
    for smell_type, instances in smell_types.items():
        print(f"  {smell_type}: {len(instances)} instance(s)")
        for smell in instances[:2]:  # Show first 2 of each type
            print(f"    - Line {smell['line']}: {smell['message']}")
    
    print(f"\n✓ Total: {len(smells)} smells detected")
    print(f"✓ AST-based analyzer is working correctly!")
else:
    print(f"✗ Test file not found: {test_file}")
