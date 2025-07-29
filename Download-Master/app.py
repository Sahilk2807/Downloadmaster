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

# --- Robust Command Builder ---
def get_yt_dlp_command(url):
    """Builds a robust yt-dlp command with a browser disguise."""
    base_command = [
        'yt-dlp', '-4', '--no-check-certificate',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        '--add-header', 'Accept-Language: en-US,en;q=0.5',
        '--no-warnings', '--quiet'
    ]
    # Optional: Use cookies for private/login-required Facebook videos if the file exists.
    cookie_file_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if 'facebook.com' in url and os.path.exists(cookie_file_path):
        base_command.extend(['--cookies', cookie_file_path])
    base_command.append(url)
    return base_command

# --- Helper Functions ---
def get_sanitized_filename(title):
    """Sanitizes a string to be a valid filename."""
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100]

def convert_facebook_url(url):
    """Converts a mobile share URL to a public 'watch' URL."""
    if 'facebook.com/share/v/' in url:
        # Regex to find the video ID from the share link
        match = re.search(r'facebook\.com/share/v/([^/]+)/', url)
        if match:
            video_id = match.group(1)
            # Construct the public, non-login required 'watch' URL
            return f'https://www.facebook.com/watch/?v={video_id}'
    return url

def get_video_info(url):
    """Fetches video information using a processed URL and robust command."""
    processed_url = convert_facebook_url(url)
    command = get_yt_dlp_command(processed_url)
    command.insert(1, '--dump-json')
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        # Log the actual error from yt-dlp for debugging
        print("!!!!!!!! YT-DLP STDERR (GET_INFO) !!!!!!!!\n", e.stderr)
        return None
    except Exception as e:
        print(f"Error (not from yt-dlp): {e}")
        return None

def parse_formats(info):
    """
    Parses video info into a simple, reliable list for the frontend.
    This version uses simple labels and a safe sorting method.
    """
    formats_list = []
    title = info.get('title', 'video')
    sanitized_title = get_sanitized_filename(title)
    
    # Audio format
    best_audio = next((f for f in reversed(info.get('formats', [])) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
    if best_audio:
        filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        formats_list.append({
            'label': "Audio MP3",
            'format_id': best_audio['format_id'],
            'type': 'audio', 'ext': 'mp3',
            'filename': f"{sanitized_title}.mp3",
            'filesize': filesize_mb
        })

    # Video formats
    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
    processed_heights = set()
    for f in reversed(video_formats): # Start from best quality
        height = f.get('height')
        if not height or height in processed_heights:
            continue
        processed_heights.add(height)

        label = f"{height}p"  # Use simple, direct labels like "1080p", "720p"

        # This command tells yt-dlp to merge the best video of this height with the best audio
        format_id = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        filesize = f.get('filesize') or f.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        
        formats_list.append({
            'label': label,
            'format_id': format_id,
            'type': 'video',
            'ext': 'mp4',
            'filename': f"{sanitized_title}_{height}p.mp4",
            'filesize': filesize_mb,
            'height': height  # Store original height for reliable sorting
        })
    
    # A safe sorting function that handles all cases
    def sort_key(item):
        if item.get('type') == 'video':
            # Sort videos by height, highest first
            return (0, -item.get('height', 0))
        else:
            # Group all other types (like audio) at the end
            return (1, 0)

    return sorted(formats_list, key=sort_key)


# --- API & Core Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
def fetch_info():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Could not fetch video information. The URL might be invalid, private, or unsupported.'}), 404
    
    response_data = {
        'title': info.get('title', 'No Title'),
        'thumbnail': info.get('thumbnail', ''),
        'duration': info.get('duration_string', 'N/A'),
        'uploader': info.get('uploader', 'N/A'),
        'formats': parse_formats(info),
        'original_url': url
    }
    return jsonify(response_data)

@app.route('/api/download')
def download_file():
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    filename = request.args.get('filename', 'download')
    ext = request.args.get('ext')
    
    if not all([url, format_id, filename, ext]):
        return "Missing required parameters", 400
    
    processed_url = convert_facebook_url(url)
    temp_filename = f"{uuid.uuid4()}.{ext}"
    command = get_yt_dlp_command(processed_url)
    command.extend(['-f', format_id])
    
    if ext == 'mp3':
        command.extend(['-x', '--audio-format', 'mp3'])
    else:
        command.extend(['--merge-output-format', 'mp4'])
        
    command.extend(['-o', os.path.join(TMP_DIR, temp_filename)])
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except Exception as e:
        print("Download Error:", e)
        return "Error during download process.", 500

    @after_this_request
    def cleanup(response):
        try:
            os.remove(os.path.join(TMP_DIR, temp_filename))
        except OSError as e:
            print(f"Error cleaning up file: {e}")
        return response

    return send_from_directory(TMP_DIR, temp_filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)