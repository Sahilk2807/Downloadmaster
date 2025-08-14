import os
import json
import subprocess
import uuid
import re
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request
import requests

app = Flask(__name__)

TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# --- SECTION 1: Logic for the External YouTube API ---
def get_youtube_info_from_api(url):
    """Fetches YouTube video info using the external NepCoder API."""
    try:
        api_url = f"https://nepcoderapis.pages.dev/api/v1/video/download?url={url}"
        response = requests.get(api_url, timeout=45)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"): return None

        video_details = data.get("videoDetails", {})
        download_links = data.get("downloadLinks", {})
        formats_list = []
        
        for item in download_links.get("mp4", []):
            formats_list.append({
                "label": item.get("qualityLabel", "Unknown Quality"),
                "filesize": item.get("size", "N/A"),
                "type": "video",
                "direct_url": item.get("url")
            })
        for item in download_links.get("mp3", []):
             formats_list.append({
                "label": "Audio MP3",
                "filesize": item.get("size", "N/A"),
                "type": "audio",
                "direct_url": item.get("url")
            })
        return {
            'title': video_details.get('title', 'No Title'),
            'thumbnail': video_details.get('thumbnail', ''),
            'duration': video_details.get('duration', 'N/A'),
            'uploader': 'YouTube',
            'formats': formats_list,
            'original_url': url
        }
    except Exception as e:
        print(f"Error calling NepCoder API: {e}")
        return None

# --- SECTION 2: Logic for ALL OTHER Platforms ---
def get_info_with_yt_dlp(url):
    """The original method, now used for non-YouTube sites."""
    processed_url = convert_facebook_url(url)
    command = get_yt_dlp_command(processed_url)
    command.insert(1, '--dump-json')
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        info = json.loads(result.stdout)
        return {
            'title': info.get('title', 'Untitled Video'),
            'thumbnail': info.get('thumbnail'),
            'uploader': info.get('uploader', 'N/A'),
            'duration': info.get('duration_string', 'N/A'),
            'formats': parse_yt_dlp_formats(info),
            'original_url': url
        }
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        return None

def parse_yt_dlp_formats(info):
    """Your original format parser."""
    formats_list = []
    title = info.get('title', 'video')
    sanitized_title = get_sanitized_filename(title)
    best_audio = next((f for f in reversed(info.get('formats', [])) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
    if best_audio:
        filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        formats_list.append({'label': "Audio MP3", 'type': 'audio', 'ext': 'mp3', 'format_id': best_audio.get('format_id'), 'filename': f"{sanitized_title}.mp3", 'filesize': filesize_mb})
    
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
        formats_list.append({'label': standard_label, 'format_id': format_id, 'type': 'video', 'ext': 'mp4', 'filename': f"{sanitized_title}_{height}p.mp4", 'filesize': filesize_mb, 'height': height})
    
    def sort_key(item):
        if item.get('type') == 'video': return (0, -item.get('height', 0))
        else: return (1, 0)
    return sorted(formats_list, key=sort_key)

# <<< THIS IS THE SECTION WITH THE CORRECTED SYNTAX >>>
# --- Helper functions from your file (Expanded for correctness) ---
def get_yt_dlp_command(url):
    base_command = ['yt-dlp', '-4', '--no-check-certificate', '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', '--add-header', 'Accept-Language: en-US,en;q=0.5', '--no-warnings', '--quiet', '--geo-bypass']
    cookie_file_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookie_file_path):
        base_command.extend(['--cookies', cookie_file_path])
    base_command.append(url)
    return base_command

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
    return f"{height}p"

# --- API & Core Routes ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
def fetch_info():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({'error': 'URL is required.'}), 400

    if 'youtube.com' in url or 'youtu.be' in url:
        print(f"Detected YouTube URL. Using external API for: {url}")
        info = get_youtube_info_from_api(url)
    else:
        print(f"Detected non-YouTube URL. Using internal yt-dlp for: {url}")
        info = get_info_with_yt_dlp(url)

    if not info: return jsonify({'error': 'Could not fetch video information. The link may be private, invalid, or unsupported.'}), 404
    return jsonify(info)


@app.route('/api/download')
def download():
    """This endpoint is now ONLY used for non-YouTube platforms."""
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    filename = request.args.get('filename')
    ext = request.args.get('ext')

    if not all([url, format_id, filename, ext]):
        return jsonify({'error': 'Missing required parameters for download.'}), 400
    
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(TMP_DIR, f"{unique_id}.%(ext)s")
    final_filepath = os.path.join(TMP_DIR, f"{unique_id}.{ext}")
    command = get_yt_dlp_command(url)
    command.extend(['-o', output_template])
    
    if ext == 'mp3':
        command.extend(['-f', 'bestaudio/best', '--extract-audio', '--audio-format', 'mp3'])
    else:
        command.extend(['-f', format_id, '--merge-output-format', 'mp4'])
    
    try:
        subprocess.run(command, check=True, timeout=600)
    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({'error': 'Download failed.'}), 500
    
    if not os.path.exists(final_filepath):
        return jsonify({'error': 'Downloaded file not found on server.'}), 500
    
    @after_this_request
    def cleanup(response):
        try:
            os.remove(final_filepath)
        except Exception as e:
            app.logger.error(f"Error cleaning up file: {e}")
        return response
    
    return send_from_directory(directory=TMP_DIR, path=f"{unique_id}.{ext}", as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)