$ErrorActionPreference = "Stop"

$bi = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$hooks = Join-Path $bi "src-tauri/windows/hooks.nsh"
$driver = Join-Path $bi "scripts/package-release.ps1"
$releaseGate = Join-Path $bi "scripts/verify-loop-releases.ps1"
$releaseIdentity = Join-Path $bi "release/loop-contract-identities.json"
$workflow = Join-Path (Split-Path (Split-Path $bi -Parent) -Parent) ".github/workflows/release-bi.yml"

if (-not (Test-Path -LiteralPath $hooks -PathType Leaf)) { throw "missing NSIS hooks" }
if (-not (Test-Path -LiteralPath $driver -PathType Leaf)) { throw "missing release driver" }
if (-not (Test-Path -LiteralPath $releaseGate -PathType Leaf)) { throw "missing mechanical Loop release gate" }
if (-not (Test-Path -LiteralPath $releaseIdentity -PathType Leaf)) { throw "missing production Loop release identity contract" }
if (-not (Test-Path -LiteralPath $workflow -PathType Leaf)) { throw "missing formal Windows release workflow" }

$workflowLines = [IO.File]::ReadAllLines($workflow)
$runBlocks = [Collections.Generic.List[string]]::new()
for ($index = 0; $index -lt $workflowLines.Length; $index++) {
    if ($workflowLines[$index] -ne "        run: |") { continue }
    $body = [Collections.Generic.List[string]]::new()
    for ($cursor = $index + 1; $cursor -lt $workflowLines.Length; $cursor++) {
        $line = $workflowLines[$cursor]
        if ($line.Length -eq 0) { $body.Add(""); continue }
        if (-not $line.StartsWith("          ")) { break }
        $body.Add($line.Substring(10))
    }
    $runBlocks.Add(($body -join "`n"))
}
if ($runBlocks.Count -ne 6) { throw "formal workflow must contain exactly six PowerShell run blocks" }
foreach ($block in $runBlocks) {
    $null = [scriptblock]::Create($block)
}

$hookText = [IO.File]::ReadAllText($hooks)
foreach ($marker in @(
    "NSIS_HOOK_POSTINSTALL",
    "NSIS_HOOK_PREUNINSTALL",
    'HKCU "Environment" "Path"',
    'SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE}',
    '!define LCCODING_PATH_STATE_KEY "Software\lccoding\LCCoding BI"',
    '!macro LCCodingDefineUserPathValueExists UNPREFIX',
    'EnumRegValue $R7 HKCU "Environment" $R8',
    '!insertmacro LCCodingDefineUserPathValueExists ""',
    '!insertmacro LCCodingDefineUserPathValueExists "un."',
    'LCCodingPathReadFailure:',
    'LCCodingPathUnreadable:',
    'un.LCCodingPathReadFailure:',
    'un.LCCodingPathUnreadable:',
    'Abort "LCCODING_PATH_INSTALL_READ_FAILED"',
    'Abort "LCCODING_PATH_UNINSTALL_READ_FAILED"',
    'LCCodingPathCapacityExceeded:',
    'Abort "LCCODING_PATH_INSTALL_CAPACITY_FAILED"',
    '"PathTxnActive"',
    '"PathTxnVersion"',
    '"PathTxnPreExists"',
    '"PathTxnPreRaw"',
    '"PathTxnPostRaw"',
    '"PathTxnInstallRoot"',
    "LCCodingPathSnapshot",
    "LCCodingPathStatePreserve",
    "un.LCCodingPathRestoreExact",
    "un.LCCodingPathRemoveCurrentOnly",
    "un.LCCodingRemoveExactInstallRootToken",
    "un.LCCodingPathTransactionCleanup"
)) {
    if (-not $hookText.Contains($marker)) { throw "missing hook marker: $marker" }
}
if ($hookText -match "(?i)\.cmd|HKLM|allUsers|NSIS_MAX_STRLEN|reg\.exe|powershell|Registry::|nsExec::|ExecWait") {
    throw "forbidden installer scope or external PATH mutation dependency"
}
foreach ($forbiddenPathRebuild in @(
    '${UnStrTok}',
    'LCCodingRemoveUserPathLoop',
    'StrCpy $R3 "$R3;$R2"'
)) {
    if ($hookText.Contains($forbiddenPathRebuild)) {
        throw "PATH uninstall must not tokenize and rebuild the full value: $forbiddenPathRebuild"
    }
}
$snapshotAt = $hookText.IndexOf("LCCodingPathSnapshot", [StringComparison]::Ordinal)
$pathWriteAt = $hookText.IndexOf('WriteRegExpandStr HKCU "Environment" "Path"', [StringComparison]::Ordinal)
$postWriteAt = $hookText.IndexOf('WriteRegExpandStr HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnPostRaw"', [StringComparison]::Ordinal)
$activeWriteAt = $hookText.IndexOf('WriteRegDWORD HKCU "${LCCODING_PATH_STATE_KEY}" "PathTxnActive" 1', [StringComparison]::Ordinal)
if ($snapshotAt -lt 0 -or $pathWriteAt -le $snapshotAt -or $postWriteAt -le $pathWriteAt -or $activeWriteAt -le $postWriteAt) {
    throw "PATH transaction must snapshot pre-install bytes, write PATH, then commit post-install bytes and active state"
}
$exactRestoreAt = $hookText.IndexOf("un.LCCodingPathRestoreExact:", [StringComparison]::Ordinal)
$concurrentFallbackAt = $hookText.IndexOf("un.LCCodingPathRemoveCurrentOnly:", [StringComparison]::Ordinal)
$cleanupAt = $hookText.IndexOf("un.LCCodingPathTransactionCleanup:", [StringComparison]::Ordinal)
if ($exactRestoreAt -lt 0 -or $concurrentFallbackAt -le $exactRestoreAt -or $cleanupAt -le $concurrentFallbackAt) {
    throw "uninstall must choose exact restoration or concurrent-safe token removal before transaction cleanup"
}
$exactPostImageCompare = 'StrCmpS $R0 "$R5" un.LCCodingPathRestoreExact un.LCCodingPathRemoveCurrentOnly'
$caseInsensitivePostImageCompare = 'StrCmp $R0 "$R5" un.LCCodingPathRestoreExact un.LCCodingPathRemoveCurrentOnly'
if (-not $hookText.Contains($exactPostImageCompare)) {
    throw "post-install PATH snapshot comparison must be case-sensitive and byte-exact"
}
if ($hookText.Contains($caseInsensitivePostImageCompare)) {
    throw "post-install PATH snapshot comparison must not use case-insensitive StrCmp"
}
$installReadAt = $hookText.IndexOf('ReadRegStr $R0 HKCU "Environment" "Path"', [StringComparison]::Ordinal)
$installClassifyAt = $hookText.IndexOf('IfErrors LCCodingPathReadFailure LCCodingPathPresent', $installReadAt, [StringComparison]::Ordinal)
$installFailureAt = $hookText.IndexOf('LCCodingPathReadFailure:', $installClassifyAt, [StringComparison]::Ordinal)
$installEnumAt = $hookText.IndexOf('Call LCCodingUserPathValueExists', $installFailureAt, [StringComparison]::Ordinal)
$installDispatchAt = $hookText.IndexOf('StrCmp $R9 0 LCCodingPathMissing LCCodingPathUnreadable', $installEnumAt, [StringComparison]::Ordinal)
$installUnreadableAt = $hookText.IndexOf('LCCodingPathUnreadable:', $installDispatchAt, [StringComparison]::Ordinal)
$installAbortAt = $hookText.IndexOf('Abort "LCCODING_PATH_INSTALL_READ_FAILED"', $installUnreadableAt, [StringComparison]::Ordinal)
if ($installReadAt -lt 0 -or $installClassifyAt -le $installReadAt -or $installFailureAt -le $installClassifyAt -or
    $installEnumAt -le $installFailureAt -or $installDispatchAt -le $installEnumAt -or
    $installUnreadableAt -le $installDispatchAt -or $installAbortAt -le $installUnreadableAt -or
    $snapshotAt -le $installAbortAt -or $pathWriteAt -le $installAbortAt) {
    throw "install must distinguish missing PATH from an existing unreadable PATH and abort before mutation"
}
$uninstallReadAt = $hookText.IndexOf('ReadRegStr $R0 HKCU "Environment" "Path"', $installReadAt + 1, [StringComparison]::Ordinal)
$uninstallClassifyAt = $hookText.IndexOf('IfErrors un.LCCodingPathReadFailure un.LCCodingPathPresent', $uninstallReadAt, [StringComparison]::Ordinal)
$uninstallFailureAt = $hookText.IndexOf('un.LCCodingPathReadFailure:', $uninstallClassifyAt, [StringComparison]::Ordinal)
$uninstallEnumAt = $hookText.IndexOf('Call un.LCCodingUserPathValueExists', $uninstallFailureAt, [StringComparison]::Ordinal)
$uninstallDispatchAt = $hookText.IndexOf('StrCmp $R9 0 un.LCCodingPathMissing un.LCCodingPathUnreadable', $uninstallEnumAt, [StringComparison]::Ordinal)
$uninstallUnreadableAt = $hookText.IndexOf('un.LCCodingPathUnreadable:', $uninstallDispatchAt, [StringComparison]::Ordinal)
$uninstallAbortAt = $hookText.IndexOf('Abort "LCCODING_PATH_UNINSTALL_READ_FAILED"', $uninstallUnreadableAt, [StringComparison]::Ordinal)
if ($uninstallReadAt -lt 0 -or $uninstallClassifyAt -le $uninstallReadAt -or
    $uninstallFailureAt -le $uninstallClassifyAt -or $uninstallEnumAt -le $uninstallFailureAt -or
    $uninstallDispatchAt -le $uninstallEnumAt -or $uninstallUnreadableAt -le $uninstallDispatchAt -or
    $uninstallAbortAt -le $uninstallUnreadableAt -or $cleanupAt -le $uninstallAbortAt) {
    throw "uninstall must preserve an existing unreadable PATH and its transaction state"
}
$enumMarker = 'EnumRegValue $R7 HKCU "Environment" $R8'
if (([regex]::Matches($hookText, [regex]::Escape($enumMarker))).Count -ne 1) {
    throw "PATH value-existence classification must use one closed EnumRegValue helper"
}
$appendAt = $hookText.IndexOf('LCCodingPathAppend:', [StringComparison]::Ordinal)
$capacityCompareAt = $hookText.IndexOf(
    'IntCmp $R5 1023 LCCodingPathCapacitySafe LCCodingPathCapacitySafe LCCodingPathCapacityExceeded',
    $appendAt,
    [StringComparison]::Ordinal
)
$capacityExceededAt = $hookText.IndexOf('LCCodingPathCapacityExceeded:', $capacityCompareAt, [StringComparison]::Ordinal)
$capacityAbortAt = $hookText.IndexOf('Abort "LCCODING_PATH_INSTALL_CAPACITY_FAILED"', $capacityExceededAt, [StringComparison]::Ordinal)
$capacitySafeAt = $hookText.IndexOf('LCCodingPathCapacitySafe:', $capacityAbortAt, [StringComparison]::Ordinal)
$appendValueAt = $hookText.IndexOf('StrCpy $R0 "$R0;$INSTDIR"', $capacitySafeAt, [StringComparison]::Ordinal)
if ($appendAt -lt 0 -or $capacityCompareAt -le $appendAt -or $capacityExceededAt -le $capacityCompareAt -or
    $capacityAbortAt -le $capacityExceededAt -or $capacitySafeAt -le $capacityAbortAt -or
    $appendValueAt -le $capacitySafeAt -or $pathWriteAt -le $appendValueAt) {
    throw "PATH append must reject a value that cannot fit in NSIS_MAX_STRLEN before PATH mutation"
}

$driverText = [IO.File]::ReadAllText($driver)
foreach ($marker in @(
    "npm ci --ignore-scripts",
    "tauri build",
    "installer.sha256",
    "provenance.json",
    "CARGO_TARGET_DIR",
    "LCCODING_BI_DIST",
    "verify-loop-releases.ps1",
    "LOCAL_BLOCKED_CANDIDATE",
    "VERIFIED_FORMAL_RELEASES",
    "build_workflow",
    "build_run_id",
    "build_run_attempt",
    "build_run_url",
    "target_triple",
    "loop_release_dependencies",
    "expectedProvenanceKeys",
    "BI_FORMAL_SOURCE_MUST_BE_CLEAN",
    '$releaseInstallerName = "LCCoding-BI_2.8.0_x64-setup.exe"',
    "BI_RELEASE_ASSET_NAME_UNSAFE",
    "stagedTauriRoot",
    'Join-Path $frontend "src-tauri"'
)) {
    if (-not $driverText.Contains($marker)) { throw "missing driver marker: $marker" }
}
if ($driverText.Contains("LCCODING_LOOP_RELEASES_VERIFIED")) {
    throw "formal release gate must not trust an environment assertion"
}
if ($driverText -match 'Push-Location\s+\$bi') {
    throw "Tauri packaging must not run in the source BI tree"
}
if ($driverText.Contains('LCCoding BI_2.8.0_x64-setup.exe')) {
    throw "release installer basename must not contain spaces"
}

$releaseGateText = [IO.File]::ReadAllText($releaseGate)
if ($releaseGateText.Contains("tests/fixtures")) {
    throw "formal release gate must not read a test fixture"
}
foreach ($marker in @(
    "release/loop-contract-identities.json",
    ".execution_methods",
    '$assetSchemaV1 = "LCCODING_BI_COMPATIBILITY_V1"',
    '$assetSchemaV2 = "LCCODING_BI_COMPATIBILITY_V2"',
    "Test-CompatibilityAsset",
    '.status_adapters."2.8.0"',
    '"REAL_PRODUCT_INTEGRATION"',
    '"SUPPORTED_LEGACY"',
    '"CURRENT"',
    '$tag = "v$($identity.version)"',
    "DWG7318/small-loop-skill",
    "DWG7318/chain-loop-skill",
    "DWG7318/large-loop-skill",
    "git/ref/tags",
    "gh release view",
    "manifest_sha256",
    "schema_sha256",
    "template_sha256"
)) {
    if (-not $releaseGateText.Contains($marker)) { throw "missing release gate marker: $marker" }
}
if ([regex]::Matches($releaseGateText, 'release/loop-contract-identities\.json').Count -ne 1) {
    throw "release verifier must consume exactly one compatibility asset path"
}
if ($releaseGateText -match '(?i)(fallback|default).*(candidate_commit|manifest_sha256|schema_sha256|template_sha256)') {
    throw "release verifier must not contain a fallback Loop identity table"
}
if ($releaseGateText.Contains("git/ref/heads/main")) {
    throw "formal release identity must not depend on mutable repository main"
}
foreach ($retired in @(
    'version = "2.5.0"',
    'version = "3.1.0"',
    'tag = "v2.5.0"',
    'tag = "v3.1.0"'
)) {
    if ($releaseGateText.Contains($retired)) { throw "retired release identity: $retired" }
}
if ($releaseGateText -match '(?i)(execution_methods\.)?["'']?calabash["'']?\s*=') {
    throw "Calabash is not a Loop release identity"
}
foreach ($powerShell7Only in @("Text.Json", "HashData", "ToHexString")) {
    if ($releaseGateText.Contains($powerShell7Only)) {
        throw "release verifier must support Windows PowerShell 5.1: $powerShell7Only"
    }
}

Write-Output "PASS: NSIS current-user packaging contract"
