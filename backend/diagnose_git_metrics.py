# Quick diagnostic script to check git history vs detected smells
# Run this in the uploaded project directory

import subprocess
import sys
from pathlib import Path

def check_git_status(project_path):
    """Check if test files with smells are in git history"""
    
    print("=" * 70)
    print("GIT METRICS DIAGNOSTIC")
    print("=" * 70)
    
    # Test files where smells were detected
    smell_files = [
        "test file/tests/test_all_11_smells.py",
        "test file/tests/test_all_21_smells.py",
        "test file/tests/test_arithmetic.py",
        "test file/tests/test_magic.py",
        "test file/tests/test_lazy.py"
    ]
    
    print(f"\nProject path: {project_path}\n")
    
    # Check if it's a git repo
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("❌ Not a git repository!")
            return
        print("✅ Valid git repository found\n")
    except Exception as e:
        print(f"❌ Git not accessible: {e}")
        return
    
    # Get all files in git history
    try:
        result = subprocess.run(
            ['git', 'log', '--name-only', '--pretty=format:', '--all'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        all_git_files = set(line.strip() for line in result.stdout.split('\n') if line.strip())
        test_files_in_git = [f for f in all_git_files if 'test' in f.lower() and f.endswith('.py')]
        
        print(f"📊 Files in Git history: {len(all_git_files)}")
        print(f"📊 Test files in Git: {len(test_files_in_git)}\n")
        
        print("Test files in Git history:")
        for f in sorted(test_files_in_git)[:20]:  # Show first 20
            print(f"  - {f}")
        if len(test_files_in_git) > 20:
            print(f"  ... and {len(test_files_in_git) - 20} more")
        
        print("\n" + "=" * 70)
        print("CHECKING FILES WITH SMELLS:")
        print("=" * 70)
        
        for smell_file in smell_files:
            # Try different path formats
            variants = [
                smell_file,
                smell_file.replace('/', '\\'),
                smell_file.replace('test file/', ''),
                smell_file.replace('test file\\', ''),
                smell_file.split('/')[-1],  # Just filename
            ]
            
            found = False
            for variant in variants:
                if variant in all_git_files:
                    # Get commit count for this file
                    commit_result = subprocess.run(
                        ['git', 'log', '--oneline', '--', variant],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    commit_count = len([l for l in commit_result.stdout.split('\n') if l.strip()])
                    print(f"✅ {smell_file}")
                    print(f"   Found as: {variant}")
                    print(f"   Commits: {commit_count}")
                    found = True
                    break
            
            if not found:
                print(f"❌ {smell_file}")
                print(f"   NOT FOUND in git history (0 commits)")
        
        print("\n" + "=" * 70)
        print("DIAGNOSIS:")
        print("=" * 70)
        
        smell_files_found = sum(1 for sf in smell_files if any(v in all_git_files for v in [
            sf, sf.replace('/', '\\'), sf.replace('test file/', ''), sf.split('/')[-1]
        ]))
        
        if smell_files_found == 0:
            print("❌ PROBLEM: None of the test files with smells are in git history")
            print("\nThis means:")
            print("  - The test files were added but never committed")
            print("  - OR the files are in a different path in git")
            print("  - OR git was initialized after files were uploaded")
            print("\nSOLUTION:")
            print("  1. Commit the test files: git add tests/ && git commit -m 'Add tests'")
            print("  2. OR use a project with committed test files")
            print("  3. Check if 'test file' folder needs to be removed from paths")
        else:
            print(f"✅ Found {smell_files_found}/{len(smell_files)} smell files in git")
            print("Git metrics should work correctly!")
        
    except Exception as e:
        print(f"❌ Error checking git history: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        # Try to detect project path
        project_path = Path.cwd()
    
    check_git_status(project_path)
