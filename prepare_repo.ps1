# PowerShell script to clone and prepare GitHub repositories for test smell analysis
# Usage: .\prepare_repo.ps1 -RepoName requests

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("requests", "flask", "httpx", "rich", "pytest")]
    [string]$RepoName = "requests",
    
    [Parameter(Mandatory=$false)]
    [int]$Depth = 50,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "."
)

# Repository URLs
$repos = @{
    "requests" = "https://github.com/psf/requests.git"
    "flask" = "https://github.com/pallets/flask.git"
    "httpx" = "https://github.com/encode/httpx.git"
    "rich" = "https://github.com/Textualize/rich.git"
    "pytest" = "https://github.com/pytest-dev/pytest.git"
}

$repoUrl = $repos[$RepoName]
$cloneDir = Join-Path $OutputDir $RepoName
$zipFile = Join-Path $OutputDir "$RepoName-test-smell.zip"

Write-Host "`n🚀 Preparing $RepoName for test smell analysis..." -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# Check if git is available
try {
    $gitVersion = git --version
    Write-Host "✅ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found! Please install Git first." -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Remove existing directory if it exists
if (Test-Path $cloneDir) {
    Write-Host "🗑️  Removing existing directory: $cloneDir" -ForegroundColor Yellow
    Remove-Item -Path $cloneDir -Recurse -Force
}

# Remove existing ZIP if it exists
if (Test-Path $zipFile) {
    Write-Host "🗑️  Removing existing ZIP: $zipFile" -ForegroundColor Yellow
    Remove-Item -Path $zipFile -Force
}

# Clone repository
Write-Host "`n📥 Cloning repository (depth: $Depth)..." -ForegroundColor Cyan
Write-Host "   URL: $repoUrl" -ForegroundColor Gray

try {
    git clone $repoUrl --depth $Depth $cloneDir 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Clone successful!" -ForegroundColor Green
    } else {
        throw "Git clone failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "❌ Failed to clone repository: $_" -ForegroundColor Red
    exit 1
}

# Analyze repository
Write-Host "`n📊 Analyzing repository..." -ForegroundColor Cyan

# Count test files
$testFiles = Get-ChildItem -Path $cloneDir -Filter "test*.py" -Recurse -ErrorAction SilentlyContinue
$testFileCount = ($testFiles | Measure-Object).Count

Write-Host "   Test files found: $testFileCount" -ForegroundColor White

# Get commit count
Push-Location $cloneDir
$commitCount = (git rev-list --count HEAD 2>$null)
$faultyCommits = (git log --oneline --all --grep="fix\|bug\|error\|defect" | Measure-Object).Count
Pop-Location

Write-Host "   Total commits: $commitCount" -ForegroundColor White
Write-Host "   Faulty commits: $faultyCommits (estimated)" -ForegroundColor White

# Create ZIP file
Write-Host "`n📦 Creating ZIP file..." -ForegroundColor Cyan

try {
    Compress-Archive -Path $cloneDir -DestinationPath $zipFile -Force
    
    $zipSize = (Get-Item $zipFile).Length / 1MB
    Write-Host "✅ ZIP created: $zipFile" -ForegroundColor Green
    Write-Host "   Size: $($zipSize.ToString('F2')) MB" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to create ZIP: $_" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Gray
Write-Host "✅ READY FOR UPLOAD!" -ForegroundColor Green -BackgroundColor Black
Write-Host ("=" * 70) -ForegroundColor Gray

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "   Repository: $RepoName" -ForegroundColor White
Write-Host "   ZIP File: $zipFile" -ForegroundColor White
Write-Host "   Test Files: $testFileCount" -ForegroundColor White
Write-Host "   Commits: $commitCount" -ForegroundColor White
Write-Host "   Faulty Commits: $faultyCommits" -ForegroundColor White

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open your Test Smell Rank application" -ForegroundColor White
Write-Host "   2. Upload: $zipFile" -ForegroundColor Yellow
Write-Host "   3. View prioritization results with real data!" -ForegroundColor White

Write-Host "`n💡 Tip: Git metrics will show meaningful scores since" -ForegroundColor Gray
Write-Host "   this repository has real commit history!" -ForegroundColor Gray

# Cleanup option
Write-Host "`n🗑️  Cleanup:" -ForegroundColor Cyan
$cleanup = Read-Host "   Do you want to delete the cloned repository folder? (Y/N)"
if ($cleanup -eq "Y" -or $cleanup -eq "y") {
    Remove-Item -Path $cloneDir -Recurse -Force
    Write-Host "   ✅ Cleanup complete!" -ForegroundColor Green
} else {
    Write-Host "   Repository kept at: $cloneDir" -ForegroundColor White
}

Write-Host "`n"
