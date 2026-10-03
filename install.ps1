# Windows PowerShell 5.1 / PowerShell 7
[CmdletBinding()]
param([string]$PythonPath = "")

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
$Candidates = @()
if ($PythonPath) {
    $Candidates += ,@($PythonPath)
} else {
    $Candidates += ,@("py", "-3")
    $Candidates += ,@("python")
    $Candidates += ,@("python3")
}
$Selected = $null
foreach ($Candidate in $Candidates) {
    $Executable = $Candidate[0]
    if (-not (Get-Command $Executable -ErrorAction SilentlyContinue)) { continue }
    $Prefix = @()
    if ($Candidate.Count -gt 1) { $Prefix = @($Candidate[1..($Candidate.Count - 1)]) }
    try {
        & $Executable @Prefix -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Selected = $Candidate; break }
    } catch { continue }
}
if ($null -eq $Selected) {
    throw "Python 3.10+ required. Install Python, reopen PowerShell, or run: .\install.ps1 -PythonPath 'C:\path\python.exe'"
}
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $Executable" }
}
$PythonExe = $Selected[0]
$PythonPrefix = @()
if ($Selected.Count -gt 1) { $PythonPrefix = @($Selected[1..($Selected.Count - 1)]) }
$VenvPath = Join-Path $ProjectDir ".venv"
Invoke-Checked -Executable $PythonExe -Arguments ($PythonPrefix + @("-m", "venv", $VenvPath))
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
Invoke-Checked -Executable $VenvPython -Arguments @("-m", "pip", "install", "-r", (Join-Path $ProjectDir "requirements.txt"))
Invoke-Checked -Executable $VenvPython -Arguments @("-m", "playwright", "install", "chromium")
$Check = @'
import asyncio
from playwright.async_api import async_playwright
async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content('<main>browser check</main>')
        assert await page.inner_text('main') == 'browser check'
        await browser.close()
asyncio.run(check())
print('Browser launch check passed')
'@
Invoke-Checked -Executable $VenvPython -Arguments @("-c", $Check)
Write-Host "Installation complete. Open this folder in local Codex: $ProjectDir"
