param(
    [switch]$SkipAppBuild
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$appVersion = "1.5.2"
$releaseDir = Join-Path $root "release"
$appDir = Join-Path $releaseDir "QuickSideNote_App_v$appVersion"
$portableZip = Join-Path $releaseDir "QuickSideNote_App_v$appVersion.zip"
$installerPath = Join-Path $releaseDir "QuickSideNote_Setup_v$appVersion.exe"
$buildManifest = Join-Path $appDir "build-manifest.json"
$docsDir = Join-Path $root "docs"
$docsImageDir = Join-Path $docsDir "images"
$appImageDir = Join-Path $appDir "images"
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

function Assert-NativeSuccess {
    param([string]$Name)

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

function Read-Version {
    param([string]$Path, [string]$Pattern)

    $match = [regex]::Match((Get-Content -Raw -LiteralPath $Path), $Pattern)
    if (-not $match.Success) {
        throw "Could not find a version in $Path."
    }
    return $match.Groups[1].Value
}

function Assert-AppExecutableVersion {
    param([string]$Path, [string]$ExpectedVersion)

    $fileVersion = (Get-Item -LiteralPath $Path).VersionInfo.FileVersion
    if ([string]::IsNullOrWhiteSpace($fileVersion) -or -not $fileVersion.StartsWith($ExpectedVersion)) {
        throw "Executable version mismatch. Expected $ExpectedVersion; got $fileVersion."
    }
}

Set-Location $root
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

$sourceVersion = Read-Version (Join-Path $root "quick_note.py") 'APP_VERSION\s*=\s*"([^"]+)"'
$installerVersion = Read-Version $setupScript '#define MyAppVersion "([^"]+)"'
$readmeVersion = Read-Version (Join-Path $root "README.md") 'QuickSideNote_Setup_v([0-9.]+)\.exe'
if ($sourceVersion -ne $appVersion -or $installerVersion -ne $appVersion -or $readmeVersion -ne $appVersion) {
    throw "Version mismatch. Expected $appVersion; source=$sourceVersion installer=$installerVersion readme=$readmeVersion."
}

if (-not $SkipAppBuild) {
    Remove-Item -LiteralPath $appDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $portableZip -Force -ErrorAction SilentlyContinue

    & python -m PyInstaller --clean $pyInstallerSpec
    Assert-NativeSuccess "PyInstaller"
    if (-not (Test-Path -LiteralPath $distExe)) {
        throw "PyInstaller reported success but did not create $distExe."
    }
    Assert-AppExecutableVersion $distExe $appVersion
    New-Item -ItemType Directory -Force -Path $appDir | Out-Null
    Copy-Item -LiteralPath $distExe -Destination $appExe -Force
    [PSCustomObject]@{
        version = $appVersion
        executable_sha256 = (Get-FileHash -LiteralPath $appExe -Algorithm SHA256).Hash
        built_at = (Get-Date).ToUniversalTime().ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath $buildManifest -Encoding UTF8
} elseif (-not (Test-Path -LiteralPath $appExe) -or -not (Test-Path -LiteralPath $buildManifest)) {
    throw "-SkipAppBuild requires an existing $appExe and build manifest."
} else {
    $manifest = Get-Content -Raw -LiteralPath $buildManifest | ConvertFrom-Json
    $actualHash = (Get-FileHash -LiteralPath $appExe -Algorithm SHA256).Hash
    if ($manifest.version -ne $appVersion -or $manifest.executable_sha256 -ne $actualHash) {
        throw "-SkipAppBuild refused an executable that does not match the v$appVersion build manifest."
    }
    Assert-AppExecutableVersion $appExe $appVersion
}

foreach ($supportItem in @(
    @{ Source = (Join-Path $docsDir "README_RUN.txt"); Destination = (Join-Path $appDir "README_RUN.txt") },
    @{ Source = (Join-Path $docsDir "QuickSideNote_intro.html"); Destination = (Join-Path $appDir "QuickSideNote_intro.html") }
)) {
    if (-not (Test-Path -LiteralPath $supportItem.Source)) {
        throw "Missing installer support file: $($supportItem.Source)"
    }
    Copy-Item -LiteralPath $supportItem.Source -Destination $supportItem.Destination -Force
}

if (-not (Test-Path -LiteralPath $docsImageDir)) {
    throw "Missing installer image directory: $docsImageDir"
}
Copy-Item -LiteralPath $docsImageDir -Destination $appImageDir -Recurse -Force

foreach ($required in @(
    $appExe,
    $buildManifest,
    (Join-Path $appDir "README_RUN.txt"),
    (Join-Path $appDir "QuickSideNote_intro.html"),
    (Join-Path $appImageDir "quick_note_ui_preview.png"),
    $setupScript
)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing installer input file: $required"
    }
}

$iscc = Resolve-Iscc
& $iscc $setupScript
Assert-NativeSuccess "Inno Setup"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Inno Setup reported success but did not create $installerPath."
}

Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $portableZip -Force
if (-not (Test-Path -LiteralPath $portableZip)) {
    throw "Portable ZIP was not created: $portableZip"
}

$installerHash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash
$portableHash = (Get-FileHash -LiteralPath $portableZip -Algorithm SHA256).Hash
Write-Host "Installer created: $installerPath"
Write-Host "Portable ZIP created: $portableZip"
Write-Host "SHA256 (installer): $installerHash"
Write-Host "SHA256 (portable): $portableHash"
