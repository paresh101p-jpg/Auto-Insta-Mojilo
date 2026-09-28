import os
import subprocess
import glob
from concurrent.futures import ThreadPoolExecutor

input_dir = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
output_dir = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\Final_Images_Ready"
logo_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\9c350ae7-79fe-465c-bdc6-c4cca7fba461\.user_uploaded\media_1790594817738.png"
ffmpeg_path = r"E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

os.makedirs(output_dir, exist_ok=True)

files = glob.glob(os.path.join(input_dir, "*.*"))
files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
total = len(files)

print(f"Found {total} total files to process.")

def process_image(file_path):
    filename = os.path.basename(file_path)
    output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".jpg")
    
    # 1. Pads image to 1200x1500 (4:5)
    # 2. Scales logo to 250px width
    # 3. Overlays logo at bottom right
    cmd = [
        ffmpeg_path,
        "-y",
        "-v", "error",
        "-i", file_path,
        "-i", logo_path,
        "-filter_complex", "[0:v]scale=1200:1500:force_original_aspect_ratio=decrease,pad=1200:1500:(ow-iw)/2:(oh-ih)/2:color=black[bg];[1:v]scale=250:-1[logo];[bg][logo]overlay=W-w-30:H-h-30",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error on {filename}")
        return False

with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_image, files))

successes = sum(1 for r in results if r)
print(f"Finished! Successfully processed {successes} out of {total} images.")
