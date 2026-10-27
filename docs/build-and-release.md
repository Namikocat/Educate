# Build and release

## Prerequisites (developers only)

* Windows 10/11 x64, Visual Studio Build Tools (C++ workload), WebView2 runtime
* Python 3.12+ (tested 3.14.5), Node 20+ (tested 24.15), Rust stable MSVC (tested 1.99.1)

Students need none of these: the installer bundles the frozen math engine; WebView2 is installed by the
bootstrapper if missing (Windows 11 ships it).

## One command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1
```

Steps: create/refresh `services/math-engine/.venv` from pinned `requirements.txt` → Python, content, frontend and
Rust tests → PyInstaller `--onedir` freeze into `build/math-engine/unilearn-math/` → `npx tauri build` (bundles that
folder as the `math-engine/` resource, produces NSIS `.exe` and WiX `.msi`) → copies installers to `release/` and
writes `release/SHA256SUMS.txt`.

## Manual steps

```powershell
cd services\math-engine; .venv\Scripts\pyinstaller --noconfirm --clean --onedir --console --name unilearn-math `
  --distpath ..\..\build\math-engine --workpath ..\..\build\pyinstaller-work --specpath ..\..\build `
  --collect-submodules unilearn_math --exclude-module tkinter --exclude-module PIL --exclude-module pymupdf engine_main.py
cd ..\..\apps\desktop; npm ci; npx tauri build          # release
npx tauri dev                                           # debug build with hot reload (uses the repo .venv engine)
```

Debug builds fall back to `services/math-engine/.venv/Scripts/python.exe -m unilearn_math.server` when the frozen
engine is not present (override with `UNILEARN_PYTHON`).

## Runtime locations

| What | Where |
|---|---|
| Program | `%LOCALAPPDATA%\UniLearn Studio\` (NSIS per-user install) or `C:\Program Files\UniLearn Studio\` (MSI) |
| Math engine | `<install>\math-engine\unilearn-math.exe` (located via Tauri resource dir) |
| Database | `%APPDATA%\studio.unilearn.desktop\unilearn.db` (+ `backups\`) |
| Exports (backups, PNG) | `%USERPROFILE%\Downloads\UniLearn Studio\` |

Uninstall via *Settings → Apps* (NSIS/MSI uninstallers). User data in `%APPDATA%` is kept on uninstall.

## Release dependencies (pinned)

Python: see `services/math-engine/requirements.txt`. JS: `apps/desktop/package-lock.json`. Rust: `apps/desktop/src-tauri/Cargo.lock`.
