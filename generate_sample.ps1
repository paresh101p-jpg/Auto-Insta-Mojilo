$ffmpeg = "E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$input = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\M0001 MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat.jpg"
$logo = "C:\Users\Admin\.gemini\antigravity-ide\brain\9c350ae7-79fe-465c-bdc6-c4cca7fba461\.user_uploaded\media_1790594817738.png"
$output = "E:\Paresh\Auto Post\Auto-Insta-Mojilo\sample_logo_overlay.jpg"

& $ffmpeg -y -i $input -i $logo -filter_complex "[1:v]scale=250:-1[logo];[0:v][logo]overlay=W-w-30:H-h-30" $output
Write-Host "Sample generated at $output"
