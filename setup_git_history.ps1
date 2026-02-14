# Script to initialize git and create commit history for test files
# Run this from: i:\Desktop\Tanjuma_BS\Test-smell-rank\testsmellRank

# Step 1: Check if git is initialized
Write-Host "`n🔍 Checking git status..." -ForegroundColor Cyan
$gitExists = Test-Path ".git"

if (-not $gitExists) {
    Write-Host "❌ Git repository not initialized" -ForegroundColor Yellow
    Write-Host "📦 Initializing git repository..." -ForegroundColor Cyan
    git init
    git config user.name "Test Smell Developer"
    git config user.email "developer@testsmell.com"
    Write-Host "✅ Git initialized!" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository exists" -ForegroundColor Green
}

# Step 2: Add test files
Write-Host "`n📝 Adding test files to git..." -ForegroundColor Cyan
git add tests/

# Step 3: Check what's being added
Write-Host "`n📊 Files to be committed:" -ForegroundColor Cyan
git status --short

$testFileCount = (git diff --cached --name-only | Where-Object { $_ -like "*test*.py" } | Measure-Object).Count
Write-Host "   Test files: $testFileCount" -ForegroundColor White

# Step 4: Create initial commit
Write-Host "`n💾 Creating initial commit..." -ForegroundColor Cyan
git commit -m "Initial commit: Add test suite with test smells"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Initial commit created!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Commit failed or nothing to commit" -ForegroundColor Yellow
}

# Step 5: Create additional commits to build history
Write-Host "`n📚 Creating commit history (for meaningful CP/FP scores)..." -ForegroundColor Cyan

# Commit 2: Bug fix
Write-Host "   Creating bug fix commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_conditional.py" -Value "`n# Bug fix: improved condition"
git commit -am "fix: Improve conditional test logic"

# Commit 3: Another bug fix
Write-Host "   Creating another bug fix commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_exception.py" -Value "`n# Fixed exception handling"
git commit -am "bug: Fix exception handling in tests"

# Commit 4: Regular update
Write-Host "   Creating refactor commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_arithmetic.py" -Value "`n# Refactor arithmetic tests"
git commit -am "refactor: Update arithmetic test structure"

# Commit 5: Error fix
Write-Host "   Creating error fix commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_magic.py" -Value "`n# Error: Fixed magic number"
git commit -am "error: Correct magic number assertions"

# Commit 6: Feature update
Write-Host "   Creating feature commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_lazy.py" -Value "`n# Added new test case"
git commit -am "feat: Add new lazy test case"

# Commit 7: Issue fix
Write-Host "   Creating issue fix commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_all_11_smells.py" -Value "`n# Issue #123: Fixed assertion"
git commit -am "issue: Fix assertion messages"

# Commit 8: Defect fix
Write-Host "   Creating defect fix commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_all_21_smells.py" -Value "`n# Defect: Corrected test logic"
git commit -am "defect: Correct test assertions"

# Commit 9: Patch
Write-Host "   Creating patch commit..." -ForegroundColor Gray
Add-Content -Path "tests\test_slow.py" -Value "`n# Patched slow test"
git commit -am "patch: Optimize slow test performance"

# Step 6: Verify commits
Write-Host "`n✅ Commit history created!" -ForegroundColor Green
Write-Host "`n📊 Git Statistics:" -ForegroundColor Cyan

$totalCommits = (git rev-list --count HEAD)
$faultyCommitsRaw = git log --oneline --all --grep="fix\|bug\|error\|defect\|issue\|patch"
$faultyCommits = ($faultyCommitsRaw | Measure-Object).Count

Write-Host "   Total commits: $totalCommits" -ForegroundColor White
Write-Host "   Faulty commits: $faultyCommits" -ForegroundColor White
Write-Host "   Fault rate: $(($faultyCommits / $totalCommits * 100).ToString('F1'))%" -ForegroundColor White

# Step 7: Show test files in history
Write-Host "`n📝 Test files in commit history:" -ForegroundColor Cyan
$testFilesInGit = git log --name-only --pretty=format: --all | Where-Object { $_ -like "*test*.py" } | Sort-Object -Unique
$testFilesInGit | ForEach-Object { Write-Host "   ✓ $_" -ForegroundColor Green }

# Step 8: Create ZIP for upload
Write-Host "`n📦 Creating ZIP file for upload..." -ForegroundColor Cyan
$zipPath = "..\testsmellRank-with-history.zip"

# Remove old ZIP if exists
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Create ZIP including .git folder (important!)
Compress-Archive -Path ".\*" -DestinationPath $zipPath -Force

$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "✅ ZIP created: $zipPath" -ForegroundColor Green
Write-Host "   Size: $($zipSize.ToString('F2')) MB" -ForegroundColor White

# Final instructions
Write-Host "`n" + ("=" * 70) -ForegroundColor Yellow
Write-Host "🎉 READY TO TEST!" -ForegroundColor Green -BackgroundColor Black
Write-Host ("=" * 70) -ForegroundColor Yellow

Write-Host "`n📋 What was done:" -ForegroundColor Cyan
Write-Host "   ✅ Git repository initialized (if needed)" -ForegroundColor White
Write-Host "   ✅ Test files committed to git" -ForegroundColor White
Write-Host "   ✅ Created $faultyCommits bug-fix commits" -ForegroundColor White
Write-Host "   ✅ Created $totalCommits total commits" -ForegroundColor White
Write-Host "   ✅ ZIP file created with git history" -ForegroundColor White

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Upload this ZIP: " -NoNewline -ForegroundColor White
Write-Host "$zipPath" -ForegroundColor Yellow
Write-Host "   2. View results in your application" -ForegroundColor White
Write-Host "   3. You should now see NON-ZERO CP and FP scores! 🎯" -ForegroundColor White

Write-Host "`n💡 Expected Results:" -ForegroundColor Cyan
Write-Host "   - Total Commits: ~$totalCommits" -ForegroundColor White
Write-Host "   - Faulty Commits: ~$faultyCommits" -ForegroundColor White
Write-Host "   - CP Scores: 0.5 - 2.0 range" -ForegroundColor White
Write-Host "   - FP Scores: 0.2 - 1.0 range" -ForegroundColor White
Write-Host "   - Different scores per smell type ✓" -ForegroundColor White

Write-Host "`n"
