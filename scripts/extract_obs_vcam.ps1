# extract_obs_vcam.ps1
# 从 OBS Studio 安装包中提取 Virtual Camera 驱动 DLL
# 在 GitHub Actions 的 windows-latest runner 上运行

$ErrorActionPreference = "Stop"

Write-Host "=== 提取 OBS Virtual Camera 驱动 ==="

# 1. 获取 OBS Studio 最新版本信息
$apiUrl = "https://api.github.com/repos/obsproject/obs-studio/releases/latest"
Write-Host "  获取 OBS 最新版本..."
$release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "GitHubActions" }
$version = $release.tag_name
Write-Host "  OBS 版本: $version"

# 2. 找到 Windows 安装包下载链接
$installer = $release.assets | Where-Object {
    $_.name -match "\.exe$" -and $_.name -match "Windows"
} | Select-Object -First 1

if (-not $installer) {
    # 备选：匹配任何 exe 安装包
    $installer = $release.assets | Where-Object { $_.name -match "obs-studio.*\.exe$" } | Select-Object -First 1
}

if (-not $installer) {
    Write-Host "  ❌ 未找到 OBS Windows 安装包"
    exit 1
}

Write-Host "  安装包: $($installer.name) ($([math]::Round($installer.size / 1MB))MB)"

# 3. 下载安装包
$installerPath = "$env:TEMP\obs-installer.exe"
Write-Host "  下载中..."
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $installer.browser_download_url -OutFile $installerPath
Write-Host "  下载完成: $([math]::Round((Get-Item $installerPath).Length / 1MB))MB"

# 4. 用 7z 解压（Windows runner 自带）
$extractDir = "$env:TEMP\obs-extracted"
if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

Write-Host "  解压安装包..."
& 7z x "$installerPath" -o"$extractDir" -y -bsp0 -bso0

# 5. 搜索 Virtual Camera 相关 DLL
Write-Host "  搜索 Virtual Camera DLL..."
$vcamFiles = Get-ChildItem -Path $extractDir -Recurse | Where-Object {
    $_.Name -match "obs-virtualcam" -and $_.Extension -eq ".dll"
}

if ($vcamFiles.Count -eq 0) {
    # 备选搜索
    $vcamFiles = Get-ChildItem -Path $extractDir -Recurse | Where-Object {
        $_.Name -match "virtualcam" -and $_.Extension -eq ".dll"
    }
}

if ($vcamFiles.Count -eq 0) {
    Write-Host "  ❌ 未找到 Virtual Camera DLL"
    Write-Host "  解压目录内容:"
    Get-ChildItem $extractDir -Recurse -Filter "*.dll" | Select-Object -First 20 | ForEach-Object {
        Write-Host "    $($_.FullName)"
    }
    exit 1
}

# 6. 复制到 driver/ 目录
$outputDir = "driver"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

foreach ($dll in $vcamFiles) {
    $dst = Join-Path $outputDir $dll.Name
    Copy-Item $dll.FullName $dst -Force
    Write-Host "  ✅ $($dll.Name) ($([math]::Round($dll.Length / 1KB))KB) → $dst"
}

# 7. 清理
Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== 驱动提取完成 ==="
Get-ChildItem $outputDir | ForEach-Object {
    Write-Host "  $($_.Name) ($([math]::Round($_.Length / 1KB))KB)"
}
