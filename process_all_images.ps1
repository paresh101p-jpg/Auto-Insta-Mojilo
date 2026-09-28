$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$inputDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
$outputDir = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\Final_Images_Ready"
$logo = "C:\Users\Admin\.gemini\antigravity-ide\brain\9c350ae7-79fe-465c-bdc6-c4cca7fba461\.user_uploaded\media_1790594817738.png"

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$files = Get-ChildItem -Path $inputDir -Filter "*.*" -File | Where-Object { $_.Extension -match "\.(jpg|jpeg|png)$" }
$total = $files.Count
$count = 0

foreach ($f in $files) {
    $count++
    $output = Join-Path $outputDir ($f.BaseName + ".jpg")
    
    if ($count % 50 -eq 0) {
        Write-Host "Processing $count of $total..."
    }
    
    # Pad to 1200x1500 (4:5) AND overlay logo
    & $ffmpeg -y -v error -i $f.FullName -i $logo -filter_complex "[0:v]scale=1200:1500:force_original_aspect_ratio=decrease,pad=1200:1500:(ow-iw)/2:(oh-ih)/2:color=black[bg];[1:v]scale=250:-1[logo];[bg][logo]overlay=W-w-30:H-h-30" $output
}
Write-Host "Done! Processed all $total images!"
