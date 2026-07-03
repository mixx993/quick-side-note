param(
    [switch]$SkipAppBuild
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$appVersion = "1.3.1"
$appDir = Join-Path $root "release\QuickSideNote_App_v$appVersion"
$supportSourceDir = Join-Path $root "release\QuickSideNote_App"
$setupScript = Join-Path $root "installer\QuickSideNote.iss"
$pyInstallerSpec = Join-Path $root "QuickSideNote.spec"
$distExe = Join-Path $root "dist\QuickSideNote.exe"
$appExe = Join-Path $appDir "QuickSideNote.exe"
$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

function Resolve-Iscc {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in $isccCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "ISCC.exe was not found. Install Inno Setup 6 first, or run: winget install --id JRSoftware.InnoSetup -e"
}

Set-Location $root

if (-not $SkipAppBuild) {
    python -m PyInstaller --clean $pyInstallerSpec
    New-Item -ItemType Directory -Force -Path $appDir | Out-Null
    Copy-Item -LiteralPath $distExe -Destination $appExe -Force
} else {
    New-Item -ItemType Directory -Force -Path $appDir | Out-Null
}

foreach ($supportFile in @("README_RUN.txt", "QuickSideNote_intro.html", "quick_note_ui_preview.png")) {
    $source = Join-Path $supportSourceDir $supportFile
    $destination = Join-Path $appDir $supportFile
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }
}

foreach ($required in @(
    $appExe,
    (Join-Path $appDir "README_RUN.txt"),
    (Join-Path $appDir "QuickSideNote_intro.html"),
    (Join-Path $appDir "quick_note_ui_preview.png"),
    $setupScript
)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing installer input file: $required"
    }
}

$iscc = Resolve-Iscc
& $iscc $setupScript

$installer = Get-ChildItem -LiteralPath (Join-Path $root "release") -Filter "QuickSideNote_Setup_v*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $installer) {
    throw "Installer compiler finished, but no setup exe was found."
}

Write-Host "Installer created: $($installer.FullName)"
