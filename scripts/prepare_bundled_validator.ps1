param(
    [Parameter(Mandatory = $true)][string]$VeraPdfInstallerJar,
    [Parameter(Mandatory = $true)][string]$TemurinJreDirectory
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$stage = Join-Path $root "vendor-stage"
$vera = Join-Path $stage "verapdf"
$jre = Join-Path $stage "jre"
$installer = (Resolve-Path -LiteralPath $VeraPdfInstallerJar).Path
$runtime = (Resolve-Path -LiteralPath $TemurinJreDirectory).Path
$java = Join-Path $runtime "bin\java.exe"
$release = Join-Path $runtime "release"

if (-not (Test-Path -LiteralPath $java -PathType Leaf)) {
    throw "The selected Temurin directory does not contain bin\java.exe."
}
if (-not (Select-String -LiteralPath $release -Pattern 'IMPLEMENTOR="Eclipse Adoptium"' -Quiet)) {
    throw "Only an official Eclipse Adoptium Temurin runtime is accepted."
}

New-Item -ItemType Directory -Force -Path $stage | Out-Null
$configuration = Join-Path $stage "verapdf-auto-install.xml"
$escaped = [Security.SecurityElement]::Escape($vera)
$xml = @"
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<AutomatedInstallation langpack="eng">
  <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="welcome"/>
  <com.izforge.izpack.panels.target.TargetPanel id="install_dir"><installpath>$escaped</installpath></com.izforge.izpack.panels.target.TargetPanel>
  <com.izforge.izpack.panels.packs.PacksPanel id="sdk_pack_select">
    <pack index="0" name="veraPDF GUI" selected="false"/>
    <pack index="1" name="veraPDF CLI" selected="true"/>
    <pack index="2" name="veraPDF Documentation" selected="true"/>
    <pack index="3" name="veraPDF Sample Plugins" selected="false"/>
  </com.izforge.izpack.panels.packs.PacksPanel>
  <com.izforge.izpack.panels.install.InstallPanel id="install"/>
  <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>
</AutomatedInstallation>
"@
Set-Content -LiteralPath $configuration -Value $xml -Encoding UTF8

& $java -jar $installer $configuration
if ($LASTEXITCODE -ne 0) { throw "veraPDF automated installation failed." }
Copy-Item -LiteralPath $runtime -Destination $jre -Recurse -Force

$env:JAVACMD = Join-Path $jre "bin\java.exe"
& (Join-Path $vera "verapdf.bat") --version
if ($LASTEXITCODE -ne 0) { throw "The prepared veraPDF launcher failed its version check." }
Write-Host "Bundled validator stage prepared at $stage"
