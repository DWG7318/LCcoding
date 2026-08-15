[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$bi = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$identityPath = Join-Path $bi "release/loop-contract-identities.json"
$assetSchemaV1 = "LCCODING_BI_COMPATIBILITY_V1"
$assetSchemaV2 = "LCCODING_BI_COMPATIBILITY_V2"

function Stop-ReleaseGate([string]$Reason) {
  throw "BI_LOOP_RELEASE_DEPENDENCY_BLOCKED:$Reason"
}

function Skip-JsonWhitespace($State) {
  while ($State.Index -lt $State.Text.Length) {
    $character = $State.Text[$State.Index]
    if ($character -ne ' ' -and $character -ne "`t" -and $character -ne "`r" -and $character -ne "`n") {
      break
    }
    $State.Index++
  }
}

function Read-JsonString($State) {
  if ($State.Index -ge $State.Text.Length -or $State.Text[$State.Index] -ne '"') {
    throw "JSON string required"
  }
  $State.Index++
  $builder = New-Object Text.StringBuilder
  while ($State.Index -lt $State.Text.Length) {
    $character = $State.Text[$State.Index]
    $State.Index++
    if ($character -eq '"') { return $builder.ToString() }
    if ([int]$character -lt 0x20) { throw "unescaped JSON control character" }
    if ($character -ne '\') {
      $null = $builder.Append($character)
      continue
    }
    if ($State.Index -ge $State.Text.Length) { throw "incomplete JSON escape" }
    $escape = $State.Text[$State.Index]
    $State.Index++
    switch ($escape) {
      '"' { $null = $builder.Append('"') }
      '\' { $null = $builder.Append('\') }
      '/' { $null = $builder.Append('/') }
      'b' { $null = $builder.Append([char]0x08) }
      'f' { $null = $builder.Append([char]0x0c) }
      'n' { $null = $builder.Append([char]0x0a) }
      'r' { $null = $builder.Append([char]0x0d) }
      't' { $null = $builder.Append([char]0x09) }
      'u' {
        if ($State.Index + 4 -gt $State.Text.Length) { throw "incomplete JSON unicode escape" }
        $hex = $State.Text.Substring($State.Index, 4)
        if ($hex -cnotmatch '^[0-9a-fA-F]{4}$') { throw "invalid JSON unicode escape" }
        $State.Index += 4
        $code = [Convert]::ToInt32($hex, 16)
        if ($code -ge 0xd800 -and $code -le 0xdbff) {
          if (
            $State.Index + 6 -gt $State.Text.Length -or
            $State.Text[$State.Index] -ne '\' -or
            $State.Text[$State.Index + 1] -ne 'u'
          ) { throw "missing JSON low surrogate" }
          $lowHex = $State.Text.Substring($State.Index + 2, 4)
          if ($lowHex -cnotmatch '^[0-9a-fA-F]{4}$') { throw "invalid JSON low surrogate" }
          $low = [Convert]::ToInt32($lowHex, 16)
          if ($low -lt 0xdc00 -or $low -gt 0xdfff) { throw "invalid JSON low surrogate" }
          $State.Index += 6
          $null = $builder.Append([char]$code)
          $null = $builder.Append([char]$low)
        } elseif ($code -ge 0xdc00 -and $code -le 0xdfff) {
          throw "unpaired JSON low surrogate"
        } else {
          $null = $builder.Append([char]$code)
        }
      }
      default { throw "invalid JSON escape" }
    }
  }
  throw "unterminated JSON string"
}

function Read-JsonLiteral($State, [string]$Literal) {
  if (
    $State.Index + $Literal.Length -gt $State.Text.Length -or
    [String]::CompareOrdinal($State.Text, $State.Index, $Literal, 0, $Literal.Length) -ne 0
  ) { throw "invalid JSON literal" }
  $State.Index += $Literal.Length
}

function Read-JsonNumber($State) {
  $match = [regex]::Match(
    $State.Text.Substring($State.Index),
    '^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?'
  )
  if (-not $match.Success) { throw "invalid JSON number" }
  $State.Index += $match.Length
}

function Read-JsonObject($State, [int]$Depth) {
  $State.Index++
  Skip-JsonWhitespace $State
  $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  if ($State.Index -lt $State.Text.Length -and $State.Text[$State.Index] -eq '}') {
    $State.Index++
    return
  }
  while ($true) {
    Skip-JsonWhitespace $State
    $name = Read-JsonString $State
    if (-not $names.Add($name)) { throw "duplicate JSON property" }
    Skip-JsonWhitespace $State
    if ($State.Index -ge $State.Text.Length -or $State.Text[$State.Index] -ne ':') {
      throw "missing JSON property separator"
    }
    $State.Index++
    Read-JsonValue $State ($Depth + 1)
    Skip-JsonWhitespace $State
    if ($State.Index -ge $State.Text.Length) { throw "unterminated JSON object" }
    if ($State.Text[$State.Index] -eq '}') {
      $State.Index++
      return
    }
    if ($State.Text[$State.Index] -ne ',') { throw "invalid JSON object separator" }
    $State.Index++
  }
}

function Read-JsonArray($State, [int]$Depth) {
  $State.Index++
  Skip-JsonWhitespace $State
  if ($State.Index -lt $State.Text.Length -and $State.Text[$State.Index] -eq ']') {
    $State.Index++
    return
  }
  while ($true) {
    Read-JsonValue $State ($Depth + 1)
    Skip-JsonWhitespace $State
    if ($State.Index -ge $State.Text.Length) { throw "unterminated JSON array" }
    if ($State.Text[$State.Index] -eq ']') {
      $State.Index++
      return
    }
    if ($State.Text[$State.Index] -ne ',') { throw "invalid JSON array separator" }
    $State.Index++
  }
}

function Read-JsonValue($State, [int]$Depth) {
  if ($Depth -gt 64) { throw "JSON nesting limit" }
  Skip-JsonWhitespace $State
  if ($State.Index -ge $State.Text.Length) { throw "missing JSON value" }
  $character = $State.Text[$State.Index]
  if ($character -eq '{') { Read-JsonObject $State $Depth }
  elseif ($character -eq '[') { Read-JsonArray $State $Depth }
  elseif ($character -eq '"') { $null = Read-JsonString $State }
  elseif ($character -eq 't') { Read-JsonLiteral $State 'true' }
  elseif ($character -eq 'f') { Read-JsonLiteral $State 'false' }
  elseif ($character -eq 'n') { Read-JsonLiteral $State 'null' }
  else { Read-JsonNumber $State }
}

function Assert-UniqueJsonProperties([string]$Raw) {
  $state = [pscustomobject]@{ Text = $Raw; Index = 0 }
  Read-JsonValue $state 0
  Skip-JsonWhitespace $state
  if ($state.Index -ne $state.Text.Length) { throw "trailing JSON data" }
}

function Read-StrictJson([string]$Path) {
  try {
    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -eq 0 -or $bytes.Length -gt 1048576) { throw "invalid JSON size" }
    $encoding = New-Object Text.UTF8Encoding($false, $true)
    $raw = $encoding.GetString($bytes)
    Assert-UniqueJsonProperties $raw
    return ($raw | ConvertFrom-Json)
  } catch {
    Stop-ReleaseGate "IDENTITY_RECORD"
  }
}

function Test-ExactKeys($Record, [string[]]$Expected) {
  if ($null -eq $Record -or $Record -isnot [pscustomobject]) { return $false }
  $actual = @($Record.PSObject.Properties.Name)
  if ($actual.Count -ne $Expected.Count) { return $false }
  $expectedNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  foreach ($name in $Expected) { $null = $expectedNames.Add($name) }
  foreach ($name in $actual) { if (-not $expectedNames.Contains($name)) { return $false } }
  return $true
}

function Test-ClosedStringArray($Value, [int]$ExpectedCount) {
  if ($Value -isnot [Array] -or $Value.Count -ne $ExpectedCount) { return $false }
  $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  foreach ($item in $Value) {
    if ($item -isnot [string] -or -not $item -or -not $seen.Add($item)) { return $false }
  }
  return $true
}

function Test-StatusAdapter(
  $Adapter,
  [string]$Version,
  [string]$Status,
  [string]$Minimum,
  [string]$IntegrationPhase,
  [int[]]$ExpectedCounts,
  [string]$ExpectedLayoutSha256
) {
  if (-not (Test-ExactKeys $Adapter @(
    "status_schema_version", "compatibility_status", "minimum_bi_version", "phase_steps"
  ))) { return $false }
  if (
    $Adapter.status_schema_version -cne $Version -or
    $Adapter.compatibility_status -cne $Status -or
    $Adapter.minimum_bi_version -cne $Minimum -or
    -not (Test-ExactKeys $Adapter.phase_steps @(
      "INITIAL", "PRODUCT_FORMATION", $IntegrationPhase, "DELIVERY_PREPARATION"
    ))
  ) { return $false }
  $phaseNames = @("INITIAL", "PRODUCT_FORMATION", $IntegrationPhase, "DELIVERY_PREPARATION")
  $layout = [Collections.Generic.List[string]]::new()
  $allSteps = [Collections.Generic.List[string]]::new()
  for ($phaseIndex = 0; $phaseIndex -lt $phaseNames.Count; $phaseIndex++) {
    $phase = $phaseNames[$phaseIndex]
    $steps = $Adapter.phase_steps.$phase
    if ($steps -isnot [Array] -or $steps.Count -ne $ExpectedCounts[$phaseIndex]) { return $false }
    $layout.Add($phase)
    foreach ($step in $steps) {
      if ($step -isnot [string] -or $step -cnotmatch "^[A-Z][A-Z0-9_]{0,95}$") { return $false }
      $layout.Add($step)
      $allSteps.Add($step)
    }
  }
  if (-not (Test-ClosedStringArray $allSteps.ToArray() 21)) { return $false }
  $sha256 = [Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes([string]::Join("`n", $layout.ToArray()))
    $actualLayoutSha256 = ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
  } finally {
    $sha256.Dispose()
  }
  return $actualLayoutSha256 -ceq $ExpectedLayoutSha256
}

function Test-ExecutionMethod($Identity, [string]$Kind) {
  $mapping = @(
    "worker_checker_wake", "supervisor_wait", "heartbeat", "no_subagents",
    "progress", "cell_capacity", "pin_policy"
  )
  if (-not (Test-ExactKeys $Identity @(
    "version", "compatibility_status", "minimum_bi_version", "adapter_schema_kind",
    "normalization_mapping", "candidate_commit", "manifest_sha256", "schema_sha256",
    "template_sha256"
  ))) { return $false }
  if (
    [string]$Identity.version -cnotmatch "^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$" -or
    $Identity.compatibility_status -cne "CURRENT" -or
    $Identity.minimum_bi_version -cne "2.6.0" -or
    $Identity.adapter_schema_kind -cne $Kind -or
    [string]$Identity.candidate_commit -cnotmatch "^[0-9a-f]{40}$"
  ) { return $false }
  if (-not (Test-ClosedStringArray $Identity.normalization_mapping 7)) { return $false }
  for ($index = 0; $index -lt $mapping.Count; $index++) {
    if ($Identity.normalization_mapping[$index] -cne $mapping[$index]) { return $false }
  }
  foreach ($hashField in @("manifest_sha256", "schema_sha256", "template_sha256")) {
    if ([string]$Identity.$hashField -cnotmatch "^[0-9a-f]{64}$") { return $false }
  }
  return $true
}

function Test-CompatibilityAsset($Identities) {
  $layout260 = "ddaf4c42505ed83196d96c8a3afd9e37907e352c61a1de901aac22202d48d1dd"
  $layout270 = "908c0cf60c93830e178508e9750298820638aa24349f8f9a51f0566ab17eb71f"
  $layout280 = "9816495f048cb64565f30af7f3802509e04d4b890c1d1f6dd97554db055f468b"
  if (
    -not (Test-ExactKeys $Identities @("asset_schema", "status_adapters", "execution_methods")) -or
    -not (Test-ExactKeys $Identities.execution_methods @("slk", "clk", "glk")) -or
    -not (Test-ExecutionMethod $Identities.execution_methods.slk "SLK_RUN_RUNTIME_INDEX") -or
    -not (Test-ExecutionMethod $Identities.execution_methods.clk "CLK_RUN_CONTROL_TRACE") -or
    -not (Test-ExecutionMethod $Identities.execution_methods.glk "GLK_RUN_PACKAGE_INDEX")
  ) { return $false }
  if ($Identities.asset_schema -ceq $assetSchemaV1) {
    return (
      (Test-ExactKeys $Identities.status_adapters @("2.6.0", "2.7.0")) -and
      (Test-StatusAdapter $Identities.status_adapters."2.6.0" "2.6.0" "SUPPORTED_LEGACY" "2.6.0" "ENGINEERING_RUNS" @(3, 5, 7, 6) $layout260) -and
      (Test-StatusAdapter $Identities.status_adapters."2.7.0" "2.7.0" "CURRENT" "2.7.0" "ENGINEERING_RUNS" @(3, 7, 5, 6) $layout270)
    )
  }
  if ($Identities.asset_schema -ceq $assetSchemaV2) {
    return (
      (Test-ExactKeys $Identities.status_adapters @("2.6.0", "2.7.0", "2.8.0")) -and
      (Test-StatusAdapter $Identities.status_adapters."2.6.0" "2.6.0" "SUPPORTED_LEGACY" "2.6.0" "ENGINEERING_RUNS" @(3, 5, 7, 6) $layout260) -and
      (Test-StatusAdapter $Identities.status_adapters."2.7.0" "2.7.0" "SUPPORTED_LEGACY" "2.7.0" "ENGINEERING_RUNS" @(3, 7, 5, 6) $layout270) -and
      (Test-StatusAdapter $Identities.status_adapters."2.8.0" "2.8.0" "CURRENT" "2.8.0" "REAL_PRODUCT_INTEGRATION" @(3, 7, 5, 6) $layout280)
    )
  }
  return $false
}

function Invoke-GhApi([string]$Endpoint) {
  $raw = & gh api $Endpoint 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $raw) { Stop-ReleaseGate "GITHUB_API" }
  try {
    return ($raw | ConvertFrom-Json)
  } catch {
    Stop-ReleaseGate "GITHUB_RESPONSE"
  }
}

function Resolve-TagCommit([string]$Repository, [string]$Tag) {
  $reference = Invoke-GhApi "repos/$Repository/git/ref/tags/$Tag"
  $type = [string]$reference.object.type
  $sha = [string]$reference.object.sha
  for ($depth = 0; $depth -lt 3 -and $type -ceq "tag"; $depth++) {
    $tagObject = Invoke-GhApi "repos/$Repository/git/tags/$sha"
    $type = [string]$tagObject.object.type
    $sha = [string]$tagObject.object.sha
  }
  if ($type -cne "commit" -or $sha -cnotmatch "^[0-9a-f]{40}$") {
    Stop-ReleaseGate "TAG_COMMIT"
  }
  return $sha
}

function Get-ReleaseFileHash(
  [string]$Repository,
  [string]$Commit,
  [string]$Path
) {
  $record = Invoke-GhApi ("repos/" + $Repository + "/contents/" + $Path + "?ref=" + $Commit)
  if ($record.type -cne "file" -or $record.encoding -cne "base64" -or -not $record.content) {
    Stop-ReleaseGate "RELEASE_FILE"
  }
  try {
    $bytes = [Convert]::FromBase64String(([string]$record.content -replace "\s", ""))
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
      return ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
    } finally {
      $sha256.Dispose()
    }
  } catch {
    Stop-ReleaseGate "RELEASE_FILE_HASH"
  }
}

if (-not (Test-Path -LiteralPath $identityPath -PathType Leaf)) {
  Stop-ReleaseGate "IDENTITY_FILE"
}
$identities = Read-StrictJson $identityPath
if (-not (Test-CompatibilityAsset $identities)) {
  Stop-ReleaseGate "IDENTITY_RECORD"
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Stop-ReleaseGate "GH_UNAVAILABLE"
}

$contracts = [ordered]@{
  slk = [ordered]@{
    repository = "DWG7318/small-loop-skill"
    manifest_path = "MANIFEST.json"
    schema_path = "small-loop-skill/contracts/slk-runtime-control.schema.json"
    template_path = "small-loop-skill/templates/run-runtime-index.yaml"
  }
  clk = [ordered]@{
    repository = "DWG7318/chain-loop-skill"
    manifest_path = "MANIFEST.json"
    schema_path = "chain-loop-skill/schemas/run-control-trace.schema.json"
    template_path = "chain-loop-skill/templates/run-control-trace.yaml"
  }
  glk = [ordered]@{
    repository = "DWG7318/large-loop-skill"
    manifest_path = "MANIFEST.json"
    schema_path = "glk/schemas/glk.schema.json"
    template_path = "glk/templates/RUN_PACKAGE_INDEX.yaml"
  }
}

$verified = [ordered]@{}
foreach ($method in $contracts.Keys) {
  $contract = $contracts[$method]
  $identity = $identities.execution_methods.$method
  $tag = "v$($identity.version)"

  $tagCommit = Resolve-TagCommit $contract.repository $tag

  # gh release view is required in addition to refs: a tag alone is not a formal Release.
  $releaseRaw = & gh release view $tag -R $contract.repository --json tagName,isDraft,isPrerelease,publishedAt,url 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $releaseRaw) {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_RELEASE"
  }
  try {
    $release = $releaseRaw | ConvertFrom-Json
  } catch {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_RELEASE_RESPONSE"
  }

  if (
    $tagCommit -cne $identity.candidate_commit -or
    $release.tagName -cne $tag -or
    $release.isDraft -ne $false -or
    $release.isPrerelease -ne $false -or
    -not $release.publishedAt
  ) {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_RELEASE_IDENTITY"
  }

  $actualHashes = [ordered]@{
    manifest_sha256 = Get-ReleaseFileHash $contract.repository $tagCommit $contract.manifest_path
    schema_sha256 = Get-ReleaseFileHash $contract.repository $tagCommit $contract.schema_path
    template_sha256 = Get-ReleaseFileHash $contract.repository $tagCommit $contract.template_path
  }
  foreach ($hashField in $actualHashes.Keys) {
    if ($actualHashes[$hashField] -cne [string]$identity.$hashField) {
      Stop-ReleaseGate "$($method.ToUpperInvariant())_$($hashField.ToUpperInvariant())"
    }
  }

  $verified[$method] = [ordered]@{
    repository = $contract.repository
    version = $identity.version
    tag = $tag
    commit = $tagCommit
    release_url = [string]$release.url
    manifest_sha256 = $actualHashes.manifest_sha256
    schema_sha256 = $actualHashes.schema_sha256
    template_sha256 = $actualHashes.template_sha256
  }
}

[pscustomobject]@{
  status = "VERIFIED_FORMAL_RELEASES"
  methods = [pscustomobject]$verified
}
