$imagesDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$outDir = Join-Path $imagesDir "final_processed"

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

$files = Get-ChildItem -Path $imagesDir -File | Where-Object { $_.Extension -match "\.(jpg|jpeg|png|webp)$" }

$m_files = @()
$n_files = @()

foreach ($f in $files) {
    if ($f.Name -match "^M(\d+)") {
        $num = [int]$matches[1]
        $m_files += [PSCustomObject]@{ File = $f; Num = $num }
    } elseif ($f.Name -match "^(\d+)") {
        $num = [int]$matches[1]
        $n_files += [PSCustomObject]@{ File = $f; Num = $num }
    } else {
        $n_files += [PSCustomObject]@{ File = $f; Num = 9999 }
    }
}

$m_files = $m_files | Sort-Object Num
$n_files = $n_files | Sort-Object Num

Write-Host "Processing Men files..."
$m_count = 1
foreach ($item in $m_files) {
    $ext = $item.File.Extension
    $newName = "M{0:D3} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{1}" -f $m_count, $ext
    $outPath = Join-Path $outDir $newName
    
    if (-not (Test-Path $outPath)) {
        & $ffmpeg -y -v error -i $item.File.FullName -vf "crop=ih*4/5:ih" -q:v 2 $outPath
    }
    $m_count++
    if ($m_count % 50 -eq 0) { Write-Host "Processed $m_count Men images..." }
}

Write-Host "Processing Normal files..."
$n_count = 1
foreach ($item in $n_files) {
    $ext = $item.File.Extension
    $newName = "{0:D4} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{1}" -f $n_count, $ext
    $outPath = Join-Path $outDir $newName
    
    if (-not (Test-Path $outPath)) {
        & $ffmpeg -y -v error -i $item.File.FullName -vf "crop=ih*4/5:ih" -q:v 2 $outPath
    }
    $n_count++
    if ($n_count % 50 -eq 0) { Write-Host "Processed $n_count Normal images..." }
}

Write-Host "All done! Check 'final_processed' folder."
