<#
.SYNOPSIS
  Installs the Swiggy Clone backend and frontend as Windows services (via NSSM)
  so they auto-start on boot and auto-restart if they crash.

.NOTES
  Run this from an ELEVATED PowerShell (Run as Administrator). It cannot be run
  as a normal user — creating/starting Windows services requires admin rights.

  This only makes the dev servers durable on THIS machine. It does not extend
  reachability beyond your LAN. Pair it with a router DHCP reservation for
  192.168.30.16 (MAC A8-93-4A-05-D3-61 on the "Wi-Fi" adapter) so the IP in
  your URL never changes.
#>

$ErrorActionPreference = "Stop"

$repoRoot   = "D:\FastAPIproject"
$backendDir = Join-Path $repoRoot "Backend"
$frontendDir= Join-Path $repoRoot "Frontend\Swiggy_Clone"

$uvicornExe = "C:\Users\bhavy\Scripts\uvicorn.exe"
$nodeExe    = "C:\Program Files\nodejs\node.exe"
$npmCli     = "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js"

$lanIp = "192.168.30.16"

# --- Ensure we're actually elevated ---
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this script from an elevated (Administrator) PowerShell."
    exit 1
}

# --- Install NSSM if missing ---
if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Host "Installing NSSM via winget..."
    winget install --id NSSM.NSSM -e --accept-source-agreements --accept-package-agreements
}

function Install-Service($name, $exe, $args, $appDir, $envExtra) {
    # Remove any previous install of this service so re-running is idempotent
    nssm stop $name 2>$null | Out-Null
    nssm remove $name confirm 2>$null | Out-Null

    nssm install $name $exe $args
    nssm set $name AppDirectory $appDir
    nssm set $name Start SERVICE_AUTO_START
    nssm set $name AppExit Default Restart      # restart on crash
    nssm set $name AppRestartDelay 3000          # 3s backoff between restarts
    if ($envExtra) {
        nssm set $name AppEnvironmentExtra $envExtra
    }
    nssm start $name
    Write-Host "Installed and started service: $name"
}

Install-Service `
    -name "SwiggyCloneBackend" `
    -exe $uvicornExe `
    -args "main:app --host 0.0.0.0 --port 8000" `
    -appDir $backendDir `
    -envExtra "CORS_ORIGINS=http://$($lanIp):3000"

Install-Service `
    -name "SwiggyCloneFrontend" `
    -exe $nodeExe `
    -args "`"$npmCli`" start" `
    -appDir $frontendDir `
    -envExtra $null   # frontend reads REACT_APP_API_URL from .env.local in that folder

Write-Host ""
Write-Host "Done. Both services are set to start automatically on boot and restart on crash."
Write-Host "Check status any time with:  Get-Service SwiggyCloneBackend, SwiggyCloneFrontend"
Write-Host "URL (once the frontend finishes its first compile, can take ~30-60s after boot):"
Write-Host "  http://$($lanIp):3000"
