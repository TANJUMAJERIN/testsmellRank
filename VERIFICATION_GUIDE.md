# Git Metrics Verification Guide

## What Was Wrong

The original implementation had a **critical bug** where:

- ALL production files were added to EVERY smell type
- This caused all smell types to have identical CP/FP scores
- The scores were artificially inflated by including all production files

## The Fix

✅ **Changed calculation to use ONLY test file metrics**

- Each smell type now gets metrics only from test files containing that smell
- Scores are now unique per smell type
- Values are properly normalized

## How to Verify the Results

### Step 1: Check Your Project Structure

First, verify your uploaded project is a Git repository:

```powershell
cd backend/uploaded_projects/user_XXXXX/your-project-name
git log --oneline -10
```

If you see commit history, ✅ it's a valid Git repo.
If you see "not a git repository", ❌ you need to initialize git.

### Step 2: Check Test Files in Git History

See which test files have been committed:

```powershell
git log --name-only --pretty=format: -- "*test*.py" | sort | uniq
```

This shows all test files that have been modified in commits.

### Step 3: Check Faulty Commits

See which commits are identified as bug fixes:

```powershell
git log --oneline --all --grep="fix\|bug\|error\|defect\|issue\|fault\|crash\|patch"
```

Expected result: You should see commits with fix/bug keywords.

### Step 4: Run Test Script

From the backend directory:

```powershell
python test_git_metrics.py
```

Expected output:

```
✓ Faulty commit identification tests pass (6/6)
✓ Git history extracted with N commits
✓ File metrics calculated
✓ Prioritization metrics computed
```

### Step 5: Restart Backend Server

```powershell
# Stop the current server (Ctrl+C)
python main.py
```

### Step 6: Re-upload Project and Check Results

Upload your project again and check:

1. **Different scores per smell type**
   - Each smell should have unique CP and FP scores
   - Not all the same value

2. **Reasonable CP scores (0-5 range typically)**
   - Change Frequency: 0-1 (percentage of commits)
   - Change Extent: 0-10 (normalized code churn)
   - CP Score = sum of above

3. **FP Score may be 0 or small**
   - This is OK if test files weren't changed in bug-fix commits
   - This is common in small projects or recent test additions

4. **Priority Score ranking makes sense**
   - Smells in frequently changed files should rank higher
   - Smells in rarely touched files should rank lower

## Expected Results

### ✅ CORRECT Results Look Like:

```
Smell Type                  | CP Score | FP Score | Priority
----------------------------|----------|----------|----------
Conditional Test Logic      | 2.5432   | 0.3210   | 1.4321
Assertion Roulette         | 1.8765   | 0.0000   | 0.9383
Suboptimal Assert          | 0.9876   | 0.1234   | 0.5555
Magic Number Test          | 0.4567   | 0.0000   | 0.2284
```

**Characteristics:**

- ✅ Different scores for each smell type
- ✅ CP scores typically 0-5
- ✅ FP scores typically 0-2 (may be 0)
- ✅ Varied priority scores

### ❌ INCORRECT Results Look Like:

```
Smell Type                  | CP Score | FP Score | Priority
----------------------------|----------|----------|----------
Conditional Test Logic      | 134.129  | 0        | 67.0645
Assertion Roulette         | 134.129  | 0        | 67.0645
Suboptimal Assert          | 134.129  | 0        | 67.0645
Magic Number Test          | 134.129  | 0        | 67.0645
```

**Problems:**

- ❌ Identical scores for all smell types
- ❌ Unrealistically high CP scores (>100)
- ❌ This indicates the bug is still present

## Understanding the Scores

### Change Frequency (ChgFreq)

```
ChgFreq = Number of commits touching test files with this smell
          ------------------------------------------------
          Total commits touching test files
```

Example: If 5 out of 20 test file commits touched files with "Magic Number Test", ChgFreq = 0.25

### Change Extent (ChgExt)

```
ChgExt = Total code churn (additions + deletions) in test files with this smell
         --------------------------------------------------------------
         Total commits touching test files
```

Example: If test files with this smell had 150 lines changed across 20 total commits, ChgExt = 7.5

### Fault Frequency (FaultFreq)

```
FaultFreq = Number of BUG-FIX commits touching test files with this smell
            -----------------------------------------------------------
            Total commits touching test files
```

Example: If 2 out of 20 test file commits were bug fixes, FaultFreq = 0.10

### Fault Extent (FaultExt)

```
FaultExt = Code churn in BUG-FIX commits for test files with this smell
           ----------------------------------------------------------
           Total commits touching test files
```

## Debugging Tips

### If FP Score is 0 for Everything

This is **NORMAL** if:

- ✅ Test files weren't changed in bug-fix commits
- ✅ No commits have bug-fix keywords
- ✅ Test files are newly added (no history of bug fixes)

To verify, check for fault-fixing commits:

```powershell
# Check if any commits have bug-fix keywords
git log --oneline --all | findstr /i "fix bug error defect issue fault crash patch"
```

If no results, FP=0 is correct!

### If All Scores Are Still Identical

1. Make sure you restarted the backend server
2. Clear browser cache and refresh
3. Re-upload the project (don't use cached results)
4. Check if the fix was applied:

```powershell
# In backend directory
python -c "from app.services.git_metrics import calculate_smell_metrics; import inspect; print(inspect.getsource(calculate_smell_metrics))" | findstr "prod_file"
```

If you see "prod_file" in the output, the old code is still loaded.

### If Scores Seem Too Low

This is **NORMAL** for:

- ✅ New test files (not much history)
- ✅ Stable test files (few changes)
- ✅ Small projects (few commits)

The ranking is still valid - smells with higher scores are more problematic relative to others.

### If No Git Metrics Appear

Check the backend console for errors:

```
⚠️ Git Metrics Not Available
No git history found or not a git repository
```

Solution:

1. Ensure project is a Git repository
2. Ensure Git is installed: `git --version`
3. Check file permissions

## Manual Calculation Check

You can manually verify one smell type:

1. Pick a smell type (e.g., "Magic Number Test")
2. Note which files have this smell (e.g., `tests/test_example.py`)
3. Count commits touching that file:

```powershell
cd uploaded_projects/user_XXX/project
git log --oneline -- tests/test_example.py | wc -l
```

4. Count total test file commits:

```powershell
git log --oneline -- "*test*.py" | wc -l
```

5. Calculate ChgFreq manually:

```
ChgFreq = commits_for_this_file / total_test_commits
```

6. Compare with displayed value - should be similar!

## Getting Help

If results still don't look right:

1. Run `python test_git_metrics.py` and share the output
2. Share the git log output: `git log --oneline -20`
3. Share the smell detection results structure
4. Check backend console for debug messages starting with 📊

The debug messages show:

- Number of test files found in git history
- Total test file commits
- Per-smell breakdown of calculations
