[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$bi = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$identityPath = Join-Path $bi "release/loop-contract-identities.json"

function Stop-ReleaseGate([string]$Reason) {
  throw "BI_LOOP_RELEASE_DEPENDENCY_BLOCKED:$Reason"
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
  for ($depth = 0; $depth -lt 3 -and $type -eq "tag"; $depth++) {
    $tagObject = Invoke-GhApi "repos/$Repository/git/tags/$sha"
    $type = [string]$tagObject.object.type
    $sha = [string]$tagObject.object.sha
  }
  if ($type -ne "commit" -or $sha -notmatch "^[0-9a-f]{40}$") {
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
  if ($record.type -ne "file" -or $record.encoding -ne "base64" -or -not $record.content) {
    Stop-ReleaseGate "RELEASE_FILE"
  }
  try {
    $bytes = [Convert]::FromBase64String(([string]$record.content -replace "\s", ""))
    return [Convert]::ToHexString(
      [Security.Cryptography.SHA256]::HashData($bytes)
    ).ToLowerInvariant()
  } catch {
    Stop-ReleaseGate "RELEASE_FILE_HASH"
  }
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Stop-ReleaseGate "GH_UNAVAILABLE"
}
if (-not (Test-Path -LiteralPath $identityPath -PathType Leaf)) {
  Stop-ReleaseGate "IDENTITY_FILE"
}

try {
  $identities = [IO.File]::ReadAllText($identityPath) | ConvertFrom-Json
} catch {
  Stop-ReleaseGate "IDENTITY_RECORD"
}

$contracts = [ordered]@{
  slk = [ordered]@{
    repository = "DWG7318/small-loop-skill"
    version = "2.5.0"
    tag = "v2.5.0"
    manifest_path = "MANIFEST.json"
    schema_path = "small-loop-skill/contracts/slk-runtime-control.schema.json"
    template_path = "small-loop-skill/templates/run-runtime-index.yaml"
  }
  clk = [ordered]@{
    repository = "DWG7318/chain-loop-skill"
    version = "2.5.0"
    tag = "v2.5.0"
    manifest_path = "MANIFEST.json"
    schema_path = "chain-loop-skill/schemas/run-control-trace.schema.json"
    template_path = "chain-loop-skill/templates/run-control-trace.yaml"
  }
  glk = [ordered]@{
    repository = "DWG7318/large-loop-skill"
    version = "3.1.0"
    tag = "v3.1.0"
    manifest_path = "MANIFEST.json"
    schema_path = "glk/schemas/glk.schema.json"
    template_path = "glk/templates/RUN_PACKAGE_INDEX.yaml"
  }
}

$verified = [ordered]@{}
foreach ($method in $contracts.Keys) {
  $contract = $contracts[$method]
  $identity = $identities.$method
  if (
    $null -eq $identity -or
    $identity.version -ne $contract.version -or
    $identity.candidate_commit -notmatch "^[0-9a-f]{40}$"
  ) {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_IDENTITY"
  }
  foreach ($hashField in @("manifest_sha256", "schema_sha256", "template_sha256")) {
    if ([string]$identity.$hashField -notmatch "^[0-9a-f]{64}$") {
      Stop-ReleaseGate "$($method.ToUpperInvariant())_HASH_IDENTITY"
    }
  }

  $main = Invoke-GhApi "repos/$($contract.repository)/git/ref/heads/main"
  $mainCommit = [string]$main.object.sha
  $tagCommit = Resolve-TagCommit $contract.repository $contract.tag

  # gh release view is required in addition to refs: a tag alone is not a formal Release.
  $releaseRaw = & gh release view $contract.tag -R $contract.repository --json tagName,isDraft,isPrerelease,publishedAt,url 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $releaseRaw) {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_RELEASE"
  }
  try {
    $release = $releaseRaw | ConvertFrom-Json
  } catch {
    Stop-ReleaseGate "$($method.ToUpperInvariant())_RELEASE_RESPONSE"
  }

  if (
    $mainCommit -ne $identity.candidate_commit -or
    $tagCommit -ne $identity.candidate_commit -or
    $release.tagName -ne $contract.tag -or
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
    if ($actualHashes[$hashField] -ne [string]$identity.$hashField) {
      Stop-ReleaseGate "$($method.ToUpperInvariant())_$($hashField.ToUpperInvariant())"
    }
  }

  $verified[$method] = [ordered]@{
    repository = $contract.repository
    version = $contract.version
    tag = $contract.tag
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
