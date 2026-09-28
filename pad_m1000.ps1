$finalDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Final_Men"
$files = Get-ChildItem -Path $finalDir -Filter "M*.*" -File
foreach ($f in $files) {
    if ($f.Name -match "^M([1-9]\d+)") {
        $newName = $f.Name -replace "^M", "M0"
        Write-Host "Renaming $($f.Name) -> $newName"
        Rename-Item -Path $f.FullName -NewName $newName -Force
    }
}
Write-Host "Done adding leading 0 to M1000+ files!"
