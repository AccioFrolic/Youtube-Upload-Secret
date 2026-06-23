import os
import yt_dlp
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# 1. READ SECRETS FROM GITHUB ACTIONS MEMORY
def get_youtube_client():
    creds = Credentials(
        token=None,
        client_id=os.environ.get("YT_CLIENT_ID"),
        client_secret=os.environ.get("YT_CLIENT_SECRET"),
        refresh_token=os.environ.get("YT_REFRESH_TOKEN"),
        token_uri="https://googleapis.com"
    )
    return build("youtube", "v3", credentials=creds)

# 2. UPLOAD MECHANISM
def upload_to_youtube(file_path, video_title):
    try:
        youtube = get_youtube_client()
        body = {
            "snippet": {
                "title": video_title[:100],
                "description": "Automated Short content deployment via GitHub Actions.",
                "categoryId": "20", # People & Blogs
                "tags": ["shorts", "viral", "automation"]
            },
            "status": {"privacyStatus": "private"} # Safely private first for review
        }
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        print("📤 Uploading bytes directly from runner container...")
        response = request.execute()
        print(f"✅ Video uploaded successfully! Video ID: {response.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

# 3. PIPELINE SCHEDULER EXECUTION
def run_daily_pipeline():
    search_topic = "Gaming" # Change this to any niche you want
    output_dir = "." # GitHub runner allows local directory storage natively
    
    ydl_opts = {
        'playlistend': 100, # Scan the top 10 items
        'outtmpl': os.path.join(output_dir, 'downloaded_short.%(ext)s'),
        
        # STRICTIONS: Only Shorts (<=60s), Creative Commons, Highly Engaged, Past 6 Months
        'match_filter': yt_dlp.utils.match_filter_func(
            "duration <= 60 & license *= 'Creative Commons' & view_count >= 50000 & upload_date >= today-6month"
        )
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"📡 Searching for: {search_topic}...")
            info = ydl.extract_info(f"ytsearch:{search_topic}", download=True)
            
            # Extract actual details of the matching video that passed filters
            if 'entries' in info and len(info['entries']) > 0:
                for entry in info['entries']:
                    if entry is not None:
                        local_file = ydl.prepare_filename(entry)
                        title = entry.get('title', 'Automated Short')
                        
                        # Process upload
                        upload_to_youtube(local_file, title)
                        return
                print("❌ No videos in search cluster matched your strict filters today.")
    except Exception as e:
        print(f"Pipeline error: {e}")

if __name__ == "__main__":
    run_daily_pipeline()
