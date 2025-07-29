import os
import json
import subprocess
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request
import re

app = Flask(__name__)

TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# --- Command Builder (No changes needed) ---
def get_yt_dlp_command(url):
    # ... This function is correct and needs no changes ...
    base_command = [
        'yt-dlp', '-4', '--no-check-certificate',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        '--add-header', 'Accept-Language: en-US,en;q=0.5',
        '--no-warnings', '--quiet'
    ]
    cookie_file_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if 'facebook.com' in url and os.path.exists(cookie_file_path):
        base_command.extend(['--cookies', cookie_file_path])
    base_command.append(url)
    return base_command

# --- Helper Functions ---
def get_sanitized_filename(title):
    # ... This function is correct ...
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100]

def convert_facebook_url(url):
    # ... This function is correct ...
    if 'facebook.com/share/v/' in url:
        match = re.search(r'facebook\.com/share/v/([^/]+)/', url)
        if match:
            video_id = match.group(1)
            return f'https://www.facebook.com/watch/?v={video_id}'
    return url

# <<< NEW: Re-introducing the pretty label function >>>
def get_standard_label(height):
    """Maps a resolution height to a standard, user-friendly quality label."""
    if height >= 3240: return "4320p (8K)"
    if height >= 1800: return "2160p (4K)"
    if height >= 1260: return "1440p (2K)"
    if height >= 900:  return "1080p (FHD)"
    if height >= 600:  return "720p (HD)"
    if height >= 420:  return "480p (SD)"
    if height >= 300:  return "360p"
    return f"{height}p" # Fallback for any unusual resolutions

def get_video_info(url):
    # ... This function is correct ...
    processed_url = convert_facebook_url(url)
    command = get_yt_dlp_command(processed_url)
    command.insert(1, '--dump-json')
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("!!!!!!!! YT-DLP STDERR (GET_INFO) !!!!!!!!\n", e.stderr)
        return None
    except Exception as e:
        print(f"Error (not from yt-dlp): {e}")
        return None

def parse_formats(info):
    formats_list = []
    title = info.get('title', 'video')
    sanitized_title = get_sanitized_filename(title)
    
    # Audio format
    best_audio = next((f for f in reversed(info.get('formats', [])) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
    if best_audio:
        filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        formats_list.append({'label': "Audio MP3", 'type': 'audio', 'ext': 'mp3', 'filename': f"{sanitized_title}.mp3", 'filesize': filesize_mb})

    # Video formats
    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
    processed_labels = set()
    for f in reversed(video_formats):
        height = f.get('height')
        if not height: continue
        
        # <<< USE THE PRETTY LABEL FUNCTION >>>
        standard_label = get_standard_label(height)
        if standard_label in processed_labels: continue
        processed_labels.add(standard_label)
        
        format_id = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        filesize = f.get('filesize') or f.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        
        formats_list.append({
            'label': standard_label, # Use the pretty label
            'format_id': format_id,
            'type': 'video', 'ext': 'mp4',
            'filename': f"{sanitized_title}_{height}p.mp4",
            'filesize': filesize_mb,
            'height': height  # Store original height for reliable sorting
        })
    
    # The safe sorting function remains the same, ensuring stability
    def sort_key(item):
        if item.get('type') == 'video': return (0, -item.get('height', 0))
        else: return (1, 0)

    return sorted(formats_list, key=sort_key)


# --- API & Core Routes (No changes needed) ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
# ... This function is correct ...

@app.route('/api/download')
# ... This function is correct ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)