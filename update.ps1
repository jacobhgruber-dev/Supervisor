<#
.SYNOPSIS
    Windows updater for the OpenCode Supervisor workspace.

.DESCRIPTION
    Updates the Supervisor install in %USERPROFILE%\.config\opencode (or
    -ConfigDir) using the same safe 3-way hash classification as setup.ps1,
    driven by the .supervisor-state.json baseline:

      install          - destination missing            -> copied
      managed          - hash matches the baseline      -> updated silently
      modified         - hash differs from the baseline -> NEVER overwritten
                         without a prompt (-Interactive); skipped otherwise
      unmanaged        - exists but not in the baseline -> treated as user-owned
      removed-upstream - baseline file no longer in repo -> left in place

    Every file replaced is snapshotted first into
    <ConfigDir>\backups\supervisor-<timestamp> so it can be restored with
    -Rollback <timestamp>.

    opencode.json:
      - missing      -> created from opencode.template.json (macOS-only MCP
                        entries dropped on Windows)
      - managed      -> merged via node scripts/merge-config.mjs (only
                        subagent_depth, default_agent, plugin and the
                        a11y-color-contrast MCP are ever touched)
      - modified     -> skipped unless -Interactive (merge preserves user edits,
                        but the file is still snapshotted first)
    On Windows, macOS-only MCP servers (macos-use, macos-automator) are never
    registered. Playwright is the universal browser-testing engine.

    If your execution policy blocks this script, run:
        powershell -NoProfile -ExecutionPolicy Bypass -File update.ps1
    or, in PowerShell 7:
        pwsh -NoProfile -ExecutionPolicy Bypass -File update.ps1

.PARAMETER Interactive
    Prompt before touching user-modified files (grouped into a single y/N
    question). Without this switch, modified files are skipped.

.PARAMETER Diff
    Show a per-file diff (git when available) for files that would change.

.PARAMETER OnlyAgents
    Only update the agent files (agent/, agents/, AGENTS.md).

.PARAMETER OnlySkills
    Only update the skills directory.

.PARAMETER OnlyPlugin
    Only update plugin/observer-bridge.js.

.PARAMETER Rollback
    Restore files from <ConfigDir>\backups\supervisor-<timestamp> and refresh
    the state baseline. Combines with nothing else.

.PARAMETER ConfigDir
    Custom config root. Default: %USERPROFILE%\.config\opencode.

.EXAMPLE
    pwsh -NoProfile -File update.ps1

.EXAMPLE
    pwsh -NoProfile -File update.ps1 -Interactive -Diff -OnlyAgents

.EXAMPLE
    pwsh -NoProfile -File update.ps1 -Rollback 20260821-154530
#>
[CmdletBinding()]
param(
    [switch]$Interactive,
    [switch]$Diff,
    [switch]$OnlyAgents,
    [switch]$OnlySkills,
    [switch]$OnlyPlugin,
    [string]$Rollback = '',
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
try {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue | Out-Null
} catch {
    # Ignore; a blocked script would never have started.
}
Write-Verbose 'Execution policy note: if a policy blocks this script, rerun with: powershell -NoProfile -ExecutionPolicy Bypass -File update.ps1'

# --- Platform ------------------------------------------------------------
if (-not (Test-IsWindows)) {
    Write-Warning 'This is the Windows updater and this machine does not look like Windows. Continuing anyway (the file layout is identical).'
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

# --- Rollback ------------------------------------------------------------
if (-not [string]::IsNullOrWhiteSpace($Rollback)) {
    if ($Rollback -match '[\\/]' -or $Rollback -match '\.\.') {
        Write-Error 'Invalid -Rollback timestamp: must be a plain timestamp like 20260821-154530.'
        exit 1
    }
    $backupRoot = Join-Path (Join-Path $ConfigDir 'backups') "supervisor-$Rollback"
    $manifestPath = Join-Path $backupRoot 'manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        Write-Error "No backup manifest found at $manifestPath"
        $backupsDir = Join-Path $ConfigDir 'backups'
        if (Test-Path -LiteralPath $backupsDir) {
            $available = @(Get-ChildItem -LiteralPath $backupsDir -Directory | Select-Object -ExpandProperty Name)
            if ($available.Count -gt 0) { Write-Host "Available snapshots: $($available -join ', ')" }
            else { Write-Host 'No snapshots exist yet.' }
        }
        exit 1
    }
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    } catch {
        Write-Error "Cannot parse $manifestPath : $($_.Exception.Message)"
        exit 1
    }
    $restoreList = @()
    foreach ($p in $manifest.files.PSObject.Properties) {
        $restoreList += [pscustomobject]@{ RelPath = $p.Name; SourceFull = ''; DestFull = (Join-Path $ConfigDir $p.Name) }
    }
    Write-Host ''
    Write-Host "Rollback will restore $($restoreList.Count) file(s) from: $backupRoot"
    foreach ($f in $restoreList) { Write-Host ('  restore  {0}' -f $f.RelPath) }
    if (-not (Confirm-YesNo -Message 'Proceed? Current versions will be overwritten.')) {
        Write-Host 'Rollback cancelled.'
        exit 0
    }
    foreach ($f in $restoreList) {
        $source = Join-Path $backupRoot $f.RelPath
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            Write-Warning "Backup file missing, skipping: $($f.RelPath)"
            continue
        }
        $parent = Split-Path -Parent $f.DestFull
        if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        Copy-Item -LiteralPath $source -Destination $f.DestFull -Force
    }
    Update-StateFileHashes -ConfigDir $ConfigDir -RepoRoot $RepoRoot -Installer 'update.ps1' -FileList $restoreList
    Write-Host ''
    Write-Host "Rollback complete: restored $($restoreList.Count) file(s) from $backupRoot"
    Write-Host "State baseline refreshed: $ConfigDir\.supervisor-state.json"
    exit 0
}

# --- Unit selection --------------------------------------------------------
$unitFilter = @()
if ($OnlyAgents) { $unitFilter += 'agents' }
if ($OnlySkills) { $unitFilter += 'skills' }
if ($OnlyPlugin) { $unitFilter += 'plugin' }
$updateConfig = ($unitFilter.Count -eq 0)   # config merges on full updates only
if ($unitFilter.Count -eq 0) { $unitFilter = $null }

Write-Host ''
Write-Host '=== Supervisor update (Windows) ==='
Write-Host "Repo:     $RepoRoot"
Write-Host "Config:   $ConfigDir"
$scope = 'everything (agents, skills, plugin, config)'
if (-not $updateConfig) { $scope = ($unitFilter -join ', ') }
Write-Host "Scope:    $scope"

# --- Classify ---------------------------------------------------------------
$state = Read-StateFile -ConfigDir $ConfigDir
$classified = @(Get-ClassifiedFiles -RepoRoot $RepoRoot -ConfigDir $ConfigDir -State $state -UnitFilter $unitFilter)

Write-Host ''
Write-Host '=== Update plan ==='
Write-Host ('{0,-16} {1,-36} {2}' -f 'Status', 'File (relative)', 'Detail')
Write-Host ('{0,-16} {1,-36} {2}' -f ('-' * 16), ('-' * 36), ('-' * 24))

$toInstall = @()    # copy new content (new files + changed managed files)
$toPrompt = @()     # modified / unmanaged files that need a decision
$upToDate = @()

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
        'modified'         { $label = '[USER-MODIFIED]'; $detail = 'skipped unless -Interactive'; $toPrompt += $f }
        'unmanaged'        { $label = '[USER FILE]';     $detail = 'not managed; skipped unless -Interactive'; $toPrompt += $f }
        'removed-upstream' { $label = '[LEFT]';          $detail = 'no longer shipped upstream; keeping your file' }
        default            { $label = '[?]';             $detail = 'unknown state' }
    }
    Write-Host ('{0,-16} {1,-36} {2}' -f $label, $f.RelPath, $detail)
}

# --- Diffs (optional) ----------------------------------------------------------
if ($Diff) {
    foreach ($f in $toInstall) {
        if (Test-Path -LiteralPath $f.DestFull -PathType Leaf) {
            Show-FileDiff -Label "$($f.RelPath) (managed update)" -OldPath $f.DestFull -NewPath $f.SourceFull
        }
    }
    foreach ($f in $toPrompt) {
        Show-FileDiff -Label "$($f.RelPath) (user-modified vs repo)" -OldPath $f.DestFull -NewPath $f.SourceFull
    }
}

# --- Decision: user-modified files ----------------------------------------------
$overwriteModified = $false
if ($toPrompt.Count -gt 0) {
    Write-Host ''
    if ($Interactive) {
        $overwriteModified = Confirm-YesNo -Message "$($toPrompt.Count) user-modified file(s) differ from the repo. Overwrite with the repo versions? They will be backed up first."
    } else {
        Write-Host "$($toPrompt.Count) user-modified file(s) skipped (never overwritten without a prompt). Re-run with -Interactive to decide, or keep your versions."
    }
}
if ($overwriteModified) {
    foreach ($f in $toPrompt) { $toInstall += $f }
}

# --- Config (opencode.json) -------------------------------------------------------
$configAction = 'none'   # none | create | merge | skip
$mergeOutput = @()
$configDest = Join-Path $ConfigDir 'opencode.json'

if ($updateConfig) {
    $configExists = Test-Path -LiteralPath $configDest -PathType Leaf
    $configStatus = 'install'
    if ($configExists) {
        $baselineHash = Get-StateHash $state 'opencode.json'
        if ($null -eq $baselineHash) {
            $configStatus = 'unmanaged'
        } elseif ($baselineHash -eq (Get-Sha256 $configDest)) {
            $configStatus = 'managed'
        } else {
            $configStatus = 'modified'
        }
    }
    Write-Host ''
    if ($configStatus -eq 'install') {
        Write-Host 'Config: opencode.json is missing - creating from opencode.template.json (macOS-only MCP entries dropped on Windows)'
        $configAction = 'create'
    } elseif ($configStatus -eq 'managed') {
        Write-Host 'Config: opencode.json is managed - merging template defaults (your settings always win)'
        $configAction = 'merge'
    } else {
        if ($Interactive) {
            $doMerge = Confirm-YesNo -Message 'Config: opencode.json is user-modified. Merge template defaults into it? Your existing settings always win; only missing defaults are added. The file will be snapshotted first.'
            $configAction = if ($doMerge) { 'merge' } else { 'skip' }
        } else {
            Write-Host 'Config: opencode.json is user-modified - skipped. Re-run with -Interactive to merge the template in.'
            $configAction = 'skip'
        }
    }
}

# --- Execute ---------------------------------------------------------------------
if ($toInstall.Count -eq 0 -and $configAction -eq 'none') {
    Write-Host ''
    Write-Host 'Nothing to update: the workspace is up to date.'
    if (Test-IsWindows) { Write-WindowsMcpNote }
    exit 0
}

$backupRoot = $null
$stateFiles = @()

# Snapshot + replace content files.
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
    Write-Host "Updated/installed: $($toInstall.Count) file(s)."
    $stateFiles += $toInstall
}
$stateFiles += $upToDate

# Config.
if ($configAction -eq 'create') {
    $templatePath = Join-Path $RepoRoot 'opencode.template.json'
    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        Write-Error "Template missing: $templatePath"
        exit 1
    }
    $parent = Split-Path -Parent $configDest
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $removedMacos = @(Copy-TemplateFilteredWindows -TemplatePath $templatePath -Dest $configDest)
    Write-Host 'Config: created opencode.json from opencode.template.json'
    if ($removedMacos.Count -gt 0) {
        Write-Host "Config: dropped macOS-only entries: $($removedMacos -join ', ')"
    }
    $stateFiles += [pscustomobject]@{ RelPath = 'opencode.json'; SourceFull = ''; DestFull = $configDest }
} elseif ($configAction -eq 'merge') {
    # Snapshot the current config so -Rollback can restore it.
    $configBackupRoot = New-BackupDir -ConfigDir $ConfigDir -Files @([pscustomobject]@{ RelPath = 'opencode.json'; SourceFull = ''; DestFull = $configDest })
    if ($configBackupRoot -ne $backupRoot) {
        Write-Host "Backup: opencode.json snapshotted to $configBackupRoot"
    }
    $mergeOutput = Invoke-ConfigMerge -RepoRoot $RepoRoot -ConfigDir $ConfigDir
    if ($null -ne $mergeOutput) {
        foreach ($line in $mergeOutput) { Write-Host "  merge-config: $line" }
        $stateFiles += [pscustomobject]@{ RelPath = 'opencode.json'; SourceFull = ''; DestFull = $configDest }
    } else {
        Write-Host 'Config: merge did not run.'
    }
}

# --- State baseline refresh ------------------------------------------------------
Update-StateFileHashes -ConfigDir $ConfigDir -RepoRoot $RepoRoot -Installer 'update.ps1' -FileList $stateFiles

# --- Summary -----------------------------------------------------------------------
Write-Host ''
Write-Host '=== Summary ==='
Write-Host "Updated/installed: $($toInstall.Count) file(s)."
if ($toPrompt.Count -gt 0 -and -not $overwriteModified) {
    Write-Host "Skipped (user-modified): $($toPrompt.Count) file(s) - run update.ps1 -Interactive to decide."
}
if ($null -ne $backupRoot) {
    Write-Host "Backup:             $backupRoot"
    Write-Host "Undo:               update.ps1 -Rollback $($backupRoot | Split-Path -Leaf)"
}
Write-Host "State baseline:     $ConfigDir\.supervisor-state.json"
Write-Host ''
if (Test-IsWindows) { Write-WindowsMcpNote }
exit 0
