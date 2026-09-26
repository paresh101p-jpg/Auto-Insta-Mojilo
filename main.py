import os
import time
import subprocess
import requests
from google import genai
from PIL import Image

# Secrets from GitHub Actions
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

# Page ID hardcoded (verified working: Mojilo)
FB_PAGE_ID = "171810493306372"

if not all([GEMINI_API_KEY, FB_ACCESS_TOKEN]):
    print("Error: Please set GEMINI_API_KEY and FB_ACCESS_TOKEN in GitHub Secrets.")
    exit(1)

print(f"[DEBUG] Using Page ID: {FB_PAGE_ID}")
print(f"[DEBUG] Token starts with: {FB_ACCESS_TOKEN[:20]}...")

client = genai.Client(api_key=GEMINI_API_KEY)
IMAGES_FOLDER = "images"
GEMINI_MODELS  = ["gemini-1.5-flash", "gemini-1.5-pro"]
GITHUB_REPO_RAW_URL = "https://raw.githubusercontent.com/paresh101p-jpg/Auto-Insta-Mojilo/master/"

def get_next_media():
    if not os.path.exists(IMAGES_FOLDER):
        raise Exception(f"'{IMAGES_FOLDER}' folder not found! Upload media there first.")
    files = sorted([
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4"))
    ])
    if not files:
        raise Exception("No media left in 'images/' folder! Please upload more.")
    chosen = os.path.join(IMAGES_FOLDER, files[0])
    print(f"Using media: {chosen} ({len(files)} remaining)")
    return chosen

def generate_caption(media_path):
    is_video = media_path.lower().endswith('.mp4')
    print(f"Analyzing {'video' if is_video else 'image'} using Gemini Vision...")
    
    prompt = (
        "You are an expert Instagram Social Media Manager for a custom T-shirt printing and fashion page. Look at the content provided. "
        "Write a long, engaging, and trendy Instagram caption in a mix of Hindi and English (Hinglish) inspired by the content. "
        "Your response MUST be the final Instagram caption, formatted beautifully with emojis. "
        "Include the following elements in this exact order:\n"
        "1. A catchy hook line at the very top.\n"
        "2. A 3-4 line description about custom t-shirt printing, DTF stickers, trending fashion, or the specific design shown in the image.\n"
        "3. A call to action exactly like this:\n\n"
        "DM us for Custom T-Shirt Printing and DTF Stickers in Surat! 👕🔥\n"
        "Follow for more amazing designs! 👇\n"
        "Instagram: @MOJILOMART\n"
        "Facebook: @MojiloMart\n\n"
        "Like ❤️ | Comment 💬 | Share 🚀 | Save 📌\n\n"
        "4. At least 15-20 highly relevant hashtags at the bottom (e.g., #mojilo #tshirtprinting #dtfsticker #suratfashion #customtshirts #trending #tshirtstyle #surat etc.). "
        "Do not include any extra text outside the caption itself."
    )
    
    content_to_pass = None
    uploaded_file = None
    
    try:
        if is_video:
            print("Uploading video to Gemini...")
            uploaded_file = client.files.upload(file=media_path)
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)
            content_to_pass = uploaded_file
        else:
            content_to_pass = Image.open(media_path)
            
        for model_name in GEMINI_MODELS:
            for attempt in range(1, 4):
                try:
                    print(f"Trying {model_name} (attempt {attempt})...")
                    resp = client.models.generate_content(
                        model=model_name, 
                        contents=[content_to_pass, prompt]
                    )
                    text = resp.text.strip()
                    if text:
                        print(f"Extracted Caption Generated!\n")
                        return text
                except Exception as e:
                    print(f"Failed: {e}")
                    time.sleep(5 * attempt)
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                print("Cleaned up video from Gemini storage.")
            except:
                pass
    
    return """Upgrade your style with custom printed T-shirts! 👕🔥\n\nDM us for the best Custom T-Shirt Printing and DTF Stickers in Surat!\n\nFollow for more amazing designs! 👇\nInstagram: @MOJILOMART\nFacebook: @MojiloMart\n\nLike ❤️ | Comment 💬 | Share 🚀 | Save 📌\n\n#mojilo #tshirtprinting #dtfsticker #suratfashion #customtshirts #trending #surat"""

def get_ig_account_id():
    print("Fetching connected Instagram Account ID...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}?fields=instagram_business_account&access_token={FB_ACCESS_TOKEN}"
    res = requests.get(url).json()
    ig_id = res.get('instagram_business_account', {}).get('id')
    if ig_id:
        print(f"Found IG Account ID: {ig_id}")
    else:
        print("Warning: No Instagram Business Account linked to this Facebook Page.")
    return ig_id

def post_fb_feed(caption, media_url, is_video=False):
    print(f"Posting to Facebook Feed ({'Video' if is_video else 'Photo'})...")
    fb_caption = caption
    
    if is_video:
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
        payload = {'description': fb_caption, 'file_url': media_url, 'access_token': FB_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
        payload = {'message': fb_caption, 'url': media_url, 'access_token': FB_ACCESS_TOKEN}
        
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"✅ FB Feed Success (ID: {res['id']})")
        return True
    else:
        print(f"❌ FB Feed Failed: {res}")
        return False

def post_fb_story(image_url):
    print("Posting to Facebook Story (2-step method)...")

    # Step 1: Upload the photo as UNPUBLISHED to get a real photo_id
    upload_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    upload_payload = {
        'url': image_url,
        'published': 'false',
        'access_token': FB_ACCESS_TOKEN
    }
    upload_res = requests.post(upload_url, data=upload_payload).json()
    photo_id = upload_res.get('id')

    if not photo_id:
        print(f"❌ FB Story Failed (photo upload step): {upload_res}")
        return False

    print(f"Uploaded unpublished photo for story (photo_id: {photo_id})")

    # Step 2: Publish that photo_id as an actual Page Story
    story_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photo_stories"
    story_payload = {
        'photo_id': photo_id,
        'access_token': FB_ACCESS_TOKEN
    }
    story_res = requests.post(story_url, data=story_payload).json()

    if story_res.get('success') or 'post_id' in story_res or 'id' in story_res:
        print(f"✅ FB Story Success: {story_res}")
        return True
    else:
        print(f"❌ FB Story Failed (photo_stories step): {story_res}")
        return False

def post_ig_media(ig_account_id, caption, media_url, is_story=False, is_video=False):
    target = "Story" if is_story else ("Reel" if is_video else "Feed")
    print(f"Posting to Instagram {target}...")
    
    # Step 1: Create Container
    url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media"
    payload = {'access_token': FB_ACCESS_TOKEN}
    
    if is_video:
        payload['video_url'] = media_url
        if is_story:
            payload['media_type'] = 'STORIES'
        else:
            payload['media_type'] = 'REELS'
            payload['caption'] = caption
    else:
        payload['image_url'] = media_url
        if is_story:
            payload['media_type'] = 'STORIES'
        else:
            payload['caption'] = caption
        
    res = requests.post(url, data=payload).json()
    creation_id = res.get('id')
    
    if not creation_id:
        print(f"❌ IG Container Creation Failed for {target}: {res}")
        return False
        
    # Step 2: Publish Container
    print(f"Publishing IG {target} container...")
    pub_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media_publish"
    pub_payload = {'creation_id': creation_id, 'access_token': FB_ACCESS_TOKEN}
    
    # Wait for processing
    if is_video:
        status = "IN_PROGRESS"
        while status != "FINISHED":
            time.sleep(10)
            status_res = requests.get(f"https://graph.facebook.com/v20.0/{creation_id}?fields=status_code&access_token={FB_ACCESS_TOKEN}").json()
            status = status_res.get('status_code', 'ERROR')
            print(f"Video Status: {status}")
            if status == "ERROR" or status == "EXPIRED":
                print(f"❌ Video Processing Failed!")
                return False
    else:
        print("Waiting 15 seconds for Instagram to process the image...")
        time.sleep(15)
    
    for attempt in range(6):
        pub_res = requests.post(pub_url, data=pub_payload).json()
        if 'id' in pub_res:
            print(f"✅ IG {target} Success (ID: {pub_res['id']})")
            return True
        elif pub_res.get('error', {}).get('code') == 9007:
            # Media not ready, wait and retry
            print(f"Media not ready, retrying... (Attempt {attempt+1}/6)")
            time.sleep(10)
        else:
            print(f"❌ IG Publish Failed for {target}: {pub_res}")
            return False
            
    return False

def delete_posted_media(media_path):
    print(f"Deleting posted media: {media_path}")
    os.remove(media_path)
    try:
        subprocess.run(["git", "config", "user.email", "bot@autopost.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Auto Post Bot"], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"Posted and removed: {os.path.basename(media_path)}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Media deleted and pushed to GitHub!")
    except Exception as e:
        print(f"Git push warning: {e}")

def main():
    try:
        media_path = get_next_media()
        media_filename = os.path.basename(media_path)
        is_video = media_filename.lower().endswith('.mp4')
        
        clean_path = media_path.replace("\\", "/")
        public_media_url = GITHUB_REPO_RAW_URL + clean_path
        print(f"Generated Public URL: {public_media_url}")

        caption = generate_caption(media_path)

        success = False

        # Post to Facebook Feed
        if post_fb_feed(caption, public_media_url, is_video=is_video):
            success = True
        
        # Post to Facebook Story (only for images, video story API is unstable)
        if not is_video:
            post_fb_story(public_media_url)

        # Instagram Posting
        ig_account_id = get_ig_account_id()
        if ig_account_id:
            # Post to IG Feed/Reel
            if post_ig_media(ig_account_id, caption, public_media_url, is_story=False, is_video=is_video):
                success = True
            # Post to IG Story
            post_ig_media(ig_account_id, "", public_media_url, is_story=True, is_video=is_video)

        if success:
            print("⏳ All posts done. Waiting 5 minutes (300s) before deleting media from GitHub...")
            time.sleep(300)
            delete_posted_media(media_path)
        else:
            print("❌ All posts failed. Not deleting the media to avoid data loss.")


    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
