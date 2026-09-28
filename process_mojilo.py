import os
import subprocess
import glob
import re

images_dir = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
ffmpeg = r"E:\Paresh\Auto Post\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

files = []
for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
    files.extend(glob.glob(os.path.join(images_dir, ext)))

print(f"Total files found: {len(files)}")

m_files = []
normal_files = []
for f in files:
    name = os.path.basename(f)
    match_m = re.search(r'^M(\d+)', name, re.IGNORECASE)
    match_n = re.search(r'^(\d+)', name)
    if match_m:
        m_files.append((f, int(match_m.group(1))))
    elif match_n:
        normal_files.append((f, int(match_n.group(1))))
    else:
        normal_files.append((f, 9999))

# Sort them based on the extracted number
m_files.sort(key=lambda x: x[1])
normal_files.sort(key=lambda x: x[1])

out_dir = os.path.join(images_dir, "final_processed")
os.makedirs(out_dir, exist_ok=True)

print("Processing Men files...")
m_count = 1
for f, num in m_files:
    ext = os.path.splitext(f)[1]
    new_name = f"M{m_count:03d} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{ext}"
    out_path = os.path.join(out_dir, new_name)
    if not os.path.exists(out_path):
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", f, "-vf", "crop=ih*4/5:ih", "-q:v", "2", out_path])
    m_count += 1
    if m_count % 100 == 0:
        print(f"Cropped {m_count} Men images...")

print("Processing Normal files...")
n_count = 1
for f, num in normal_files:
    ext = os.path.splitext(f)[1]
    new_name = f"{n_count:04d} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{ext}"
    out_path = os.path.join(out_dir, new_name)
    if not os.path.exists(out_path):
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", f, "-vf", "crop=ih*4/5:ih", "-q:v", "2", out_path])
    n_count += 1
    if n_count % 100 == 0:
        print(f"Cropped {n_count} Normal images...")

print("All done!")
