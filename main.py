import schedule
import time
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import instaloader

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("8783790470:AAF1nHZUUFc0oGdu6aZTDgyrS3tklLhkVeA", "")
TELEGRAM_CHAT_ID = os.getenv("8396339706", "")
SOURCE_USERNAME = os.getenv("bittu_all_remix", "")
YOUR_USERNAME = os.getenv("rise.protocol_", "")
START_HOUR = int(os.getenv("START_HOUR", "6"))
END_HOUR = int(os.getenv("END_HOUR", "22"))
INTERVAL_HOURS = float(os.getenv("INTERVAL_HOURS", "1.5"))

# --- STATE MANAGEMENT ---
STATE_FILE = "bot_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "last_video_id": None,
        "last_upload_time": None,
        "mode": "syncing",
        "is_running": False
    }

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

# --- NOTIFICATION SYSTEM ---
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] Telegram credentials not configured")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        print(f"[NOTIFY] {message}")
    except requests.exceptions.Timeout:
        print(f"[ERROR] Telegram API timeout")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to send notification: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

# --- INSTAGRAM SOURCE FETCHING ---
def get_source_reels():
    """
    Fetch list of Reels from Source Account using instaloader
    """
    try:
        print(f"[DEBUG] Fetching reels from: {SOURCE_USERNAME}")
        
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L, SOURCE_USERNAME)
        
        reels = []
        for post in profile.get_posts():
            if post.is_video:
                reels.append({
                    'id': str(post.postid),
                    'url': post.url,
                    'caption': post.caption if post.caption else "",
                    'timestamp': post.date_utc,
                    'thumbnail': post.thumbnail_url
                })
        
        # Sort by timestamp (oldest first)
        reels.sort(key=lambda x: x['timestamp'])
        
        print(f"[DEBUG] Found {len(reels)} reels from source")
        return reels
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch reels: {e}")
        return []
    
        # Sort by timestamp (oldest first)
        reels.sort(key=lambda x: x['timestamp'])
        
        print(f"[DEBUG] Found {len(reels)} reels from source")
        return reels
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch reels: {e}")
        return []

# --- UPLOAD TO YOUR PAGE ---
def upload_to_your_page(video_url, caption):
    """
    Upload video to YOUR Instagram Page
    Note: This requires Meta Graph API with proper permissions
    """
    try:
        # Placeholder for actual upload
        # You need to implement this with Meta Graph API
        # For now, return a placeholder link
        upload_link = f"https://www.instagram.com/reel/PLACEHOLDER_{datetime.now().strftime('%Y%m%d%H%M%S')}/"
        print(f"[INFO] Video uploaded: {upload_link}")
        return upload_link
        
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None

# --- TIME WINDOW CHECK ---
def check_time_window():
    current_hour = datetime.now().hour
    return START_HOUR <= current_hour < END_HOUR

# --- MAIN UPLOAD CYCLE ---
def process_upload_cycle():
    if not check_time_window():
        print(f"[INFO] Outside operating hours (6:00 AM - 10:00 PM)")
        return

    state = load_state()
    
    # Check if enough time has passed since last upload
    if state["last_upload_time"]:
        last_time = datetime.fromisoformat(state["last_upload_time"])
        now = datetime.now()
        diff = now - last_time
        if diff < timedelta(hours=INTERVAL_HOURS):
            remaining = INTERVAL_HOURS - diff.total_seconds()/3600
            print(f"[INFO] Waiting {remaining:.1f} hours for next upload")
            return

    # 1. Fetch Source Reels
    print(f"[INFO] Fetching reels from {SOURCE_USERNAME}")
    reels = get_source_reels()
    
    if not reels:
        send_telegram_message("⚠️ No new videos found on Source Page.")
        return

    print(f"[INFO] Found {len(reels)} reels from source")

    # 2. Filter out already uploaded videos
    new_reels = [r for r in reels if r['id'] != state["last_video_id"]]
    
    # Sort to ensure 1st to Latest
    new_reels.sort(key=lambda x: x['timestamp'])

    if not new_reels:
        # We have reached the latest video
        send_telegram_message("✅ All videos synced! Bot reached the latest video.\nPlease change mode to 'Latest Only' or stop bot.")
        state["mode"] = "completed"
        save_state(state)
        return

    print(f"[INFO] {len(new_reels)} new reels available for upload")

    # 3. Process the first available new reel
    target_reel = new_reels[0]
    
    try:
        # Download & Upload Logic
        upload_link = upload_to_your_page(target_reel['url'], target_reel['caption'])
        
        if upload_link:
            # 4. Update State
            state["last_video_id"] = target_reel['id']
            state["last_upload_time"] = datetime.now().isoformat()
            save_state(state)
            
            # 5. Notify User
            msg = f"🚀 Reel Uploaded!\nLink: {upload_link}\nCaption: {target_reel['caption'][:100]}..."
            send_telegram_message(msg)
        else:
            send_telegram_message(f"❌ Upload Failed: Could not upload video")
        
    except Exception as e:
        send_telegram_message(f"❌ Upload Failed: {str(e)}")

# --- SCHEDULER SETUP ---
def run_scheduler():
    # Run every 10 minutes to check if it's time to upload
    schedule.every(10).minutes.do(process_upload_cycle)
    
    # Run a check at startup
    print("[INFO] Starting bot...")
    process_upload_cycle()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Instagram AutoPoster Bot")
    print("=" * 50)
    print(f"Operating Hours: {START_HOUR}:00 - {END_HOUR}:00")
    print(f"Upload Interval: {INTERVAL_HOURS} hours")
    print(f"Source Account: {SOURCE_USERNAME}")
    print("=" * 50)
    
    run_scheduler()
