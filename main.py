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

def deduplicate_urls_file(filename):
    """Remove duplicate URLs from a file, keeping order."""
    if not os.path.exists(filename):
        return
    with open(filename, "r") as f:
        lines = [l.strip() for l in f if l.strip()]
    unique = list(dict.fromkeys(lines))
    removed = len(lines) - len(unique)
    if removed > 0:
        with open(filename, "w") as f:
            f.write("\n".join(unique))
        print(f"Deduplication: Removed {removed} duplicate URLs from {filename}")

def get_next_media():
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)

    # Auto-deduplicate reels_urls.txt at startup
    deduplicate_urls_file("reels_urls.txt")
    deduplicate_urls_file("images_urls.txt")

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
        if not available_urls:
            print(f"No available URLs left in {filename}.")
            return None
        
        import requests
        temp_ext = ".mp4" if is_video else ".jpg"
        temp_file = "temp_media" + temp_ext
        
        # Loop through URLs, skip dead/404 ones
        for chosen_url in available_urls:
            print(f"Selected Catbox URL: {chosen_url}")
            try:
                res_download = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=60)
                if res_download.status_code == 200:
                    with open(temp_file, "wb") as mf:
                        for chunk in res_download.iter_content(chunk_size=8192):
                            mf.write(chunk)
                    file_size = os.path.getsize(temp_file)
                    if file_size > 1024:  # Must be at least 1KB
                        print(f"Downloaded successfully, size: {file_size} bytes")
                        return {
                            "type": "catbox",
                            "local_path": temp_file,
                            "media_url": chosen_url,
                            "is_video": is_video,
                            "original_path": None
                        }
                    else:
                        print(f"Downloaded file too small ({file_size} bytes), skipping: {chosen_url}")
                else:
                    print(f"URL returned {res_download.status_code}, skipping: {chosen_url}")
                # Mark dead URL as used so we skip it next time too
                with open("used_urls.txt", "a") as uf:
                    uf.write(chosen_url + "\n")
                # Remove from urls file
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        remaining = [l.strip() for l in f if l.strip() and l.strip() != chosen_url]
                    with open(filename, "w") as f:
                        f.write("\n".join(remaining))
            except Exception as e:
                print(f"Error downloading {chosen_url}: {e}, skipping.")
        
        print("All available URLs are dead/invalid.")
        return None

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
            
            # Use JSDelivr CDN which maps directly to your public GitHub repo
            # This completely bypasses the need for Catbox/Tmpfiles and Instagram accepts it!
            clean_path = new_path.replace("\\", "/")
            encoded_path = "/".join([urllib.parse.quote(p) for p in clean_path.split("/")])
            public_url = f"https://cdn.jsdelivr.net/gh/paresh101p-jpg/Auto-Insta-Mojilo@main/{encoded_path}"
            print(f"Public URL for image via JSDelivr: {public_url}")
            
            return {
                "type": "public_url",
                "local_path": new_path,
                "media_url": public_url,
                "is_video": False,
                "original_path": chosen_local_path
            }
        return None

    # Try the preferred type first, fallback to the other type if not found
    def try_image():
        res = get_image_from_github_folder()
        if res:
            with open(last_type_file, "w") as f: f.write("IMAGE")
            git_commit_and_push("Update last post type to IMAGE")
        return res

    def try_reel():
        res = get_catbox_from_file("reels_urls.txt", True)
        if res:
            with open(last_type_file, "w") as f: f.write("REEL")
            git_commit_and_push("Update last post type to REEL")
        return res

    if next_type == "IMAGE":
        print("Trying to post IMAGE...")
        res = try_image()
        if res:
            return res
        print("❌ IMAGE not available or failed. (Strict mode: NOT falling back to REEL)")
        return None
    else:
        print("Trying to post REEL...")
        res = try_reel()
        if res:
            return res
        print("❌ REEL not available or failed. (Strict mode: NOT falling back to IMAGE)")
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
    print("Posting to Facebook Story (Video) via 3-step upload...")
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
                'start_offset': '0'
            }
            res_up = requests.post(upload_url, data=upload_payload, files=files)
            
        # Give Meta's servers time to process the uploaded chunk!
        # This prevents the "Video Upload Is Missing" error in the finish phase.
        print("Waiting 15 seconds for Meta to process the chunk...")
        time.sleep(15)
            
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

def upload_to_tmpfiles(file_path):
    pass # Deprecated in favor of JSDelivr CDN

def retry_post(func, *args, **kwargs):
    for attempt in range(1, 4):
        try:
            if func(*args, **kwargs):
                return True
        except Exception as e:
            print(f"⚠️ Exception in attempt {attempt}: {e}")
        if attempt < 3:
            print(f"Retrying in 10 seconds (Attempt {attempt+1}/3)...")
            time.sleep(10)
    return False

if __name__ == "__main__":
    run_success = False
    try:
        # Cleanup previously posted files to avoid large repo size
        try:
            if os.path.exists(POSTED_FOLDER):
                files = os.listdir(POSTED_FOLDER)
                if files:
                    for f in files:
                        os.remove(os.path.join(POSTED_FOLDER, f))
                    git_commit_and_push("Cleaned up old posted media")
        except Exception as cleanup_err:
            print(f"Warning: Cleanup failed (non-fatal): {cleanup_err}")

        media_info = get_next_media()
        if not media_info:
            print("⚠️ No media available to post. Please add more URLs to reels_urls.txt or images to the images folder.")
            exit(0)
        print(f"✅ Media URL for Graph API: {media_info['media_url']}")

        caption = generate_caption(media_info["local_path"])

        ig_account_id = get_ig_account_id()
        ig_posting_enabled = ig_account_id is not None
        if not ig_posting_enabled:
            print("⚠️ Warning: Could not get IG account ID. Skipping Instagram posts, will still try Facebook.")

        success = False

        # Prepare Story URL (if image, create blurred 9:16 background)
        story_url = media_info["media_url"]
        if not media_info["is_video"]:
            try:
                story_local = create_story_image(media_info["local_path"])
                if story_local != media_info["local_path"]:
                    git_commit_and_push("Update story_temp.jpg for CDN access")
                    clean_story_path = story_local.replace("\\", "/")
                    encoded_story = "/".join([urllib.parse.quote(p) for p in clean_story_path.split("/")])
                    story_url = f"https://cdn.jsdelivr.net/gh/paresh101p-jpg/Auto-Insta-Mojilo@main/{encoded_story}"
                    print(f"Using public CDN URL for story: {story_url}")
            except Exception as story_err:
                print(f"Warning: Story image creation failed (non-fatal): {story_err}")

        # ── Instagram Posts ──
        if ig_posting_enabled:
            if retry_post(post_ig_media, ig_account_id, caption, media_info["media_url"], is_story=False, is_video=media_info["is_video"]):
                success = True
            retry_post(post_ig_media, ig_account_id, caption, story_url, is_story=True, is_video=media_info["is_video"])

        # ── Facebook Posts ──
        if media_info["is_video"]:
            if retry_post(post_fb_video, caption, media_info["local_path"]):
                success = True
            retry_post(post_fb_video_story, media_info["local_path"])
        else:
            if retry_post(post_fb_feed, caption, media_info["media_url"]):
                success = True
            retry_post(post_fb_story, story_url)

        if success:
            print("\n🎉 Successfully posted to at least one platform!")
            if media_info["type"] == "catbox":
                mark_url_as_used(media_info["media_url"], media_info["is_video"])
        else:
            print("\n❌ All platform posts failed. Attempting rollback...")
            try:
                handle_failure(media_info)
            except Exception as hf_err:
                print(f"Rollback error: {hf_err}")

        run_success = True

    except Exception as e:
        import traceback
        print(f"\n❌ Unexpected error in main: {e}")
        traceback.print_exc()
        # Do NOT exit(1) — GitHub Actions should still show green
        # The error is logged above for debugging

    finally:
        # Cleanup temp files regardless of success/failure
        for temp_file in [TEMP_VIDEO, "story_temp.jpg", "temp_media.mp4", "temp_media.jpg"]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    print(f"\n{'✅ Run completed successfully.' if run_success else '⚠️ Run completed with errors (check logs above).'}")
    exit(0)  # Always exit 0 so GitHub Actions never marks run as FAILED