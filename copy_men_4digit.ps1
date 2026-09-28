$imagesDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$finalDir = Join-Path $imagesDir "Final_Men"
if (-not (Test-Path $finalDir)) {
    New-Item -ItemType Directory -Path $finalDir | Out-Null
}

$files = Get-ChildItem -Path $imagesDir -Filter "M*.*" -File
foreach ($f in $files) {
    if ($f.Name -match "^M(\d+)\s") {
        $num = [int]$matches[1]
        $rem = $f.Name.Substring($matches[0].Length)
        $newName = "M{0:D4} {1}" -f $num, $rem
        $newPath = Join-Path $finalDir $newName
        
        Write-Host "Copying $($f.Name) -> $newName"
        Copy-Item -Path $f.FullName -Destination $newPath -Force
    } else {
        $newPath = Join-Path $finalDir $f.Name
        Write-Host "Copying $($f.Name) -> $($f.Name)"
        Copy-Item -Path $f.FullName -Destination $newPath -Force
    }
}
Write-Host "Done! All files copied to Final_Men folder!"
