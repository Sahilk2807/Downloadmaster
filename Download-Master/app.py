import os
import json
import subprocess
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request, url_for

# Initialize Flask App
app = Flask(__name__)

# Create a temporary directory for downloads
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# --- Helper Functions (No changes from previous version) ---
def get_sanitized_filename(title):
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100]

def get_video_info(url):
    command = ['yt-dlp', '--dump-json', '--no-warnings', '--quiet', url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error fetching video info: {e}")
        return None

def parse_formats(info):
    formats_list = []
    title = info.get('title', 'video')
    sanitized_title = get_sanitized_filename(title)
    
    # Audio Only (MP3)
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

    # Video Formats (merged)
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

# --- SEO and Core Routes ---

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/robots.txt')
def robots_txt():
    """Serves the robots.txt file."""
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Serves the sitemap.xml file."""
    return send_from_directory(app.static_folder, 'sitemap.xml')

# --- API Routes (No changes) ---

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
    command = ['yt-dlp', '--no-warnings', '-f', format_id]
    
    if ext == 'mp3':
        command.extend(['-x', '--audio-format', 'mp3'])
    else:
        command.extend(['--merge-output-format', 'mp4'])
        
    command.extend(['-o', os.path.join(TMP_DIR, temp_filename), url])
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Download error: {e.stderr}")
        return f"Error during download process: {e.stderr}", 500

    @after_this_request
    def cleanup(response):
        try:
            os.remove(os.path.join(TMP_DIR, temp_filename))
        except OSError as e:
            print(f"Error cleaning up file: {e}")
        return response

    return send_from_directory(TMP_DIR, temp_filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    # For production, use a proper WSGI server like Gunicorn or Waitress
    app.run(host='0.0.0.0', port=5001, debug=False)