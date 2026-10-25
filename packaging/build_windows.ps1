$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'venv failed' }
}
$python = '.venv\Scripts\python.exe'
& $python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
$env:QT_QPA_PLATFORM = 'offscreen'
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
Remove-Item Env:QT_QPA_PLATFORM
& $python -m PyInstaller --noconfirm --clean --windowed --onedir --name SpinPopulationLab desktop.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
$iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
if (!(Test-Path $iscc)) { throw 'Install Inno Setup 6 to create the installer. The portable app is in dist\SpinPopulationLab.' }
& $iscc 'packaging\installer.iss'
if ($LASTEXITCODE -ne 0) { throw 'Installer failed' }
