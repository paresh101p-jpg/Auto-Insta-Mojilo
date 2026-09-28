$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$inputDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$outputDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Men_With_Logo"
$logo = "C:\Users\Admin\.gemini\antigravity-ide\brain\9c350ae7-79fe-465c-bdc6-c4cca7fba461\.user_uploaded\media_1790594817738.png"

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$files = Get-ChildItem -Path $inputDir -Filter "M0*.*" -File | Where-Object { $_.Extension -match "\.(jpg|png)$" }
$total = $files.Count
$count = 0

foreach ($f in $files) {
    $count++
    $output = Join-Path $outputDir $f.Name
    if ($count % 50 -eq 0) {
        Write-Host "Processing $count of $total..."
    }
    & $ffmpeg -y -v error -i $f.FullName -i $logo -filter_complex "[1:v]scale=250:-1[logo];[0:v][logo]overlay=W-w-30:H-h-30" $output
}
Write-Host "Done adding logo to all $total Men images!"
