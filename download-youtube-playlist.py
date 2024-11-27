import os
import shutil
import time
import yt_dlp
from pathlib import Path
import argparse

# Define paths
VIDEOS_DIR = './videos'
DOWNLOAD_TRACKER = os.path.join(VIDEOS_DIR, 'downloaded_urls.txt')

# Create videos directory if it doesn't exist
os.makedirs(VIDEOS_DIR, exist_ok=True)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Download YouTube playlist videos.')
    parser.add_argument('playlist_url', 
                       help='The YouTube playlist URL to download')
    return parser.parse_args()

def get_safe_filename(url):
    """Generate a safe filename from the video URL"""
    return url.split('watch?v=')[1]

def check_disk_space(required_space_mb, extra_space_mb=500):
    total, used, free = shutil.disk_usage(VIDEOS_DIR)
    free_mb = free // (2**20)
    return free_mb >= (required_space_mb + extra_space_mb)

def load_cookies(cookie_file='cookies.txt'):
    """Load cookies from the specified file"""
    if not os.path.exists(cookie_file):
        print(f"Warning: Cookie file {cookie_file} not found!")
        return None
    
    try:
        cookies = MozillaCookieJar(cookie_file)
        cookies.load()
        return cookies
    except Exception as e:
        print(f"Error loading cookies: {str(e)}")
        return None

def load_downloaded_videos():
    """Load the list of already downloaded videos"""
    if not os.path.exists(DOWNLOAD_TRACKER):
        # Create the file if it doesn't exist
        with open(DOWNLOAD_TRACKER, 'w') as f:
            pass
        return set()
    
    with open(DOWNLOAD_TRACKER, 'r') as f:
        return set(line.strip() for line in f)

def save_downloaded_video(video_url):
    """Save the URL of a successfully downloaded video"""
    with open(DOWNLOAD_TRACKER, 'a') as f:
        f.write(video_url + '\n')

def download_with_retry(url, position, title, max_retries=3, delay=5):
    """Attempts to download a video multiple times before giving up"""
    safe_title = "".join(c for c in title if c not in '<>:"/\\|?*')
    filename = f"{position:03d} - {safe_title}.%(ext)s"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(VIDEOS_DIR, filename),
        'cookiefile': 'cookies.txt',
        'ignoreerrors': False,
        'no_warnings': False,
    }
    
    for attempt in range(max_retries):  # Now will only try 3 times
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True, None
            
        except Exception as e:
            print(f'Attempt {attempt + 1}/{max_retries} failed: {str(e)}')
            if attempt < max_retries - 1:
                print(f'Waiting {delay} seconds before retrying...')
                time.sleep(delay)
            else:
                return False, str(e)

def get_playlist_info(playlist_url):
    """Get detailed playlist information including video positions"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        # Create a mapping of video_id to its position and title
        video_info = {
            entry['id']: {
                'position': entry.get('playlist_index', idx + 1),
                'title': entry.get('title', 'Unknown Title'),
                'url': f"https://www.youtube.com/watch?v={entry['id']}"
            }
            for idx, entry in enumerate(playlist_info['entries'])
        }
        return video_info

def rename_video_file(video_id, position, title):
    """Rename a video file from ID-based name to position-based name with title"""
    video_dir = Path(VIDEOS_DIR)
    # Look for any file with the video ID as its name
    existing_file = next(video_dir.glob(f"{video_id}.*"), None)
    
    if existing_file:
        # Create new filename: "001 - Video Title.ext"
        safe_title = "".join(c for c in title if c not in '<>:"/\\|?*')  # Remove invalid chars
        new_name = f"{position:03d} - {safe_title}{existing_file.suffix}"
        new_path = existing_file.parent / new_name
        
        try:
            existing_file.rename(new_path)
            print(f"Renamed: {existing_file.name} -> {new_name}")
            return True
        except Exception as e:
            print(f"Error renaming file: {str(e)}")
            return False
    else:
        print(f"File not found for video ID: {video_id}")
    return False

def rename_existing_videos(video_info, downloaded_urls):
    """Rename all existing videos to the correct format based on playlist position"""
    print("\nRenaming existing videos...")
    renamed_count = 0
    for video_id, info in video_info.items():
        video_url = info['url']
        if video_url in downloaded_urls:
            position = info['position']
            title = info['title']
            if rename_video_file(video_id, position, title):
                renamed_count += 1
    print(f"Renamed {renamed_count} videos to include position and title")

# Main execution
if __name__ == "__main__":
    args = parse_arguments()
    playlist_url = args.playlist_url

    try:
        # Get playlist info with positions
        video_info = get_playlist_info(playlist_url)
        total_videos = len(video_info)
        print(f"Found {total_videos} videos in playlist")
        
        downloaded_urls = load_downloaded_videos()
        print(f"Found {len(downloaded_urls)} previously downloaded videos")
        
        # Rename existing videos first
        rename_existing_videos(video_info, downloaded_urls)
        
        # Download remaining videos
        for video_id, info in video_info.items():
            video_url = info['url']
            if video_url in downloaded_urls:
                print(f'Skipping already downloaded video: {video_url}')
                continue
            
            position = info['position']
            print(f'Processing video {position}/{total_videos}: {video_url}')
            
            try:
                time.sleep(5)  # Delay between downloads
                success, error = download_with_retry(video_url, position, info['title'])
                if not success:
                    print(f'Failed to download video after retries: {error}')
                    print('Stopping script as all videos are required.')
                    exit(1)
                
                save_downloaded_video(video_url)
                print(f'Download completed! ({position}/{total_videos})')

            except Exception as e:
                print(f'Error processing video {position}/{total_videos}: {str(e)}')
                print('Stopping script as all videos are required.')
                exit(1)

    except Exception as e:
        print(f'Error accessing playlist: {str(e)}')
        exit(1)

    print("All videos downloaded successfully!")
