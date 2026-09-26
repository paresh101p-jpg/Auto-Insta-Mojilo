import os
import glob
from PIL import Image
import concurrent.futures

image_folder = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images"
logo_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\75a8776b-91c8-4f09-8194-33b0fc8097c7\.user_uploaded\media_1790399893094.png"

files = []
for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
    files.extend(glob.glob(os.path.join(image_folder, '**', ext), recursive=True))

print(f"Found {len(files)} images to watermark.")

# Pre-load and convert logo
logo = Image.open(logo_path).convert("RGBA")

def process_image(file_path):
    try:
        with Image.open(file_path) as base_img:
            base_img = base_img.convert("RGBA")
            
            # Calculate new size for logo (20% of the base image width)
            new_w = int(base_img.width * 0.20)
            new_h = int((new_w / logo.width) * logo.height)
            logo_resized = logo.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Paste logo onto base image
            base_img.paste(logo_resized, (20, 20), logo_resized)
            
            # Save the final image (overwrite)
            final_img = base_img.convert("RGB")
            final_img.save(file_path, "JPEG", quality=90)
            return True
    except Exception as e:
        print(f"Failed {file_path}: {e}")
        return False

# Use multithreading for faster processing
watermarked_count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_image, files))
    watermarked_count = sum(1 for r in results if r)

print(f"Successfully watermarked {watermarked_count} images.")
