# Quick verification script to test smell detection
from pathlib import Path
from app.services.smell_detection import detect_smells_for_project
import json

# Test on the tests folder
test_dir = Path(__file__).parent.parent / "tests"

if test_dir.exists():
    print(f"Testing smell detection on: {test_dir}")
    result = detect_smells_for_project(test_dir)
    
    print(f"\n{'='*60}")
    print(f"Total Files: {result['total_files']}")
    print(f"Total Smells: {result['total_smells']}")
    print(f"{'='*60}\n")
    
    for detail in result['details']:
        if detail['smell_count'] > 0:
            print(f"\n📄 {detail['file']}")
            print(f"   Smells found: {detail['smell_count']}")
            for smell in detail['smells']:
                print(f"   ⚠️  Line {smell['line']}: {smell['type']} - {smell['message']}")
else:
    print(f"Test directory not found: {test_dir}")
