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
    base_command = [
        'yt-dlp', '-4', '--no-check-certificate',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        '--add-header', 'Accept-Language: en-US,en;q=0.5',
        '--no-warnings', '--quiet'
    ]
    # NOTE: The cookie file method is the only reliable way for private/login-required Facebook videos.
    # Public watch links will continue to work without it.
    if 'facebook.com' in url and os.path.exists(os.path.join(os.path.dirname(__file__), 'cookies.txt')):
        base_command.extend(['--cookies', 'cookies.txt'])
    base_command.append(url)
    return base_command


# --- Helper Functions ---
def get_sanitized_filename(title):
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100]

def convert_facebook_url(url):
    if 'facebook.com/share/v/' in url:
        match = re.search(r'facebook\.com/share/v/([^/]+)/', url)
        if match:
            video_id = match.group(1)
            return f'https://www.facebook.com/watch/?v={video_id}'
    return url

def get_standard_label(height):
    if height >= 3240: return "4320p (8K)"
    if height >= 1800: return "2160p (4K)"
    if height >= 1260: return "1440p (2K)"
    if height >= 900:  return "1080p (FHD)"
    if height >= 600:  return "720p (HD)"
    if height >= 420:  return "480p (SD)"
    if height >= 300:  return "360p"
    return "240p"

def get_video_info(url):
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
    
    best_audio = next((f for f in reversed(info.get('formats', [])) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
    if best_audio:
        filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        formats_list.append({'label': "Audio MP3", 'format_id': best_audio['format_id'], 'type': 'audio', 'ext': 'mp3', 'filename': f"{sanitized_title}.mp3", 'filesize': filesize_mb})

    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
    processed_labels = set()
    for f in reversed(video_formats):
        height = f.get('height')
        if not height: continue
        
        standard_label = get_standard_label(height)
        if standard_label in processed_labels: continue
        processed_labels.add(standard_label)
        
        format_id = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        filesize = f.get('filesize') or f.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        
        formats_list.append({'label': standard_label, 'format_id': format_id, 'type': 'video', 'ext': 'mp4', 'filename': f"{sanitized_title}_{height}p.mp4", 'filesize': filesize_mb})
    
    # <<< THE BUG FIX: A completely safe sorting function >>>
    def sort_key(item):
        if item['type'] == 'audio':
            return (1, 0)  # Group audio at the end
        
        # Safely find the number in the label (like 720 from "720p (HD)")
        match = re.search(r'(\d+)', item['label'])
        if match:
            # Sort by highest number first
            return (0, -int(match.group(1)))
        
        return (2, 0) # Fallback for anything else

    return sorted(formats_list, key=sort_key)


# --- API & Core Routes (No changes needed) ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
def fetch_info():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({'error': 'URL is required'}), 400
    info = get_video_info(url)
    if not info: return jsonify({'error': 'Could not fetch video information. The URL might be invalid, private, or unsupported.'}), 404
    response_data = {'title': info.get('title', 'No Title'),'thumbnail': info.get('thumbnail', ''),'duration': info.get('duration_string', 'N/A'),'uploader': info.get('uploader', 'N/A'),'formats': parse_formats(info),'original_url': url}
    return jsonify(response_data)

@app.route('/api/download')
def download_file():
    # This function is correct and needs no changes
    url = request.args.get('url'); format_id = request.args.get('format_id'); filename = request.args.get('filename', 'download'); ext = request.args.get('ext')
    if not all([url, format_id, filename, ext]): return "Missing required parameters", 400
    processed_url = convert_facebook_url(url)
    temp_filename = f"{uuid.uuid4()}.{ext}"; command = get_yt_dlp_command(processed_url); command.extend(['-f', format_id])
    if ext == 'mp3': command.extend(['-x', '--audio-format', 'mp3'])
    else: command.extend(['--merge-output-format', 'mp4'])
    command.extend(['-o', os.path.join(TMP_DIR, temp_filename)])
    try: subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except Exception as e: print("Download Error:", e); return f"Error during download process.", 500
    @after_this_request
    def cleanup(response):
        try: os.remove(os.path.join(TMP_DIR, temp_filename))
        except OSError as e: print(f"Error cleaning up file: {e}")
        return response
    return send_from_directory(TMP_DIR, temp_filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)