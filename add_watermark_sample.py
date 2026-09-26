import os
from PIL import Image

logo_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\75a8776b-91c8-4f09-8194-33b0fc8097c7\.user_uploaded\media_1790400513904.png"
sample_img_path = r"E:\Paresh\Auto Post\Auto-Insta-Mojilo\images\Men\0001 MOJILO Tshirt Printing and DTF sticker and custmaiz printing surat.jpg"
output_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\75a8776b-91c8-4f09-8194-33b0fc8097c7\mojilo_sample_watermark.jpg"

try:
    with Image.open(sample_img_path) as base_img:
        # Convert base to RGBA if not
        if base_img.mode != "RGBA":
            base_img = base_img.convert("RGBA")
            
        with Image.open(logo_path) as logo:
            # Convert logo to RGBA
            if logo.mode != "RGBA":
                logo = logo.convert("RGBA")
            
            # Calculate new size for logo (e.g., 20% of the base image width)
            base_w, base_h = base_img.size
            logo_w, logo_h = logo.size
            
            new_logo_w = int(base_w * 0.20)
            new_logo_h = int((new_logo_w / logo_w) * logo_h)
            
            # Resize logo
            logo_resized = logo.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)
            
            # Position: Top-Left with a small padding
            padding = 20
            position = (padding, padding)
            
            # Paste logo onto base image (use logo as mask if it has transparency)
            # Since the logo provided has a solid black background, it might not look like a true watermark 
            # unless we make it slightly transparent or use it as is. 
            # I will just paste it directly.
            base_img.paste(logo_resized, position, logo_resized if 'A' in logo_resized.mode else None)
            
            # Save the final image
            final_img = base_img.convert("RGB")
            final_img.save(output_path, "JPEG", quality=90)
            print(f"Sample generated at: {output_path}")

except Exception as e:
    print(f"Error: {e}")
