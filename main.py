import os
import time
import subprocess
import requests
from google import genai
from PIL import Image
import urllib.parse
import fallback_captions
import json
from datetime import datetime

HISTORY_FILE = "post_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)
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
POSTED_FOLDER = "posted_images"
REELS_FILE = "reels_urls.txt"
TEMP_VIDEO = "temp_video.mp4"
GEMINI_MODELS  = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]
GITHUB_REPO_RAW_URL = "https://raw.githubusercontent.com/paresh101p-jpg/Auto-Insta-Mojilo/master/"

def get_next_media():
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        
    last_type_file = "last_post_type.txt"
    last_type = "REEL"
    if os.path.exists(last_type_file):
        with open(last_type_file, "r") as f:
            last_type = f.read().strip()
            
    next_type = "REEL" if last_type == "IMAGE" else "IMAGE"
    print(f"Last post was {last_type}. Now attempting to post {next_type}...")
    
    import random
    files = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".mp4"))]
    random.shuffle(files)
    
    images = [f for f in files if not f.lower().endswith('.mp4')]
    videos = [f for f in files if f.lower().endswith('.mp4')]
    
    history = load_history()
    now = datetime.now()
    
    def process_local_file(f):
        base_name = os.path.splitext(f)[0]
        if base_name in history:
            last_date_str = history[base_name]
            try:
                last_post_date = datetime.fromisoformat(last_date_str)
                days_passed = (now - last_post_date).days
                if days_passed < 7:
                    print(f"Skipping {f} (posted {days_passed} days ago, need 7)")
                    return None
            except:
                pass
                
        chosen_local_path = os.path.join(IMAGES_FOLDER, f)
        history[base_name] = now.isoformat()
        save_history(history)
        
        if not os.path.exists(POSTED_FOLDER):
            os.makedirs(POSTED_FOLDER)
        new_path = os.path.join(POSTED_FOLDER, f)
        os.rename(chosen_local_path, new_path)
        git_commit_and_push(f"Moved to posted: {f}")
        
        clean_path = new_path.replace("\\\\", "/")
        encoded_path = "/".join([urllib.parse.quote(p) for p in clean_path.split("/")])
        media_url = f"{GITHUB_REPO_RAW_URL}{encoded_path}"
        
        return {
            "type": "local",
            "local_path": new_path,
            "media_url": media_url,
            "is_video": f.lower().endswith('.mp4'),
            "original_path": chosen_local_path
        }

    # Try matching next_type first
    if next_type == "IMAGE" and images:
        for img in images:
            res = process_local_file(img)
            if res:
                with open(last_type_file, "w") as f: f.write("IMAGE")
                return res
        print("No valid images left, falling back to reel...")
        next_type = "REEL"
        
    if next_type == "REEL":
        if videos:
            for vid in videos:
                res = process_local_file(vid)
                if res:
                    with open(last_type_file, "w") as f: f.write("REEL")
                    return res
        
        try:
            # Check for reels_urls.txt (only for pooja or if mojilo has it)
            if "REELS_FILE" in globals() and os.path.exists(REELS_FILE):
                with open(REELS_FILE, "r") as f:
                    urls = [line.strip() for line in f.readlines() if line.strip()]
                if urls:
                    catbox_url = random.choice(urls)
                    with open(REELS_FILE, "w") as f:
                        urls.remove(catbox_url)
                        f.write("
".join(urls))
                    git_commit_and_push("Used a Catbox URL and removed it")
                    
                    print("Downloading video from Catbox for Gemini caption...")
                    import requests
                    res = requests.get(catbox_url)
                    with open(TEMP_VIDEO, "wb") as f:
                        f.write(res.content)
                        
                    with open(last_type_file, "w") as f: f.write("REEL")
                    return {
                        "type": "catbox",
                        "local_path": TEMP_VIDEO,
                        "media_url": catbox_url,
                        "is_video": True,
                        "original_path": None
                    }
        except Exception as e:
            print("Error checking reels_urls: ", e)
                
        # If reel failed, try image again as absolute fallback
        print("No valid reels left, falling back to image...")
        for img in images:
            res = process_local_file(img)
            if res:
                with open(last_type_file, "w") as f: f.write("IMAGE")
                return res

    raise Exception("No media available at all! Please upload new media.")


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
        "DM us for Custom T-Shirt Printing and DTF Stickers in Surat! ðŸ‘•ðŸ”¥\n"
        "Follow for more amazing designs! ðŸ‘‡\n"
        "Instagram: @MOJILOMART\n"
        "Facebook: @MojiloMart\n\n"
        "Like â¤ï¸ | Comment ðŸ’¬ | Share ðŸš€ | Save ðŸ“Œ\n\n"
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
    
    print("All AI attempts failed. Using random dynamic fallback caption.")
    return fallback_captions.get_random_fallback_caption()

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
        print(f"âœ… FB Feed Success (ID: {res['id']})")
        return True
    else:
        print(f"âŒ FB Feed Failed: {res}")
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
        print(f"âŒ FB Story Failed (photo upload step): {upload_res}")
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
        print(f"âœ… FB Story Success: {story_res}")
        return True
    else:
        print(f"âŒ FB Story Failed (photo_stories step): {story_res}")
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
        print(f"âŒ IG Container Creation Failed for {target}: {res}")
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
                print(f"âŒ Video Processing Failed!")
                return False
    else:
        print("Waiting 15 seconds for Instagram to process the image...")
        time.sleep(15)
    
    for attempt in range(6):
        pub_res = requests.post(pub_url, data=pub_payload).json()
        if 'id' in pub_res:
            print(f"âœ… IG {target} Success (ID: {pub_res['id']})")
            return True
        elif pub_res.get('error', {}).get('code') == 9007:
            # Media not ready, wait and retry
            print(f"Media not ready, retrying... (Attempt {attempt+1}/6)")
            time.sleep(10)
        else:
            print(f"âŒ IG Publish Failed for {target}: {pub_res}")
            return False
            
    return False

POSTED_FOLDER = "posted_images"

def cleanup_old_posted_media():
    if not os.path.exists(POSTED_FOLDER):
        os.makedirs(POSTED_FOLDER)
    files = os.listdir(POSTED_FOLDER)
    if files:
        for f in files:
            os.remove(os.path.join(POSTED_FOLDER, f))
        try:
            subprocess.run(["git", "config", "user.email", "bot@autopost.com"], check=True)
            subprocess.run(["git", "config", "user.name", "Auto Post Bot"], check=True)
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", "Cleaned up old posted media"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("Cleaned up old posted images and pushed.")
        except Exception as e:
            print(f"Git push warning during cleanup: {e}")

def move_media_and_push(media_path):
    if not os.path.exists(POSTED_FOLDER):
        os.makedirs(POSTED_FOLDER)
    new_path = os.path.join(POSTED_FOLDER, os.path.basename(media_path))
    os.rename(media_path, new_path)
    try:
        subprocess.run(["git", "config", "user.email", "bot@autopost.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Auto Post Bot"], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"Moved to posted: {os.path.basename(media_path)}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Media moved to posted folder and pushed to GitHub immediately!")
    except Exception as e:
        print(f"Git push warning during move: {e}")
    return new_path

def move_back_to_images(posted_path):
    print(f"Moving {posted_path} back to images folder because post failed...")
    base_name = os.path.splitext(os.path.basename(posted_path))[0]
    
    # Remove from history so it can be tried again
    history = load_history()
    if base_name in history:
        del history[base_name]
        save_history(history)
        
    new_path = os.path.join(IMAGES_FOLDER, os.path.basename(posted_path))
    os.rename(posted_path, new_path)
    try:
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Auto Insta Bot"], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"Moved back to images due to failure: {os.path.basename(posted_path)}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Media moved back to images folder and pushed to GitHub.")
    except Exception as e:
        print(f"Git push warning during move back: {e}")

def main():
    try:
        cleanup_old_posted_media()
        
        media_path = get_next_media()
        media_path = move_media_and_push(media_path)
        media_filename = os.path.basename(media_path)
        is_video = media_filename.lower().endswith('.mp4')
        
        clean_path = media_path.replace("\\", "/")
        encoded_path = "/".join([urllib.parse.quote(p) for p in clean_path.split("/")])
        public_media_url = GITHUB_REPO_RAW_URL + encoded_path
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
            print("âœ… All posts done successfully! Media is already in posted_images folder.")
        else:
            print("âŒ All posts failed. Moving media back to images folder so it's not lost.")
            move_back_to_images(media_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
