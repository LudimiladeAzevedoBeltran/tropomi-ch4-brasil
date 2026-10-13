<#
.SYNOPSIS
    Limpeza e verificacao de um repositorio Git que fica dentro do Google Drive.

.DESCRIPTION
    O Google Drive injeta arquivos "desktop.ini" em todas as pastas sincronizadas
    - inclusive dentro de ".git". Isso pode quebrar o Git: por exemplo, o erro
    "bad object refs/desktop.ini" aparece ao rodar "git log --all" ou "git fsck".

    Este script:
      1. localiza o Git (no PATH ou no GitHub Desktop / Git for Windows);
      2. remove os "desktop.ini" de dentro da pasta ".git";
      3. roda "git fsck --full" para conferir a integridade;
      4. mostra refs, remote e status.

.PARAMETER Repo
    Caminho da raiz do repositorio. Padrao: a pasta-mae deste script.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\limpar_repo.ps1
#>

[CmdletBinding()]
param(
    [string]$Repo = ""
)

$ErrorActionPreference = "Stop"

# Raiz do repositorio = pasta-mae desta pasta (limpeza-de-git).
if (-not $Repo) {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Repo = Split-Path -Parent $scriptDir
}

function Find-Git {
    $candidatos = @()
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { $candidatos += $cmd.Source }
    $candidatos += @(Get-ChildItem "$env:LOCALAPPDATA\GitHubDesktop\*\resources\app\git\cmd\git.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName)
    $candidatos += @(Get-ChildItem "C:\Program Files\Git\cmd\git.exe", "C:\Program Files (x86)\Git\cmd\git.exe" -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName)
    foreach ($c in $candidatos) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    throw "Git nao encontrado. Instale o Git for Windows ou o GitHub Desktop."
}

Write-Host "== Repositorio: $Repo" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath (Join-Path $Repo ".git"))) {
    throw "Nao encontrei a pasta .git em: $Repo"
}

$git = Find-Git
Write-Host "Git: $git"

Write-Host "`n== 1) Removendo desktop.ini de dentro de .git ==" -ForegroundColor Yellow
$gitDir = Join-Path $Repo ".git"
$alvos = @(Get-ChildItem -LiteralPath $gitDir -Recurse -Force -Filter "desktop.ini" -ErrorAction SilentlyContinue)
Write-Host ("encontrados: " + $alvos.Count)
if ($alvos.Count -gt 0) {
    $alvos | Remove-Item -Force -ErrorAction SilentlyContinue
    $restantes = @(Get-ChildItem -LiteralPath $gitDir -Recurse -Force -Filter "desktop.ini" -ErrorAction SilentlyContinue).Count
    Write-Host ("removidos. restantes: " + $restantes) -ForegroundColor Green
}
else {
    Write-Host "nada a remover (ja esta limpo)."
}

Write-Host "`n== 2) Verificando integridade (git fsck --full) ==" -ForegroundColor Yellow
& $git -C $Repo fsck --full
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: repositorio integro." -ForegroundColor Green
}
else {
    Write-Host "ATENCAO: o fsck reportou problemas (veja acima)." -ForegroundColor Red
}

Write-Host "`n== 3) Refs ==" -ForegroundColor Yellow
& $git -C $Repo show-ref

Write-Host "`n== 4) Remote ==" -ForegroundColor Yellow
& $git -C $Repo remote -v

Write-Host "`n== 5) Status ==" -ForegroundColor Yellow
& $git -C $Repo status --short
Write-Host "(vazio acima = tudo certo)"

Write-Host "`nConcluido." -ForegroundColor Green
