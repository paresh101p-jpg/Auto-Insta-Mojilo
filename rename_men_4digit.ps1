$imagesDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$files = Get-ChildItem -Path $imagesDir -Filter "M*.*" -File
foreach ($f in $files) {
    if ($f.Name -match "^M(\d+)\s") {
        $num = [int]$matches[1]
        $rem = $f.Name.Substring($matches[0].Length)
        $newName = "M{0:D4} {1}" -f $num, $rem
        
        # Only rename if the name is actually changing (e.g. M475 -> M0475)
        if ($f.Name -ne $newName) {
            Write-Host "Renaming $($f.Name) to $newName"
            Rename-Item -Path $f.FullName -NewName $newName -Force
        }
    }
}
Write-Host "Done renaming to 4-digit format!"
