$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$menDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Men"
$imagesDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$oldDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\old_raw_images\Men"

if (-not (Test-Path $oldDir)) { New-Item -ItemType Directory -Force -Path $oldDir | Out-Null }

$files = Get-ChildItem -Path $menDir -File | Where-Object { $_.Extension -match "\.(jpg|jpeg|png|webp)$" }
$startNum = 1359

Write-Host "Found $($files.Count) files in Men folder."

foreach ($f in $files) {
    $ext = $f.Extension
    $newName = "M{0:D3} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{1}" -f $startNum, $ext
    $outPath = Join-Path $imagesDir $newName
    
    if (-not (Test-Path $outPath)) {
        & $ffmpeg -y -v error -i $f.FullName -vf "crop=ih*4/5:ih" -q:v 2 $outPath
    }
    
    Move-Item -Path $f.FullName -Destination $oldDir -Force
    
    $startNum++
    if ($startNum % 50 -eq 0) { Write-Host "Processed up to $startNum..." }
}
Write-Host "Finished processing Men folder!"
