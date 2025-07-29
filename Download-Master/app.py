import os
import json
import subprocess
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request

app = Flask(__name__)

TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# --- Helper Functions ---

def get_sanitized_filename(title):
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100]

def get_video_info(url):
    """
    Uses yt-dlp to extract video information.
    The -4 flag forces yt-dlp to use IPv4, which can solve connection issues on cloud hosts.
    """
    command = [
        'yt-dlp',
        '-4',  # <-- THE FIX
        '--dump-json',
        '--no-warnings',
        '--quiet',
        url
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"Error fetching video info: {e}")
        return None

def parse_formats(info):
    formats_list = []
    title = info.get('title', 'video')
    sanitized_title = get_sanitized_filename(title)
    
    best_audio = next((f for f in reversed(info.get('formats', [])) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
    if best_audio:
        filesize = best_audio.get('filesize') or best_audio.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        formats_list.append({
            'label': f"Audio MP3 ({best_audio.get('abr', 0)}k)",
            'format_id': best_audio['format_id'],
            'type': 'audio', 'ext': 'mp3',
            'filename': f"{sanitized_title}.mp3",
            'filesize': filesize_mb,
        })

    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
    processed_resolutions = set()
    for f in reversed(video_formats):
        height = f.get('height')
        if not height or height in processed_resolutions: continue
        processed_resolutions.add(height)
        
        format_id = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        filesize = f.get('filesize') or f.get('filesize_approx')
        filesize_mb = f"~{filesize / (1024*1024):.2f} MB" if filesize else "N/A"
        label = f"{height}p"

        formats_list.append({
            'label': label,
            'format_id': format_id,
            'type': 'video', 'ext': 'mp4',
            'filename': f"{sanitized_title}_{height}p.mp4",
            'filesize': filesize_mb,
        })
    return sorted(formats_list, key=lambda x: (x['type'], -int(x['label'].split('p')[0])) if 'p' in x['label'] else 0)


# --- API & Core Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/api/fetch_info', methods=['POST'])
def fetch_info():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({'error': 'URL is required'}), 400
    info = get_video_info(url)
    if not info: return jsonify({'error': 'Could not fetch video information. The URL might be invalid, private, or unsupported.'}), 404
    
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
    
    if not all([url, format_id, filename, ext]): return "Missing required parameters", 400

    temp_filename = f"{uuid.uuid4()}.{ext}"
    command = [
        'yt-dlp',
        '-4', # <-- THE FIX
        '--no-warnings',
        '-f', format_id
    ]
    
    if ext == 'mp3':
        command.extend(['-x', '--audio-format', 'mp3'])
    else:
        command.extend(['--merge-output-format', 'mp4'])
        
    command.extend(['-o', os.path.join(TMP_DIR, temp_filename), url])
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Download error: {e}")
        return f"Error during download process: {e}", 500

    @after_this_request
    def cleanup(response):
        try: os.remove(os.path.join(TMP_DIR, temp_filename))
        except OSError as e: print(f"Error cleaning up file: {e}")
        return response

    return send_from_directory(TMP_DIR, temp_filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)