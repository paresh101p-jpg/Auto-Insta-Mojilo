import os
import random
import time
import subprocess
import requests
from google import genai
from PIL import Image, ImageFilter
import urllib.parse
import json
from datetime import datetime

# Secrets from GitHub Actions
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")

# NAYE PAGE KA ID YAHAN HARDCODE KAREIN
FB_PAGE_ID = "171810493306372" 

if not all([GEMINI_API_KEY, FB_ACCESS_TOKEN]):
    print("Error: Please set GEMINI_API_KEY and FB_ACCESS_TOKEN in GitHub Secrets.")
    exit(1)

if FB_PAGE_ID == "YAHAN_APNA_NAYA_PAGE_ID_DALNA_HAI":
    print("Error: Please set your FB_PAGE_ID in main.py first.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
IMAGES_FOLDER = "images"
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash-latest"]
# Yahan naye repo ka naam aayega (e.g., Auto-Insta-Mojilo)
GITHUB_REPO_RAW_URL = "https://raw.githubusercontent.com/paresh101p-jpg/Auto-Insta-Mojilo/main/"

HISTORY_FILE = "post_history.json"
POSTED_FOLDER = "posted_images"
REELS_FILE = "reels_urls.txt"
TEMP_VIDEO = "temp_video.mp4"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def git_commit_and_push(commit_message):
    try:
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Auto Insta Bot"], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"Git Push Success: {commit_message}")
    except Exception as e:
        print(f"Git push warning: {e}")

def mark_url_as_used(url, is_video):
    filename = "reels_urls.txt" if is_video else "images_urls.txt"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        if url in urls:
            urls.remove(url)
            with open(filename, "w") as f:
                f.write("\n".join(urls))
            with open("used_urls.txt", "a") as uf:
                uf.write(url + "\n")
            git_commit_and_push(f"Used and removed URL from {filename}")

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

    def get_catbox_from_file(filename, is_video):
        if not os.path.exists(filename): return None
        with open(filename, "r") as f: urls = [line.strip() for line in f if line.strip()]
        
        used_urls = []
        if os.path.exists("used_urls.txt"):
            with open("used_urls.txt", "r") as f: used_urls = [line.strip() for line in f if line.strip()]
            
        available_urls = [u for u in urls if u not in used_urls]
        if not available_urls: return None
        
        chosen_url = available_urls[0]
        print(f"Selected Catbox URL: {chosen_url}")
        
        import requests
        temp_ext = ".mp4" if is_video else ".jpg"
        temp_file = "temp_media" + temp_ext
        
        res_download = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        if res_download.status_code == 200:
            with open(temp_file, "wb") as mf:
                for chunk in res_download.iter_content(chunk_size=8192):
                    mf.write(chunk)
            print(f"Downloaded video successfully, size: {os.path.getsize(temp_file)} bytes")
        else:
            print(f"Failed to download video, status code: {res_download.status_code}")
            return None
            
        return {
            "type": "catbox",
            "local_path": temp_file,
            "media_url": chosen_url,
            "is_video": is_video,
            "original_path": None
        }

    def get_image_from_github_folder():
        import random
        from datetime import datetime
        import urllib.parse
        history = load_history()
        now = datetime.now()
        files = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        random.shuffle(files)
        
        for f in files:
            base_name = os.path.splitext(f)[0]
            if base_name in history:
                last_date_str = history[base_name]
                try:
                    last_post_date = datetime.fromisoformat(last_date_str)
                    days_passed = (now - last_post_date).days
                    if days_passed < 7: continue
                except: pass
                    
            chosen_local_path = os.path.join(IMAGES_FOLDER, f)
            history[base_name] = now.isoformat()
            save_history(history)
            
            if not os.path.exists(POSTED_FOLDER): os.makedirs(POSTED_FOLDER)
            new_path = os.path.join(POSTED_FOLDER, f)
            os.rename(chosen_local_path, new_path)
            git_commit_and_push(f"Moved to posted: {f}")
            
            # Upload to Catbox so Instagram/Facebook can access the URL
            # raw.githubusercontent.com URLs are NOT accepted by Instagram Graph API
            print(f"Uploading image to Catbox for public URL...")
            catbox_url = None
            try:
                with open(new_path, 'rb') as img_f:
                    cat_res = requests.post('https://catbox.moe/user/api.php',
                        data={'reqtype': 'fileupload'},
                        files={'fileToUpload': img_f})
                if cat_res.status_code == 200 and cat_res.text.strip().startswith('https://'):
                    catbox_url = cat_res.text.strip()
                    print(f"Catbox URL for image: {catbox_url}")
            except Exception as ce:
                print(f"Catbox image upload failed: {ce}")
            
            if not catbox_url:
                print("Could not get Catbox URL for image, skipping this image.")
                continue
            
            return {
                "type": "local",
                "local_path": new_path,
                "media_url": catbox_url,
                "is_video": False,
                "original_path": chosen_local_path
            }
        return None

    if next_type == "IMAGE":
        res = get_image_from_github_folder()
        if res:
            with open(last_type_file, "w") as f: f.write("IMAGE")
            git_commit_and_push("Update last post type to IMAGE")
            return res

    if next_type == "REEL":
        res = get_catbox_from_file("reels_urls.txt", True)
        if res:
            with open(last_type_file, "w") as f: f.write("REEL")
            git_commit_and_push("Update last post type to REEL")
            return res

    print("Could not find media of the requested type.")
    return None

def generate_caption(media_path):
    is_video = media_path.lower().endswith('.mp4')
    print(f"Analyzing {'video' if is_video else 'image'} using Gemini Vision...")
    prompt = """You are an expert Instagram Social Media Manager for a custom T-shirt printing and fashion page. Look at the content provided.
Write a long, engaging, and trendy Instagram caption in English ONLY inspired by the content.
Your response MUST be the final Instagram caption, formatted beautifully with standard emojis.
Include the following elements in this exact order:
1. A catchy hook line at the very top.
2. A 3-4 line description about custom t-shirt printing, DTF stickers, trending fashion, or the specific design shown in the image.
3. A call to action exactly like this:

DM us for Custom T-Shirt Printing and DTF Stickers in Surat! 👇🔥
Follow for more amazing designs! 👇🔥
Instagram: @MOJILOMART
Facebook: @MojiloMart

Like 👍 💬 | Comment 💬 | Share 🚀 | Save 📌

4. At least 15-20 highly relevant hashtags at the bottom (e.g., #mojilo #tshirtprinting #dtfsticker #suratfashion #customtshirts #trending #tshirtstyle #surat etc.).
Do not include any extra text outside the caption itself."""
    
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
                    print(f"Attempt {attempt} with model {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[content_to_pass, prompt]
                    )
                    caption = response.text
                    if caption:
                        print("Caption generated successfully!\n")
                        print(caption)
                        print("\n" + "="*50 + "\n")
                        return caption
                except Exception as e:
                    print(f"Gemini error on attempt {attempt} with {model_name}: {e}")
                    time.sleep(3)
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                print("Cleaned up video from Gemini storage.")
            except:
                pass
                
    try:
        import fallback_captions
        return fallback_captions.get_random_fallback_caption()
    except Exception as e:
        print(f"Fallback captions failed too: {e}")
        return """DM us for Custom T-Shirt Printing and DTF Stickers in Surat! 👇🔥

Follow for more amazing designs! 👇🔥
Instagram: @MOJILOMART
Facebook: @MojiloMart

Like 👍 💬 | Comment 💬 | Share 🚀 | Save 📌

#mojilo #tshirtprinting #dtfsticker #suratfashion #customtshirts"""

def get_ig_account_id():
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}?fields=instagram_business_account&access_token={FB_ACCESS_TOKEN}"
    res = requests.get(url).json()
    if 'instagram_business_account' in res:
        return res['instagram_business_account']['id']
    else:
        print(f"âŒ Error getting IG Account ID: {res}")
        return None

def post_fb_feed(caption, image_url):
    print("Posting to Facebook Feed (Photo)...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload).json()
    if 'id' in res:
        print(f"âœ… FB Feed Success (ID: {res['id']})")
        return True
    else:
        print(f"âŒ FB Feed Failed: {res}")
        return False

def post_fb_video(caption, local_file):
    print("Posting to Facebook Feed (Video) via direct file upload...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open(local_file, "rb") as vf:
            files = {
                'source': (local_file, vf, 'video/mp4')
            }
            payload = {
                'description': caption,
                'access_token': FB_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, files=files).json()
            
        if 'id' in res:
            print(f"✅ FB Video Success (ID: {res['id']})")
            return True
        else:
            print(f"❌ FB Video Failed: {res}")
            return False
    except Exception as e:
        print(f"❌ Error uploading FB Video: {e}")
        return False



def post_fb_video_story(local_file):
    print("Posting to Facebook Story (Video)...")
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/video_stories"
    
    try:
        import os
        file_size = os.path.getsize(local_file)
        
        # Step 1: Start
        start_payload = {
            'upload_phase': 'start',
            'access_token': FB_ACCESS_TOKEN,
            'file_size': file_size
        }
        res_start = requests.post(url, data=start_payload).json()
        if 'video_id' not in res_start:
            print(f"❌ FB Video Story Start Failed: {res_start}")
            return False
            
        video_id = res_start['video_id']
        upload_url = res_start['upload_url']
        
        # Step 2: Upload
        with open(local_file, "rb") as vf:
            files = {'video_file_chunk': (local_file, vf, 'video/mp4')}
            upload_payload = {
                'access_token': FB_ACCESS_TOKEN,
                'upload_phase': 'transfer',
                'start_offset': '0',
                'video_id': video_id
            }
            headers = {'Authorization': f'OAuth {FB_ACCESS_TOKEN}'}
            res_up = requests.post(upload_url, headers=headers, data=upload_payload, files=files).json()
            # Some FB APIs return success in a weird format, let's just proceed
            
        # Step 3: Finish
        finish_payload = {
            'upload_phase': 'finish',
            'access_token': FB_ACCESS_TOKEN,
            'video_id': video_id
        }
        res_finish = requests.post(url, data=finish_payload).json()
        if res_finish.get('success'):
            print(f"✅ FB Video Story Success (ID: {video_id})")
            return True
        else:
            print(f"❌ FB Video Story Finish Failed: {res_finish}")
            return False
    except Exception as e:
        print(f"❌ Error uploading FB Video Story: {e}")
        return False

def post_fb_story(image_url):
    print("Posting to Facebook Story (2-step method)...")
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
    media_endpoint_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media"
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
            
    res = requests.post(media_endpoint_url, data=payload).json()
    if 'id' not in res:
        print(f"âŒ IG Upload Error: {res}")
        return False
        
    container_id = res['id']
    print(f"Container Created: {container_id}. Waiting for processing...")
    
    if is_video:
        status = "IN_PROGRESS"
        while status != "FINISHED":
            time.sleep(10)
            status_res = requests.get(f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={FB_ACCESS_TOKEN}").json()
            status = status_res.get('status_code', 'ERROR')
            print(f"Video Status: {status}")
            if status == "ERROR" or status == "EXPIRED":
                print(f"âŒ Video Processing Failed!")
                return False
    else:
        time.sleep(25)
    
    publish_url = f"https://graph.facebook.com/v20.0/{ig_account_id}/media_publish"
    pub_payload = {
        'creation_id': container_id,
        'access_token': FB_ACCESS_TOKEN
    }
    pub_res = requests.post(publish_url, data=pub_payload).json()
    if 'id' in pub_res:
        print(f"âœ… IG {target} Published Successfully! (ID: {pub_res['id']})")
        return True
    else:
        print(f"âŒ IG Publish Error: {pub_res}")
        return False

def handle_failure(media_info):
    print("âŒ Post failed. Attempting to rollback...")
    if media_info["type"] == "local":
        print("Moving media back to images folder...")
        os.rename(media_info["local_path"], media_info["original_path"])
        
        # Remove from history
        base_name = os.path.splitext(os.path.basename(media_info["original_path"]))[0]
        history = load_history()
        if base_name in history:
            del history[base_name]
            save_history(history)
            
        git_commit_and_push(f"Rollback: Moved back to images: {os.path.basename(media_info['original_path'])}")
    elif media_info["type"] == "catbox":
        print("Restoring Catbox URL to top of reels_urls.txt...")
        url = media_info["media_url"]
        urls = []
        if os.path.exists(REELS_FILE):
            with open(REELS_FILE, "r") as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
        urls.insert(0, url)
        with open(REELS_FILE, "w") as f:
            f.write("\n".join(urls))
        git_commit_and_push("Rollback: Restored failed Catbox URL")


def create_story_image(local_path):
    try:
        img = Image.open(local_path).convert("RGB")
        target_w, target_h = 1080, 1920
        bg = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        w, h = img.size
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        fg = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        bg.paste(fg, (x_offset, y_offset))
        story_path = "story_temp.jpg"
        bg.save(story_path, quality=95)
        return story_path
    except Exception as e:
        print(f"Error creating story image: {e}")
        return local_path

def upload_to_catbox(file_path):
    try:
        import requests
        print(f"Uploading {file_path} to Catbox for story...")
        with open(file_path, 'rb') as f:
            response = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"Catbox upload failed: {e}")
    return None

if __name__ == "__main__":
    try:
        # Cleanup previously posted files to avoid large repo size
        if os.path.exists(POSTED_FOLDER):
            files = os.listdir(POSTED_FOLDER)
            if files:
                for f in files:
                    os.remove(os.path.join(POSTED_FOLDER, f))
                git_commit_and_push("Cleaned up old posted media")
        
        media_info = get_next_media()
        print(f"Media URL for Graph API: {media_info['media_url']}")
        
        caption = generate_caption(media_info["local_path"])
        
        ig_account_id = get_ig_account_id()
        if not ig_account_id:
            raise Exception("No Instagram account linked to the page.")
            
        success = False
        
        # Prepare Story URL (if image, create blurred 9:16 background)
        story_url = media_info["media_url"]
        if not media_info["is_video"]:
            story_local = create_story_image(media_info["local_path"])
            if story_local != media_info["local_path"]:
                catbox_url = upload_to_catbox(story_local)
                if catbox_url:
                    story_url = catbox_url
                    print(f"Using Catbox URL for story: {story_url}")
        
        # Post to Instagram Feed/Reel
        if post_ig_media(ig_account_id, caption, media_info["media_url"], is_story=False, is_video=media_info["is_video"]):
            success = True
            
        # Post to Instagram Story (using the story_url which has the blurred background for images)
        post_ig_media(ig_account_id, caption, story_url, is_story=True, is_video=media_info["is_video"])
        
        # Post to Facebook
        if media_info["is_video"]:
            # Need to ensure post_fb_video exists or just use feed
            if "post_fb_video" in globals():
                if post_fb_video(caption, media_info["local_path"]):
                    success = True
            else:
                if post_fb_feed(caption, media_info["media_url"]):
                    success = True
            
            if "post_fb_video_story" in globals():
                post_fb_video_story(media_info["local_path"])
        else:
            if post_fb_feed(caption, media_info["media_url"]):
                success = True
            if "post_fb_story" in globals():
                post_fb_story(story_url)
        
        if success:
            print("Successfully posted!")
            # Now we mark it as used!
            if media_info["type"] == "catbox":
                mark_url_as_used(media_info["media_url"], media_info["is_video"])
        else:
            if "handle_failure" in globals():
                handle_failure(media_info)
            else:
                print("All posts failed.")
            
        if os.path.exists(TEMP_VIDEO):
            os.remove(TEMP_VIDEO)
        if os.path.exists("story_temp.jpg"):
            os.remove("story_temp.jpg")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)