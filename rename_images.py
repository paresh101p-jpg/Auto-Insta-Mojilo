import os
import glob

image_folder = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"

# Get all images recursively
files = []
for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4'):
    files.extend(glob.glob(os.path.join(image_folder, '**', ext), recursive=True))

# Sort to maintain some order
files.sort()

print(f"Found {len(files)} files to rename.")

counter = 1
for file_path in files:
    dir_name = os.path.dirname(file_path)
    ext = os.path.splitext(file_path)[1]
    
    # New name format: 0001 MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat.jpg
    new_name = f"{counter:04d} MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat{ext}"
    new_path = os.path.join(dir_name, new_name)
    
    try:
        os.rename(file_path, new_path)
        counter += 1
    except Exception as e:
        print(f"Failed to rename {file_path}: {e}")

print(f"Successfully renamed {counter-1} files.")
