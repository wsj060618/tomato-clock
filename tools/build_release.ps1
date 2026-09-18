# 一键构建：读版本 -> 生成版本信息 -> PyInstaller(onedir) -> 便携 zip -> Inno Setup 安装包
# 用法：powershell -ExecutionPolicy Bypass -File tools\build_release.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# 1. 版本号唯一来源：pomodoro/__init__.py
$initPy = Join-Path $Root "pomodoro\__init__.py"
$match  = Select-String -LiteralPath $initPy -Pattern '__version__\s*=\s*"([^"]+)"'
if (-not $match) { throw "Cannot read __version__ from $initPy" }
$version = $match.Matches[0].Groups[1].Value
Write-Host "版本: $version"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }

# 2. 生成 exe 版本信息
& $Python (Join-Path $Root "tools\make_version_info.py")
if ($LASTEXITCODE -ne 0) { throw "make_version_info failed" }

# 3. PyInstaller onedir（用 *.spec 匹配，避开中文文件名编码问题）
$spec = (Get-ChildItem -LiteralPath $Root -Filter *.spec | Select-Object -First 1).FullName
if (-not $spec) { throw "No .spec file found" }
& $Python -m PyInstaller --noconfirm $spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$appDir = Join-Path $Root "dist\TomatoClock-v$version"
if (-not (Test-Path -LiteralPath $appDir)) { throw "Build output not found: $appDir" }

# 4. 便携 zip（解压即用）
$outDir = Join-Path $Root "dist\installer"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$zip = Join-Path $outDir "TomatoClock-Portable-v$version.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -LiteralPath $appDir -DestinationPath $zip -CompressionLevel Optimal
Write-Host "便携版: $zip"

# 5. Inno Setup 安装包
$Iscc = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Iscc) { throw "ISCC.exe not found. Install: winget install JRSoftware.InnoSetup" }

& $Iscc "/DAppVersion=$version" (Join-Path $Root "installer\TomatoClock.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed" }

Write-Host "安装包: $outDir\TomatoClock-Setup-v$version.exe"
