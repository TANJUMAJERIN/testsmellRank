# Script to add commit history for CP/FP score generation
# Run this from: i:\Desktop\Tanjuma_BS\Test-smell-rank\testsmellRank
# Assumes: Git is already initialized and test files are already committed

Write-Host "`n📚 Adding commit history to existing repository..." -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

# Check current status
Write-Host "`n📊 Current Status:" -ForegroundColor Cyan
$currentCommits = (git rev-list --count HEAD 2>$null)
if ($currentCommits) {
    Write-Host "   ✅ Existing commits: $currentCommits" -ForegroundColor Green
} else {
    Write-Host "   ❌ No commits found! Please commit your test files first." -ForegroundColor Red
    Write-Host "   Run: git add tests/ && git commit -m 'Initial commit'" -ForegroundColor Yellow
    exit 1
}

# Create bug-fix commits
Write-Host "`n🐛 Creating bug-fix commits (for FP scores)..." -ForegroundColor Cyan

Write-Host "   1. Bug fix in conditional test..." -ForegroundColor Gray
Add-Content -Path "tests\test_conditional.py" -Value "`n# Fix: Improved condition handling"
git add tests\test_conditional.py
git commit -m "fix: Improve conditional test logic" --allow-empty-message 2>$null

Write-Host "   2. Bug fix in exception test..." -ForegroundColor Gray
Add-Content -Path "tests\test_exception.py" -Value "`n# Bug: Fixed exception handling"
git add tests\test_exception.py
git commit -m "bug: Fix exception handling in tests" --allow-empty-message 2>$null

Write-Host "   3. Error fix in magic number test..." -ForegroundColor Gray
Add-Content -Path "tests\test_magic.py" -Value "`n# Error fix: Corrected magic number"
git add tests\test_magic.py
git commit -m "error: Correct magic number usage" --allow-empty-message 2>$null

Write-Host "   4. Defect fix in lazy test..." -ForegroundColor Gray
Add-Content -Path "tests\test_lazy.py" -Value "`n# Defect: Fixed lazy evaluation"
git add tests\test_lazy.py
git commit -m "defect: Fix lazy test evaluation" --allow-empty-message 2>$null

Write-Host "   5. Issue fix in smell test..." -ForegroundColor Gray
Add-Content -Path "tests\test_all_11_smells.py" -Value "`n# Issue #42: Fixed assertions"
git add tests\test_all_11_smells.py
git commit -m "issue: Fix assertion messages (closes #42)" --allow-empty-message 2>$null

Write-Host "   6. Patch for comprehensive test..." -ForegroundColor Gray
Add-Content -Path "tests\test_all_21_smells.py" -Value "`n# Patch: Updated test logic"
git add tests\test_all_21_smells.py
git commit -m "patch: Update comprehensive test logic" --allow-empty-message 2>$null

Write-Host "   7. Fault fix in slow test..." -ForegroundColor Gray
Add-Content -Path "tests\test_slow.py" -Value "`n# Fault: Optimized performance"
git add tests\test_slow.py
git commit -m "fault: Optimize slow test performance" --allow-empty-message 2>$null

# Create some regular commits (for CP scores)
Write-Host "`n📝 Creating regular commits (for CP scores)..." -ForegroundColor Cyan

Write-Host "   1. Refactor arithmetic test..." -ForegroundColor Gray
Add-Content -Path "tests\test_arithmetic.py" -Value "`n# Refactored test structure"
git add tests\test_arithmetic.py
git commit -m "refactor: Improve arithmetic test structure" --allow-empty-message 2>$null

Write-Host "   2. Update duplicate test..." -ForegroundColor Gray
Add-Content -Path "tests\test_duplication.py" -Value "`n# Updated duplicates"
git add tests\test_duplication.py
git commit -m "chore: Update duplication tests" --allow-empty-message 2>$null

Write-Host "   3. Enhance verbose test..." -ForegroundColor Gray
Add-Content -Path "tests\test_verbose.py" -Value "`n# Enhanced verbosity"
git add tests\test_verbose.py
git commit -m "feat: Add more verbose test cases" --allow-empty-message 2>$null

# Verify results
Write-Host "`n✅ Commit history created!" -ForegroundColor Green

Write-Host "`n📊 Final Statistics:" -ForegroundColor Cyan
$totalCommits = (git rev-list --count HEAD)
$faultyCommitsRaw = git log --oneline --all --grep="fix\|bug\|error\|defect\|issue\|patch\|fault"
$faultyCommits = ($faultyCommitsRaw | Measure-Object).Count
$faultRate = if ($totalCommits -gt 0) { ($faultyCommits / $totalCommits * 100).ToString('F1') } else { "0.0" }

Write-Host "   Total commits: $totalCommits" -ForegroundColor White
Write-Host "   Faulty commits: $faultyCommits" -ForegroundColor White
Write-Host "   Fault rate: $faultRate%" -ForegroundColor White

# Show recent commits
Write-Host "`n📜 Recent commits:" -ForegroundColor Cyan
git log --oneline -10

# Show test files in history
Write-Host "`n📝 Test files with commits:" -ForegroundColor Cyan
$testFilesInGit = git log --name-only --pretty=format: --all | Where-Object { $_ -like "*test*.py" } | Sort-Object -Unique
$testFileCount = ($testFilesInGit | Measure-Object).Count
Write-Host "   Found: $testFileCount test files" -ForegroundColor White

# Create ZIP for upload
Write-Host "`n📦 Creating ZIP file for upload..." -ForegroundColor Cyan
$zipPath = "..\testsmellRank-with-history.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# ZIP the entire project INCLUDING .git folder
Compress-Archive -Path ".\*" -DestinationPath $zipPath -Force

$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "✅ ZIP created successfully!" -ForegroundColor Green
Write-Host "   Path: $zipPath" -ForegroundColor White
Write-Host "   Size: $($zipSize.ToString('F2')) MB" -ForegroundColor White

# Final instructions
Write-Host "`n" + ("=" * 70) -ForegroundColor Yellow
Write-Host "🎉 READY TO UPLOAD!" -ForegroundColor Green -BackgroundColor Black
Write-Host ("=" * 70) -ForegroundColor Yellow

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Added 10 new commits" -ForegroundColor White
Write-Host "   ✅ Created $faultyCommits bug-fix commits" -ForegroundColor White
Write-Host "   ✅ Total commits now: $totalCommits" -ForegroundColor White
Write-Host "   ✅ ZIP file includes .git folder" -ForegroundColor White

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Upload: " -NoNewline -ForegroundColor White
Write-Host "testsmellRank-with-history.zip" -ForegroundColor Yellow
Write-Host "   2. View results in your application" -ForegroundColor White
Write-Host "   3. Check the Git Metrics section" -ForegroundColor White

Write-Host "`n💡 Expected Results:" -ForegroundColor Cyan
Write-Host "   ✓ Total Commits: $totalCommits" -ForegroundColor Green
Write-Host "   ✓ Faulty Commits: $faultyCommits" -ForegroundColor Green
Write-Host "   ✓ Fault Rate: $faultRate%" -ForegroundColor Green
Write-Host "   ✓ CP Scores: NON-ZERO (typically 0.5 - 3.0)" -ForegroundColor Green
Write-Host "   ✓ FP Scores: NON-ZERO (typically 0.2 - 1.5)" -ForegroundColor Green
Write-Host "   ✓ Different scores per smell type" -ForegroundColor Green

Write-Host "`n✨ Tip: Smell types in files with more commits will rank higher!" -ForegroundColor Gray
Write-Host "`n"
