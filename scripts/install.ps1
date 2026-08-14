$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Repository = if ($env:LEMONO_REPOSITORY) { $env:LEMONO_REPOSITORY } else { "mkseo1012-pixel/Lemono-Agent" }
$Ref = if ($env:LEMONO_REF) { $env:LEMONO_REF } else { "main" }
$InstallRoot = if ($env:LEMONO_INSTALL_DIR) { $env:LEMONO_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "LemonoAgent" }
$BinDir = if ($env:LEMONO_BIN_DIR) { $env:LEMONO_BIN_DIR } else { Join-Path $HOME ".local\bin" }

if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw "Invalid LEMONO_REPOSITORY value"
}

function Test-PythonCandidate {
    param([string]$Command, [string[]]$PrefixArguments)
    try {
        & $Command @PrefixArguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Find-Python {
    $Candidates = @(
        @{ Command = "py.exe"; Arguments = @("-3.13") },
        @{ Command = "py.exe"; Arguments = @("-3.12") },
        @{ Command = "py.exe"; Arguments = @("-3.11") },
        @{ Command = "python.exe"; Arguments = @() },
        @{ Command = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"); Arguments = @() },
        @{ Command = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"); Arguments = @() },
        @{ Command = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"); Arguments = @() }
    )
    foreach ($Candidate in $Candidates) {
        if (Test-PythonCandidate $Candidate.Command $Candidate.Arguments) {
            return [PSCustomObject]$Candidate
        }
    }
    return $null
}

$Python = Find-Python
if (-not $Python) {
    $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $Winget) {
        throw "Python 3.11+ is missing and WinGet is unavailable. Install Microsoft App Installer, then run this command again."
    }
    Write-Host "Installing required Python 3.12 with WinGet..."
    & $Winget.Source install --id Python.Python.3.12 --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        throw "WinGet could not install Python 3.12 (exit code $LASTEXITCODE)"
    }
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    $Python = Find-Python
    if (-not $Python) {
        throw "Python was installed but could not be located. Open a new PowerShell window and run the installer again."
    }
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $Python.Command @($Python.Arguments) @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

$TemporaryDirectory = Join-Path ([IO.Path]::GetTempPath()) ("lemono-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TemporaryDirectory | Out-Null
try {
    $EncodedRef = [Uri]::EscapeDataString($Ref)
    $Headers = @{ "User-Agent" = "Lemono-Installer"; "Accept" = "application/vnd.github+json" }
    Write-Host "Resolving Lemono Agent revision ($Ref)..."
    $CommitInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository/commits/$EncodedRef" -Headers $Headers
    $Commit = [string]$CommitInfo.sha
    if ($Commit -notmatch '^[0-9a-f]{40}$') {
        throw "GitHub returned an invalid revision"
    }

    $Archive = Join-Path $TemporaryDirectory "lemono.zip"
    $Extracted = Join-Path $TemporaryDirectory "source"
    Invoke-WebRequest -Uri "https://codeload.github.com/$Repository/zip/$Commit" -OutFile $Archive -Headers $Headers
    Expand-Archive -Path $Archive -DestinationPath $Extracted
    $Source = Get-ChildItem -Path $Extracted -Directory | Select-Object -First 1
    if (-not $Source -or -not (Test-Path (Join-Path $Source.FullName "pyproject.toml"))) {
        throw "Downloaded archive is not a valid Lemono Agent release"
    }

    $ReleaseDirectory = Join-Path $InstallRoot "releases\$Commit"
    New-Item -ItemType Directory -Force -Path (Split-Path $ReleaseDirectory), $BinDir | Out-Null
    if (-not (Test-Path $ReleaseDirectory)) {
        Move-Item -Path $Source.FullName -Destination $ReleaseDirectory
    }
    $VenvPython = Join-Path $ReleaseDirectory ".venv\Scripts\python.exe"
    if (-not (Test-Path $VenvPython)) {
        Invoke-Python -m venv (Join-Path $ReleaseDirectory ".venv")
    }
    & $VenvPython -m pip install --quiet --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not update pip" }
    & $VenvPython -m pip install --quiet --upgrade $ReleaseDirectory
    if ($LASTEXITCODE -ne 0) { throw "Could not install Lemono Agent" }

    $LemonoExecutable = Join-Path $ReleaseDirectory ".venv\Scripts\lemono.exe"
    $Launcher = Join-Path $BinDir "lemono.cmd"
    $TemporaryLauncher = "$Launcher.tmp"
    Set-Content -Path $TemporaryLauncher -Encoding Ascii -Value "@echo off`r`n`"$LemonoExecutable`" %*"
    Move-Item -Force -Path $TemporaryLauncher -Destination $Launcher

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $PathParts = @($UserPath -split ';' | Where-Object { $_ })
    if ($PathParts -notcontains $BinDir) {
        $NewPath = (@($PathParts) + $BinDir) -join ';'
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    }
    if (($env:Path -split ';') -notcontains $BinDir) {
        $env:Path = "$BinDir;$env:Path"
    }

    Write-Host "`nLemono Agent installed successfully without WSL."
    Write-Host "Command: $Launcher"
    if ($env:LEMONO_NO_SETUP -ne "1") {
        $Answer = Read-Host "Configure an AI provider now? [Y/n]"
        if ($Answer -notmatch '^(n|no)$') {
            & $LemonoExecutable setup
        } else {
            Write-Host "Run 'lemono setup' whenever you are ready."
        }
    }
} finally {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $TemporaryDirectory
}
