# SCM Risk Intelligence Platform — Desktop Launcher
# Starts Docker services + Next.js dev server, then opens Chrome in app mode.

$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$FrontendDir = Join-Path $ProjectRoot "frontend"
$NpmCmd = "C:\Program Files\nodejs\npm.cmd"
$Port = 3000
$Url = "http://localhost:$Port"

# --- Detect browser ---
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$EdgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if (Test-Path $ChromePath) {
    $BrowserPath = $ChromePath
} elseif (Test-Path $EdgePath) {
    $BrowserPath = $EdgePath
} else {
    # Fallback: open in default browser
    $BrowserPath = $null
}

# --- Step 1: Docker services ---
$DockerCompose = Join-Path $ProjectRoot "docker-compose.yml"
if (Test-Path $DockerCompose) {
    $dockerStatus = docker compose -f $DockerCompose ps --format json 2>$null
    if (-not $dockerStatus -or $dockerStatus -match '"State":"exited"') {
        Start-Process -FilePath "docker" -ArgumentList "compose", "-f", $DockerCompose, "up", "-d" -WindowStyle Hidden -Wait
    }
}

# --- Step 2: Check if dev server is already running ---
$serverRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("localhost", $Port)
    $tcp.Close()
    $serverRunning = $true
} catch {
    $serverRunning = $false
}

# --- Step 3: Start dev server if needed ---
if (-not $serverRunning) {
    Start-Process -FilePath $NpmCmd -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -WindowStyle Hidden
}

# --- Step 4: Wait for server to be ready ---
$timeout = 60
$elapsed = 0
while ($elapsed -lt $timeout) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { break }
    } catch { }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if ($elapsed -ge $timeout) {
    [System.Windows.Forms.MessageBox]::Show("Dev server failed to start within $timeout seconds.", "SCM Risk Intelligence", 0, 48)
    exit 1
}

# --- Step 5: Open browser in app mode ---
if ($BrowserPath) {
    Start-Process -FilePath $BrowserPath -ArgumentList "--app=$Url", "--window-size=1920,1080"
} else {
    Start-Process $Url
}
