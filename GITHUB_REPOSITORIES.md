# Recommended GitHub Repositories for Testing Git-Based Test Smell Prioritization

## ✅ Best Candidates

### 1. **Flask** (Web Framework)

- **URL**: https://github.com/pallets/flask
- **Why**: Large test suite, frequent commits, many contributors
- **Test Files**: `tests/` directory with 100+ test files
- **Commits**: 5000+ commits
- **Clone Command**:

```bash
git clone https://github.com/pallets/flask.git --depth 50
```

### 2. **Requests** (HTTP Library)

- **URL**: https://github.com/psf/requests
- **Why**: Well-maintained tests, clear bug fixes in history
- **Test Files**: `tests/` directory with 30+ test files
- **Commits**: 3000+ commits
- **Clone Command**:

```bash
git clone https://github.com/psf/requests.git --depth 50
```

### 3. **httpx** (Async HTTP Client)

- **URL**: https://github.com/encode/httpx
- **Why**: Modern codebase, good test coverage, pytest-based
- **Test Files**: `tests/` directory with 50+ test files
- **Commits**: 2000+ commits
- **Clone Command**:

```bash
git clone https://github.com/encode/httpx.git --depth 50
```

### 4. **Rich** (Terminal Formatting)

- **URL**: https://github.com/Textualize/rich
- **Why**: Active development, clean test structure
- **Test Files**: `tests/` directory with 80+ test files
- **Commits**: 2000+ commits
- **Clone Command**:

```bash
git clone https://github.com/Textualize/rich.git --depth 50
```

### 5. **pytest** (Testing Framework)

- **URL**: https://github.com/pytest-dev/pytest
- **Why**: Testing framework tests itself, lots of test smells to find
- **Test Files**: `testing/` directory with 200+ test files
- **Commits**: 10,000+ commits
- **Clone Command**:

```bash
git clone https://github.com/pytest-dev/pytest.git --depth 50
```

## 📥 Quick Setup Instructions

### Option A: Clone and ZIP (Recommended)

```bash
# 1. Clone a repository (use --depth to limit history)
git clone https://github.com/psf/requests.git --depth 50
cd requests

# 2. Create a ZIP file
# On Windows PowerShell:
Compress-Archive -Path requests -DestinationPath requests.zip

# On Linux/Mac:
zip -r requests.zip requests/
```

### Option B: Download ZIP from GitHub

1. Go to repository URL
2. Click green "Code" button
3. Click "Download ZIP"
4. **Important**: The ZIP won't have git history!
5. Extract, then run:

```bash
cd extracted-folder
git init
git add .
git commit -m "Initial commit"
```

### Option C: Use the Script Below

Save this as `clone_and_prepare.ps1`:

```powershell
# Clone and prepare a repository for testing

param(
    [string]$repo = "https://github.com/psf/requests.git",
    [string]$name = "requests",
    [int]$depth = 50
)

Write-Host "Cloning $repo..." -ForegroundColor Green
git clone $repo --depth $depth

Write-Host "Creating ZIP file..." -ForegroundColor Green
Compress-Archive -Path $name -DestinationPath "$name-test-smell.zip" -Force

Write-Host "✅ Done! Upload: $name-test-smell.zip" -ForegroundColor Green
Write-Host "Test files: $(Get-ChildItem -Path "$name/tests" -Filter "test*.py" -Recurse | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Cyan
```

Run it:

```powershell
.\clone_and_prepare.ps1 -repo "https://github.com/psf/requests.git" -name "requests"
```

## 🎯 Best Choice for Demo

**I recommend starting with `requests`** because:

- ✅ Medium-sized (not too big, not too small)
- ✅ Clean test structure
- ✅ Well-documented bug fixes
- ✅ Uses pytest (similar to your test files)
- ✅ Active maintenance

## 🔍 What to Expect

After uploading a repository like `requests`, you should see:

**Git Metrics:**

- Total Commits: 40-50 (with --depth 50)
- Faulty Commits: 5-10 (depends on recent history)
- Test Files: 30-40

**Prioritization Scores:**

- Different scores per smell type
- CP scores: 0.5 - 5.0 range
- FP scores: 0.1 - 2.0 range
- Meaningful ranking based on file change history

## 📊 Expected Results Example

```
Smell Type                  | CP Score | FP Score | Priority | Rank
----------------------------|----------|----------|----------|------
Assertion Roulette         | 3.2456   | 0.8765   | 2.0611   | #1
Conditional Test Logic     | 2.1234   | 0.5432   | 1.3333   | #2
Magic Number Test          | 1.5678   | 0.2345   | 0.9012   | #3
Suboptimal Assert          | 0.9876   | 0.1234   | 0.5555   | #4
```

## ⚠️ Troubleshooting

### If Still Getting All 0s:

**Check 1**: Verify git history exists

```bash
cd uploaded_repository
git log --oneline -10
```

**Check 2**: Verify test files in history

```bash
git log --name-only -- "*/test*.py" | head -20
```

**Check 3**: Run diagnostic

```bash
python backend/diagnose_git_metrics.py "uploaded_projects/user_XXX/repository_name"
```

### If Clone is Too Large:

Use smaller depth:

```bash
git clone <repo-url> --depth 10
```

Or clone specific directory:

```bash
git clone --depth 10 --filter=blob:none --no-checkout <repo-url>
cd repo
git checkout main -- tests/
```

## 🚀 Alternative: Small Test Repository

If you want a smaller, controlled example:

```bash
# Create a test repository with history
mkdir test-smell-demo
cd test-smell-demo
git init

# Create test file
cat > tests/test_example.py << 'EOF'
def test_addition():
    assert 1 + 1 == True  # Suboptimal Assert
    assert 2 + 2 == 4

def test_conditional():
    if True:  # Conditional Test Logic
        assert True

def test_magic():
    assert 42 == 42  # Magic Number
EOF

git add .
git commit -m "Initial tests"

# Simulate changes
echo "# More tests" >> tests/test_example.py
git add .
git commit -m "fix: Update test assertions"

# Create more commits...
# Then ZIP it
```

## 📝 Quick Start Commands

**For `requests` (Recommended):**

```powershell
# 1. Clone
git clone https://github.com/psf/requests.git --depth 50

# 2. ZIP
Compress-Archive -Path requests -DestinationPath requests.zip

# 3. Upload requests.zip to your application
```

This will give you real, meaningful prioritization scores! 🎯
