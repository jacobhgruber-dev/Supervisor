# scripts/supervisor-install-common.ps1
# Shared helpers for setup.ps1 and update.ps1. Do not run directly.
#
# Compatibility: Windows PowerShell 5.1 and PowerShell 7+.
# - ASCII only (PS 5.1 parses BOM-less files as ANSI; ASCII is identical in UTF-8).
# - No ternary/null-coalescing/null-conditional operators (PS 7 only).
# - No -Encoding utf8NoBom (PS 7 only); UTF-8 no-BOM writes use .NET directly.
#
# Both installers dot-source this file so they share the exact same hashing,
# classification, backup and state-file logic. The state file format matches
# install.sh (.supervisor-state.json: schema_version / installed_at / source /
# files -> { sha256 }).

function Test-IsWindows {
    # $IsWindows exists only in PowerShell 6+; $env:OS works everywhere.
    return ($env:OS -eq 'Windows_NT')
}

function Get-Sha256 {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-StateHash {
    # Baseline hash recorded in .supervisor-state.json for a relative path.
    param($State, [string]$RelPath)
    if ($null -eq $State) { return $null }
    $files = $State.files
    if ($null -eq $files) { return $null }
    $entry = $files.PSObject.Properties | Where-Object { $_.Name -eq $RelPath } | Select-Object -First 1
    if ($null -eq $entry) { return $null }
    return [string]$entry.Value.sha256
}

function Get-RepoFiles {
    # Enumerates every managed file shipped by this repo, mapped to its
    # install-relative path under the config dir. Returns objects:
    #   Id (unit), RelPath (posix separators), SourceFull
    param([string]$RepoRoot, [string[]]$UnitFilter)
    $units = @(
        @{ Id = 'agents'; SrcDir = (Join-Path $RepoRoot 'agent');  DestRel = 'agent';  Pattern = '*.md'; Recurse = $true },
        @{ Id = 'agents'; SrcDir = (Join-Path $RepoRoot 'agents'); DestRel = 'agents'; Pattern = '*.md'; Recurse = $true },
        @{ Id = 'agents'; SrcDir = $RepoRoot;                      DestRel = '';       Pattern = 'AGENTS.md'; Recurse = $false },
        @{ Id = 'skills'; SrcDir = (Join-Path $RepoRoot 'skills'); DestRel = 'skills'; Pattern = '*'; Recurse = $true },
        @{ Id = 'plugin'; SrcDir = (Join-Path $RepoRoot 'plugin'); DestRel = 'plugin'; Pattern = 'observer-bridge.js'; Recurse = $false }
    )
    $files = @()
    foreach ($u in $units) {
        if ($null -ne $UnitFilter -and ($UnitFilter -notcontains $u.Id)) { continue }
        if (-not (Test-Path -LiteralPath $u.SrcDir)) { continue }
        $items = @()
        if ($u.Recurse) {
            $items = @(Get-ChildItem -LiteralPath $u.SrcDir -Recurse -File -Filter $u.Pattern)
        } else {
            $items = @(Get-ChildItem -LiteralPath $u.SrcDir -File -Filter $u.Pattern)
        }
        foreach ($item in $items) {
            if ($item.Name -eq '.DS_Store') { continue }
            $rel = $item.Name
            if ($u.DestRel) {
                if ($item.FullName.Length -gt $u.SrcDir.Length + 1) {
                    $sub = $item.FullName.Substring($u.SrcDir.Length + 1)
                    $rel = Join-Path $u.DestRel $sub
                } else {
                    $rel = Join-Path $u.DestRel $item.Name
                }
            }
            $files += [pscustomobject]@{
                Id = $u.Id
                RelPath = $rel.Replace('\', '/')
                SourceFull = $item.FullName
            }
        }
    }
    return $files
}

function Get-ClassifiedFiles {
    # 3-way hash classification of every managed repo file against the config dir.
    # Status values:
    #   install          - destination missing, safe to install
    #   managed          - destination hash matches the recorded baseline (ours)
    #   modified         - destination hash differs from the baseline (user edited)
    #   unmanaged        - destination exists but has no baseline entry (user file)
    #   removed-upstream - in the baseline but no longer shipped by the repo
    param([string]$RepoRoot, [string]$ConfigDir, $State, [string[]]$UnitFilter)
    $repoFiles = @(Get-RepoFiles -RepoRoot $RepoRoot -UnitFilter $UnitFilter)
    $classified = @()
    foreach ($f in $repoFiles) {
        $dest = Join-Path $ConfigDir $f.RelPath
        $exists = Test-Path -LiteralPath $dest -PathType Leaf
        $currentHash = $null
        if ($exists) { $currentHash = Get-Sha256 $dest }
        $baselineHash = Get-StateHash $State $f.RelPath
        $status = 'install'
        if ($exists) {
            if ($null -ne $baselineHash) {
                if ($baselineHash -eq $currentHash) { $status = 'managed' } else { $status = 'modified' }
            } else {
                $status = 'unmanaged'
            }
        }
        $classified += [pscustomobject]@{
            Id = $f.Id
            RelPath = $f.RelPath
            SourceFull = $f.SourceFull
            DestFull = $dest
            Status = $status
            SourceHash = Get-Sha256 $f.SourceFull
            CurrentHash = $currentHash
            BaselineHash = $baselineHash
        }
    }
    $repoRels = @{}
    foreach ($c in $classified) { $repoRels[$c.RelPath] = $true }
    if ($null -ne $State -and $null -ne $State.files) {
        foreach ($p in $State.files.PSObject.Properties) {
            if (-not $repoRels.ContainsKey($p.Name)) {
                $classified += [pscustomobject]@{
                    Id = ''
                    RelPath = $p.Name
                    SourceFull = ''
                    DestFull = (Join-Path $ConfigDir $p.Name)
                    Status = 'removed-upstream'
                    SourceHash = $null
                    CurrentHash = $null
                    BaselineHash = $null
                }
            }
        }
    }
    return $classified
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

function Read-StateFile {
    param([string]$ConfigDir)
    $statePath = Join-Path $ConfigDir '.supervisor-state.json'
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { return $null }
    try {
        return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
    } catch {
        Write-Warning "Could not parse $statePath ($($_.Exception.Message)); treating as no baseline."
        return $null
    }
}

function Get-UtcTimestamp {
    return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
}

function Write-StateFile {
    # Fresh baseline. Hashes SOURCE repo files (matching install.sh semantics);
    # entries without a SourceFull (e.g. merged opencode.json) hash the dest.
    param([string]$ConfigDir, [string]$RepoRoot, [string]$Installer, $FileList)
    $files = [ordered]@{}
    foreach ($f in $FileList) {
        $hashPath = $f.SourceFull
        if ([string]::IsNullOrWhiteSpace($hashPath)) { $hashPath = $f.DestFull }
        if ([string]::IsNullOrWhiteSpace($hashPath)) { continue }
        if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) { continue }
        $files[$f.RelPath] = [ordered]@{ sha256 = (Get-Sha256 $hashPath) }
    }
    $state = [ordered]@{
        schema_version = 1
        installed_at = (Get-UtcTimestamp)
        source = $RepoRoot
        files = $files
    }
    Write-Utf8NoBom -Path (Join-Path $ConfigDir '.supervisor-state.json') -Text ((ConvertTo-Json -Depth 10 $state) + "`n")
}

function Update-StateFileHashes {
    # Refresh baseline hashes for the given files, preserving all other
    # entries. Entries whose hash path no longer exists are removed.
    param([string]$ConfigDir, [string]$RepoRoot, [string]$Installer, $FileList)
    $state = Read-StateFile -ConfigDir $ConfigDir
    $files = [ordered]@{}
    if ($null -ne $state -and $null -ne $state.files) {
        foreach ($p in $state.files.PSObject.Properties) { $files[$p.Name] = $p.Value }
    }
    foreach ($f in $FileList) {
        $hashPath = $f.SourceFull
        if ([string]::IsNullOrWhiteSpace($hashPath)) { $hashPath = $f.DestFull }
        if ([string]::IsNullOrWhiteSpace($hashPath)) { continue }
        if (Test-Path -LiteralPath $hashPath -PathType Leaf) {
            $files[$f.RelPath] = [ordered]@{ sha256 = (Get-Sha256 $hashPath) }
        } elseif ($files.Contains($f.RelPath)) {
            $files.Remove($f.RelPath)
        }
    }
    $newState = [ordered]@{
        schema_version = 1
        installed_at = (Get-UtcTimestamp)
        source = $RepoRoot
        files = $files
    }
    Write-Utf8NoBom -Path (Join-Path $ConfigDir '.supervisor-state.json') -Text ((ConvertTo-Json -Depth 10 $newState) + "`n")
}

function New-BackupDir {
    # Snapshots every existing destination in $Files into
    # <ConfigDir>\backups\supervisor-<timestamp> with a manifest.json.
    # Returns the backup root path.
    param([string]$ConfigDir, $Files)
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupRoot = Join-Path (Join-Path $ConfigDir 'backups') "supervisor-$timestamp"
    $manifest = [ordered]@{ version = 1; createdAt = (Get-Date).ToString('o'); files = [ordered]@{} }
    foreach ($f in $Files) {
        if ($null -eq $f.DestFull) { continue }
        if (-not (Test-Path -LiteralPath $f.DestFull -PathType Leaf)) { continue }
        $backupDest = Join-Path $backupRoot $f.RelPath
        $parent = Split-Path -Parent $backupDest
        if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        Copy-Item -LiteralPath $f.DestFull -Destination $backupDest
        $manifest.files[$f.RelPath] = [ordered]@{
            hash = (Get-Sha256 $f.DestFull)
            bytes = (Get-Item -LiteralPath $f.DestFull).Length
        }
    }
    if ($manifest.files.Count -gt 0) {
        Write-Utf8NoBom -Path (Join-Path $backupRoot 'manifest.json') -Text ((ConvertTo-Json -Depth 10 $manifest) + "`n")
    }
    return $backupRoot
}

function Confirm-YesNo {
    param([string]$Message, [switch]$DefaultYes)
    $suffix = ' [y/N]'
    if ($DefaultYes) { $suffix = ' [Y/n]' }
    try {
        $answer = Read-Host ($Message + $suffix)
    } catch {
        return [bool]$DefaultYes
    }
    if ([string]::IsNullOrWhiteSpace($answer)) { return [bool]$DefaultYes }
    return ($answer.Trim().ToLowerInvariant() -in @('y', 'yes'))
}

function Show-FileDiff {
    # Prefers git for a real unified diff; falls back to a line comparison.
    param([string]$Label, [string]$OldPath, [string]$NewPath)
    Write-Host ''
    Write-Host "--- diff: $Label ---"
    $oldExists = Test-Path -LiteralPath $OldPath -PathType Leaf
    $newExists = Test-Path -LiteralPath $NewPath -PathType Leaf
    if ($oldExists -and $newExists) {
        $git = Get-Command git -ErrorAction SilentlyContinue
        if ($git) {
            $diffText = (& git --no-pager diff --no-index -- $OldPath $NewPath 2>&1 | Out-String).TrimEnd()
            if (-not [string]::IsNullOrWhiteSpace($diffText)) {
                Write-Host $diffText
            } else {
                Write-Host '(no textual diff)'
            }
            return
        }
        $lines = @(Compare-Object (Get-Content -LiteralPath $OldPath) (Get-Content -LiteralPath $NewPath) | Select-Object -First 40)
        if ($lines.Count -eq 0) {
            Write-Host '(no textual diff)'
        } else {
            foreach ($line in $lines) {
                if ($line.SideIndicator -eq '<=') { Write-Host ('- ' + $line.InputObject) }
                else { Write-Host ('+ ' + $line.InputObject) }
            }
        }
    } else {
        Write-Host "(new file: $NewPath)"
    }
}

function Invoke-ConfigMerge {
    # Runs the canonical node merge helper: node scripts/merge-config.mjs
    # [--dry-run] <target>. It only ever touches four keys (subagent_depth,
    # default_agent, plugin, mcp.a11y-color-contrast); everything else is
    # preserved. Returns the captured output lines (array of strings) or
    # $null when the invocation could not even start.
    param([string]$RepoRoot, [string]$ConfigDir, [switch]$Dry)
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        if ($Dry) {
            Write-Host '  would run: node scripts/merge-config.mjs --dry-run opencode.json (Node.js is not installed - get it with: winget install OpenJS.NodeJS.LTS)'
            return $null
        }
        Write-Error 'Node.js is required to merge the config. Install it with: winget install OpenJS.NodeJS.LTS'
        return $null
    }
    $mergeScript = Join-Path $RepoRoot 'scripts\merge-config.mjs'
    if (-not (Test-Path -LiteralPath $mergeScript -PathType Leaf)) {
        Write-Error "Missing merge helper: $mergeScript"
        return $null
    }
    $configDest = Join-Path $ConfigDir 'opencode.json'
    $nodeArgs = @($mergeScript)
    if ($Dry) { $nodeArgs += '--dry-run' }
    $nodeArgs += $configDest
    $raw = (& node @nodeArgs 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Write-Error "merge-config.mjs failed (exit $LASTEXITCODE): $raw"
        return $null
    }
    return @($raw -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Copy-TemplateFilteredWindows {
    # Creates <Dest> from <TemplatePath> with the macOS-only MCP entries
    # (macos-use, macos-automator) and their permission keys removed.
    # Playwright stays - it is the universal browser-testing engine.
    # Returns the list of removed entries.
    param([string]$TemplatePath, [string]$Dest)
    try {
        $cfg = Get-Content -LiteralPath $TemplatePath -Raw | ConvertFrom-Json
    } catch {
        Write-Error "Cannot parse template $TemplatePath : $($_.Exception.Message)"
        return $null
    }
    $removed = @()
    if ($null -ne $cfg.mcp) {
        foreach ($name in @('macos-use', 'macos-automator')) {
            $prop = $cfg.mcp.PSObject.Properties | Where-Object { $_.Name -eq $name } | Select-Object -First 1
            if ($null -ne $prop) {
                $cfg.mcp.PSObject.Properties.Remove($name) | Out-Null
                $removed += "mcp.$name"
            }
        }
    }
    $permissionBlocks = @()
    if ($null -ne $cfg.permission) { $permissionBlocks += ,@($cfg.permission, 'permission') }
    if ($null -ne $cfg.agent) {
        foreach ($agentProp in $cfg.agent.PSObject.Properties) {
            $agentObj = $agentProp.Value
            if ($null -ne $agentObj -and $null -ne $agentObj.permission) {
                $permissionBlocks += ,@($agentObj.permission, "agent.$($agentProp.Name).permission")
            }
        }
    }
    foreach ($block in $permissionBlocks) {
        $perm = $block[0]
        $prefix = $block[1]
        $toRemove = @($perm.PSObject.Properties | Where-Object {
            $_.Name -eq 'macos-use' -or $_.Name -eq 'macos-automator' -or
            $_.Name -like 'macos-use_*' -or $_.Name -like 'macos-automator_*'
        })
        foreach ($prop in $toRemove) {
            $perm.PSObject.Properties.Remove($prop.Name) | Out-Null
            $removed += "$prefix.$($prop.Name)"
        }
    }
    $json = (ConvertTo-Json -Depth 32 $cfg) + "`n"
    Write-Utf8NoBom -Path $Dest -Text $json
    return $removed
}

function Write-WindowsMcpNote {
    Write-Host 'Windows note: macOS-only MCP servers (macos-use, macos-automator) are not registered. Playwright is the universal browser-testing engine.'
}
