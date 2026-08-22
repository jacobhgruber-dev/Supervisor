<#
.SYNOPSIS
    Windows installer for the OpenCode Supervisor workspace.

.DESCRIPTION
    Copies the Supervisor agent tree, subagents, skills, the observer plugin and
    AGENTS.md into %USERPROFILE%\.config\opencode (or -ConfigDir), then writes a
    .supervisor-state.json baseline that update.ps1 uses for safe 3-way updates.
    This is the Windows counterpart of install.sh (same layout, same state file
    format, same merge helper).

    opencode.json handling:
      - If an opencode.json already exists, it is ALWAYS safely merged via
        `node scripts/merge-config.mjs` (only four keys are ever touched:
        subagent_depth, default_agent, plugin, mcp.a11y-color-contrast).
        Everything else is preserved. A backup copy is made first.
      - If it does not exist, it is created from opencode.template.json only
        when -WithConfig is passed. On Windows the macOS-only MCP servers
        (macos-use, macos-automator) are dropped from that fresh copy and never
        warned about - Playwright is the universal browser-testing engine.

    If your execution policy blocks this script, run:
        powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
    or, in PowerShell 7:
        pwsh -NoProfile -ExecutionPolicy Bypass -File setup.ps1

.PARAMETER Doctor
    Scan for tools using deps.json and report installed vs missing (Windows
    package managers: winget, choco, scoop, pip, npm). Never fails. Exits
    after the report, like install.sh --doctor.

.PARAMETER DryRun
    Preview every file operation without touching the disk.

.PARAMETER WithConfig
    Create opencode.json from opencode.template.json when it is missing.
    (Existing configs are always merged, with or without this switch.)

.PARAMETER ConfigDir
    Custom config root. Default: %USERPROFILE%\.config\opencode.

.PARAMETER Force
    Non-interactive: overwrite user-modified files without prompting, backing
    them up first into <ConfigDir>\backups\supervisor-<timestamp>.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 -Doctor

.EXAMPLE
    pwsh -NoProfile -File setup.ps1 -WithConfig -DryRun

.EXAMPLE
    pwsh -NoProfile -File setup.ps1 -WithConfig -Force
#>
[CmdletBinding()]
param(
    [switch]$Doctor,
    [switch]$DryRun,
    [switch]$WithConfig,
    [switch]$Force,
    [string]$ConfigDir = '',
    [switch]$Help
)

# --- Help ---------------------------------------------------------------
if ($Help) {
    Get-Help -Detailed ($MyInvocation.MyCommand.Path)
    exit 0
}

# --- Shared helpers ------------------------------------------------------
$CommonPath = Join-Path $PSScriptRoot 'scripts\supervisor-install-common.ps1'
if (-not (Test-Path -LiteralPath $CommonPath -PathType Leaf)) {
    Write-Error "Missing helper module: $CommonPath"
    exit 1
}
. $CommonPath

# --- Execution policy ----------------------------------------------------
# If we are running, we were already allowed to run. Still, best-effort:
# lift the policy for this process only, so any child processes (node) and
# future scripts started from here are not blocked.
try {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue | Out-Null
} catch {
    # Some hosts refuse even the Process scope; harmless, keep going.
}
Write-Verbose 'Execution policy note: if a policy blocks this script, rerun with: powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1'

# --- Platform ------------------------------------------------------------
if (-not (Test-IsWindows)) {
    Write-Warning 'This is the Windows installer and this machine does not look like Windows. Continuing anyway (the file layout is identical).'
}

# --- ConfigDir -----------------------------------------------------------
if ([string]::IsNullOrWhiteSpace($ConfigDir)) {
    if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        Write-Error 'USERPROFILE is empty; pass -ConfigDir explicitly.'
        exit 1
    }
    $ConfigDir = Join-Path $env:USERPROFILE '.config\opencode'
}

$RepoRoot = $PSScriptRoot
Write-Host ''
Write-Host '=== Supervisor setup (Windows) ==='
Write-Host "Repo:     $RepoRoot"
Write-Host "Config:   $ConfigDir"
Write-Host "Mode:     $(if ($DryRun) { 'DryRun (preview only, nothing is written)' } else { 'install' })"

# --- Doctor ---------------------------------------------------------------
function Invoke-DoctorScan {
    # Mirrors install.sh --doctor (same deps.json schema, same output shape).
    param([string]$ScanRepoRoot)
    $depsPath = Join-Path $ScanRepoRoot 'deps.json'
    if (-not (Test-Path -LiteralPath $depsPath -PathType Leaf)) {
        Write-Warning "deps.json not found at $depsPath - cannot scan."
        return
    }
    try {
        $deps = Get-Content -LiteralPath $depsPath -Raw | ConvertFrom-Json
    } catch {
        Write-Warning "deps.json is not valid JSON: $($_.Exception.Message)"
        return
    }

    $priority = @('winget', 'choco', 'scoop', 'pip', 'npm')
    $available = New-Object System.Collections.Generic.HashSet[string]
    foreach ($mgr in $priority) {
        if (Get-Command $mgr -ErrorAction SilentlyContinue) { [void]$available.Add($mgr) }
    }
    $py = $null
    if (Get-Command python3 -ErrorAction SilentlyContinue) { $py = 'python3' }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $py = 'python' }

    Write-Host ''
    Write-Host '=== Doctor: dependency scan (deps.json) ==='
    Write-Host 'Platform: windows'
    if ($available.Count -gt 0) { Write-Host "Package managers detected: $($available -join ', ')" }
    else { Write-Host 'Package managers detected: none' }
    if ($py) { Write-Host "python: $py" } else { Write-Host 'python: MISSING' }

    function Test-ToolInstalled {
        param($Tool)
        if ($null -ne $Tool.detect.commands) {
            foreach ($cmd in $Tool.detect.commands) {
                if (Get-Command ([string]$cmd).Trim() -ErrorAction SilentlyContinue) { return $true }
            }
        }
        if ($py -and $null -ne $Tool.detect.python_modules) {
            foreach ($mod in $Tool.detect.python_modules) {
                & $py -c "import $mod" 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return $true }
            }
        }
        return $false
    }

    function Get-InstallLine {
        param($Tool)
        $perPlat = $Tool.install.windows
        if ($null -eq $perPlat) { return @() }
        $lines = @()
        foreach ($mgr in $priority) {
            $entry = $perPlat.PSObject.Properties | Where-Object { $_.Name -eq $mgr } | Select-Object -First 1
            if ($null -ne $entry) {
                $argv = @($entry.Value)
                $detected = $available.Contains($mgr)
                $tag = if ($detected) { '' } else { ' (package manager not detected)' }
                $lines += ,@("$mgr`:$($argv -join ' ')$tag")
            }
        }
        if ($lines.Count -eq 0) {
            $first = $perPlat.PSObject.Properties | Select-Object -First 1
            if ($null -ne $first) {
                $argv = @($first.Value)
                $lines += ,@("$($first.Name): $($argv -join ' ')")
            }
        }
        return $lines
    }

    $total = 0
    $missing = 0
    foreach ($catProp in $deps.categories.PSObject.Properties) {
        $category = $catProp.Value
        $label = $catProp.Name
        if ($null -ne $category.label) { $label = [string]$category.label }
        Write-Host ''
        Write-Host "== $label =="
        if ($null -eq $category.tools) { continue }
        foreach ($toolProp in $category.tools.PSObject.Properties) {
            $name = $toolProp.Name
            $tool = $toolProp.Value
            $total += 1
            if (Test-ToolInstalled -Tool $tool) {
                Write-Host "  [ok] $name"
                continue
            }
            $missing += 1
            Write-Host "  [--] $name"
            $lines = @(Get-InstallLine -Tool $tool)
            if ($lines.Count -gt 0) {
                foreach ($line in $lines) { Write-Host "       install: $line" }
            } else {
                Write-Host '       install: manual install - see DEPENDENCIES.md'
            }
            if ($null -ne $tool.notes) { Write-Host "       note: $($tool.notes)" }
        }
    }
    Write-Host ''
    Write-Host "Summary: $($total - $missing)/$total tools available."
    if ($missing -gt 0) {
        Write-Host "Run the listed commands for the $missing missing tool(s), then re-run -Doctor."
    } else {
        Write-Host 'All tools present.'
    }
    Write-Host 'Next step: opencode auth login (see PROVIDERS.md)'
}

if ($Doctor) {
    Invoke-DoctorScan -ScanRepoRoot $RepoRoot
    Write-Host ''
    Write-Host 'Doctor never fails; missing items are informational.'
    exit 0
}

# --- Classify managed files -----------------------------------------------
$state = Read-StateFile -ConfigDir $ConfigDir
$classified = @(Get-ClassifiedFiles -RepoRoot $RepoRoot -ConfigDir $ConfigDir -State $state -UnitFilter $null)

Write-Host ''
Write-Host '=== Install plan ==='
Write-Host ('{0,-16} {1,-36} {2}' -f 'Status', 'File (relative)', 'Detail')
Write-Host ('{0,-16} {1,-36} {2}' -f ('-' * 16), ('-' * 36), ('-' * 24))

$toInstall = @()    # files to copy (new or changed)
$toPrompt = @()     # user-modified / unmanaged files that need a decision
$upToDate = @()     # managed files already matching the repo source

foreach ($f in $classified) {
    $label = ''
    $detail = ''
    switch ($f.Status) {
        'install'          { $label = '[INSTALL]';      $detail = 'new file'; $toInstall += $f }
        'managed'          {
            if ($f.SourceHash -eq $f.CurrentHash) {
                $label = '[OK]'; $detail = 'up to date'; $upToDate += $f
            } else {
                $label = '[UPDATE]'; $detail = 'managed; will replace'; $toInstall += $f
            }
        }
        'modified'         { $label = '[USER-MODIFIED]'; $detail = 'needs a decision'; $toPrompt += $f }
        'unmanaged'        { $label = '[USER FILE]';     $detail = 'not managed; needs a decision'; $toPrompt += $f }
        'removed-upstream' { $label = '[LEFT]';          $detail = 'no longer shipped upstream; keeping your file' }
        default            { $label = '[?]';             $detail = 'unknown state' }
    }
    Write-Host ('{0,-16} {1,-36} {2}' -f $label, $f.RelPath, $detail)
}

# --- Decision: user-modified files -----------------------------------------
$overwriteModified = [bool]$Force
if ($toPrompt.Count -gt 0) {
    if ($DryRun) {
        Write-Host ''
        Write-Host "DryRun: $($toPrompt.Count) user-modified file(s) would require a prompt (or -Force to overwrite with backup)."
    } elseif (-not $Force) {
        Write-Host ''
        $overwriteModified = Confirm-YesNo -Message "$($toPrompt.Count) file(s) exist locally and are not managed. Overwrite them with the repo versions? They will be backed up first."
    }
}
if ($overwriteModified) {
    foreach ($f in $toPrompt) { $toInstall += $f }
} elseif ($toPrompt.Count -gt 0) {
    Write-Host "Keeping $($toPrompt.Count) user-modified file(s) untouched."
}

# --- Config (opencode.json) -------------------------------------------------
$configDest = Join-Path $ConfigDir 'opencode.json'
$configExists = Test-Path -LiteralPath $configDest -PathType Leaf
$configMerged = $false
$configCreated = $false
$configSkipped = $false
$mergeOutput = @()
$removedMacos = @()

if ($configExists) {
    # Existing config: always merge (only 4 keys, everything else preserved).
    if ($DryRun) {
        Write-Host ''
        Write-Host 'Config: existing opencode.json - merge would apply:'
        $mergeOutput = Invoke-ConfigMerge -RepoRoot $RepoRoot -ConfigDir $ConfigDir -Dry
    } else {
        # Flat backup first, exactly like install.sh.
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $backupsDir = Join-Path $ConfigDir 'backups'
        New-Item -ItemType Directory -Force -Path $backupsDir | Out-Null
        $bak = Join-Path $backupsDir "opencode.json.$stamp.bak"
        Copy-Item -LiteralPath $configDest -Destination $bak
        Write-Host ''
        Write-Host "Backup: opencode.json -> $bak"
        Write-Host 'Config: merging opencode.json (only subagent_depth, default_agent, plugin, a11y-color-contrast MCP are touched)'
        $mergeOutput = Invoke-ConfigMerge -RepoRoot $RepoRoot -ConfigDir $ConfigDir
    }
    if ($null -ne $mergeOutput) {
        foreach ($line in $mergeOutput) { Write-Host "  merge-config: $line" }
        $configMerged = $true
    } else {
        $configSkipped = $true
    }
} elseif ($WithConfig) {
    # Fresh config from the template, Windows-filtered.
    $templatePath = Join-Path $RepoRoot 'opencode.template.json'
    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        Write-Error "Template missing: $templatePath"
        exit 1
    }
    if ($DryRun) {
        Write-Host ''
        Write-Host 'Config: no opencode.json - would create it from opencode.template.json (macOS-only MCP entries dropped on Windows)'
    } else {
        $parent = Split-Path -Parent $configDest
        if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        $removedMacos = @(Copy-TemplateFilteredWindows -TemplatePath $templatePath -Dest $configDest)
        $configCreated = $true
        Write-Host ''
        Write-Host 'Config: created opencode.json from opencode.template.json'
        if ($removedMacos.Count -gt 0) {
            Write-Host "Config: dropped macOS-only entries: $($removedMacos -join ', ')"
        }
    }
} else {
    Write-Host ''
    Write-Host 'Config: no opencode.json and -WithConfig not given - config left untouched.'
    $configSkipped = $true
}

# --- Execute -----------------------------------------------------------------
if ($DryRun) {
    Write-Host ''
    Write-Host "DryRun complete: $($toInstall.Count) file(s) would be written. Nothing was touched."
    Write-Host 'Would write .supervisor-state.json'
    if (Test-IsWindows) { Write-WindowsMcpNote }
    exit 0
}

$backupRoot = $null
if ($toInstall.Count -gt 0) {
    $existingToReplace = @($toInstall | Where-Object { Test-Path -LiteralPath $_.DestFull -PathType Leaf })
    if ($existingToReplace.Count -gt 0) {
        $backupRoot = New-BackupDir -ConfigDir $ConfigDir -Files $existingToReplace
        Write-Host ''
        Write-Host "Backup: $($existingToReplace.Count) file(s) snapshotted to $backupRoot"
    }
    foreach ($f in $toInstall) {
        $parent = Split-Path -Parent $f.DestFull
        if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        Copy-Item -LiteralPath $f.SourceFull -Destination $f.DestFull -Force
    }
    Write-Host "Installed/updated: $($toInstall.Count) file(s)."
}

# --- State baseline -----------------------------------------------------------
$stateFiles = @()
$stateFiles += $toInstall
$stateFiles += $upToDate
if ($configMerged -or $configCreated) {
    # opencode.json has no repo source of its own; hash the merged result.
    $stateFiles += [pscustomobject]@{ RelPath = 'opencode.json'; SourceFull = ''; DestFull = $configDest }
}
Write-StateFile -ConfigDir $ConfigDir -RepoRoot $RepoRoot -Installer 'setup.ps1' -FileList $stateFiles

# --- Post-install verification ------------------------------------------------
$failCount = 0
Write-Host ''
Write-Host '=== Verification ==='
if (Test-Path -LiteralPath (Join-Path $ConfigDir 'agent\supervisor.md') -PathType Leaf) {
    Write-Host '  verify OK: agent\supervisor.md'
} else {
    Write-Host '  verify FAIL: agent\supervisor.md missing'
    $failCount += 1
}
$expectedAgents = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'agents') -File -Filter '*.md').Count
$actualAgents = @(Get-ChildItem -LiteralPath (Join-Path $ConfigDir 'agents') -File -Filter '*.md' -ErrorAction SilentlyContinue).Count
if ($actualAgents -eq $expectedAgents) {
    Write-Host "  verify OK: agents\ contains $actualAgents files"
} else {
    Write-Host "  verify FAIL: agents\ has $actualAgents files, expected $expectedAgents"
    $failCount += 1
}
$expectedSkills = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'skills') -Directory).Count
$actualSkills = @(Get-ChildItem -LiteralPath (Join-Path $ConfigDir 'skills') -Directory -ErrorAction SilentlyContinue).Count
if ($actualSkills -eq $expectedSkills) {
    Write-Host "  verify OK: skills\ contains $actualSkills skill dirs"
} else {
    Write-Host "  verify FAIL: skills\ has $actualSkills dirs, expected $expectedSkills"
    $failCount += 1
}
if (Test-Path -LiteralPath (Join-Path $ConfigDir 'plugin\observer-bridge.js') -PathType Leaf) {
    Write-Host '  verify OK: plugin\observer-bridge.js'
} else {
    Write-Host '  verify FAIL: plugin\observer-bridge.js missing'
    $failCount += 1
}
if (Test-Path -LiteralPath (Join-Path $ConfigDir 'AGENTS.md') -PathType Leaf) {
    Write-Host '  verify OK: AGENTS.md'
} else {
    Write-Host '  verify FAIL: AGENTS.md missing'
    $failCount += 1
}
if (Test-Path -LiteralPath $configDest -PathType Leaf) {
    try {
        Get-Content -LiteralPath $configDest -Raw | ConvertFrom-Json | Out-Null
        Write-Host '  verify OK: opencode.json is valid JSON'
    } catch {
        Write-Host '  verify FAIL: opencode.json is not valid JSON'
        $failCount += 1
    }
} else {
    Write-Host '  verify SKIP: no opencode.json (pass -WithConfig to add one)'
}
if (Test-Path -LiteralPath (Join-Path $ConfigDir '.supervisor-state.json') -PathType Leaf) {
    Write-Host '  verify OK: .supervisor-state.json'
}

# --- Summary -------------------------------------------------------------------
Write-Host ''
Write-Host '=== Summary ==='
Write-Host "Installed/updated: $($toInstall.Count) file(s)."
if ($toPrompt.Count -gt 0 -and -not $overwriteModified) {
    Write-Host "Skipped (user-modified): $($toPrompt.Count) file(s)."
}
if ($null -ne $backupRoot) { Write-Host "Backup:             $backupRoot" }
Write-Host "State baseline:     $ConfigDir\.supervisor-state.json"
Write-Host ''
Write-Host 'Next steps:'
Write-Host '  1. opencode auth login   (add your DeepSeek key; see PROVIDERS.md)'
Write-Host '  2. opencode               (start working with the supervisor agent)'
Write-Host '  3. setup.ps1 -Doctor      (re-check remaining dependencies)'
Write-Host ''
if (Test-IsWindows) { Write-WindowsMcpNote }
if ($failCount -gt 0) {
    Write-Error "Post-install verification found $failCount problem(s)."
    exit 1
}
Write-Host 'Verification passed.'
exit 0
