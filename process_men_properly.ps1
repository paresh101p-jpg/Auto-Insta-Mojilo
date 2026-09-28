$menDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Men"
$imagesDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

$files = Get-ChildItem -Path $menDir -File | Where-Object { $_.Extension -match "\.(jpg|jpeg|png|webp)$" }

Write-Host "Found $($files.Count) files in Men folder."
foreach ($f in $files) {
    $ext = $f.Extension
    $numStr = ""
    
    if ($f.Name -match "^0*(\d+)") {
        $numStr = $matches[1]
    } elseif ($f.Name -match "(?i)^M0*(\d+)") {
        $numStr = $matches[1]
    }
    
    if ($numStr -ne "") {
        $num = [int]$numStr
        $newName = "M{0:D3} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{1}" -f $num, $ext
    } else {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        $newName = "M $baseName MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat$ext"
    }
    
    $outPath = Join-Path $imagesDir $newName
    
    & $ffmpeg -y -v error -i $f.FullName -vf "crop=ih*4/5:ih" -q:v 2 $outPath
}
Write-Host "Done! All Men images have been properly processed and copied to the images folder!"
