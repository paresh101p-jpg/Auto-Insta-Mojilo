$finalDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Final_Men"
$files = Get-ChildItem -Path $finalDir -Filter "M*.*" -File
foreach ($f in $files) {
    if ($f.Name -match "^M([1-9]\d+)") {
        Remove-Item -Path $f.FullName -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Done deleting unpadded files!"
