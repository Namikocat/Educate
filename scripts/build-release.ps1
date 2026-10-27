# Reproducible Windows release build for UniLearn Studio.
# Prerequisites (developer machine only): Python 3.12+ (3.14 tested), Node 20+, Rust stable MSVC, VS Build Tools (C++).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1 [-SkipTests]
param([switch]$SkipTests)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
$engine = Join-Path $root "services\math-engine"
$py = Join-Path $engine ".venv\Scripts\python.exe"

Write-Host "== 1. Python environment"
if (-not (Test-Path $py)) { py -3 -m venv (Join-Path $engine ".venv") }
& $py -m pip install -q -r (Join-Path $engine "requirements.txt")

if (-not $SkipTests) {
  Write-Host "== 2. Tests"
  Push-Location $engine; & $py -X utf8 -m pytest -q; if ($LASTEXITCODE) { throw "python tests failed" }; Pop-Location
  & $py -X utf8 (Join-Path $root "tools\curriculum-validator\validate.py") (Join-Path $root "subjects\calculus") --write
  if ($LASTEXITCODE) { throw "curriculum validation failed" }
  Push-Location (Join-Path $root "apps\desktop"); npm ci; npx tsc --noEmit; npx vitest run; if ($LASTEXITCODE) { throw "frontend tests failed" }; Pop-Location
  Push-Location (Join-Path $root "apps\desktop\src-tauri"); cargo test; if ($LASTEXITCODE) { throw "rust tests failed" }; Pop-Location
}

Write-Host "== 3. Freeze math engine (PyInstaller onedir)"
Push-Location $engine
& (Join-Path $engine ".venv\Scripts\pyinstaller.exe") --noconfirm --clean --onedir --console --name unilearn-math `
  --distpath ..\..\build\math-engine --workpath ..\..\build\pyinstaller-work --specpath ..\..\build `
  --collect-submodules unilearn_math --exclude-module tkinter --exclude-module matplotlib --exclude-module PIL `
  --exclude-module pymupdf --exclude-module fitz --exclude-module PyInstaller --exclude-module pytest --exclude-module hypothesis engine_main.py
if ($LASTEXITCODE) { throw "pyinstaller failed" }
Pop-Location

Write-Host "== 4. Desktop app + installers (NSIS, MSI)"
Push-Location (Join-Path $root "apps\desktop"); npm ci; npx tauri build; if ($LASTEXITCODE) { throw "tauri build failed" }; Pop-Location

Write-Host "== 5. Checksums"
$out = Join-Path $root "release"
New-Item -ItemType Directory -Force $out | Out-Null
$bundle = Join-Path $root "apps\desktop\src-tauri\target\release\bundle"
Get-ChildItem $bundle -Recurse -Include *.exe, *.msi | ForEach-Object { Copy-Item $_.FullName $out -Force }
Get-ChildItem $out -Include *.exe, *.msi -Recurse | Get-FileHash -Algorithm SHA256 |
  ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), (Split-Path -Leaf $_.Path) } | Set-Content -Encoding utf8 (Join-Path $out "SHA256SUMS.txt")
Get-Content (Join-Path $out "SHA256SUMS.txt")
