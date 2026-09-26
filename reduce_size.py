import os
import glob
from PIL import Image
import concurrent.futures

image_folder = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
files = glob.glob(os.path.join(image_folder, '**', '*.jpg'), recursive=True)

print(f"Found {len(files)} images to reduce size.")

def process_image(file_path):
    try:
        with Image.open(file_path) as img:
            # We don't need to resize or add logo, just re-save with lower quality to reduce size
            img.save(file_path, "JPEG", optimize=True, quality=65)
            return True
    except Exception as e:
        print(f"Failed {file_path}: {e}")
        return False

# Multithreading for speed
reduced_count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_image, files))
    reduced_count = sum(1 for r in results if r)

print(f"Successfully reduced size of {reduced_count} images.")
