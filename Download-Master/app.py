import os
import json
import subprocess
import uuid
import re
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request

app = Flask(__name__)

# Create a temporary directory to store downloads
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# --- Command Builder ---
def get_yt_dlp_command(url):
    """Builds the base yt-dlp command."""
    base_command = [
        'yt-dlp', '-4', '--no-check-certificate',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        '--add-header', 'Accept-Language: en-US,en;q=0.5',
        '--no-warnings', '--quiet',
        '--geo-bypass'  # <<< UPDATED: Added this flag to help with region-locked content
    ]

    # Always use cookies if the file exists, for ALL platforms.
    cookie_file_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookie_file_path):
        base_command.extend(['--cookies', cookie_file_path])

    base_command.append(url)
    return base_command

# --- Helper Functions ---
def get_sanitized_filename(title):
    """Removes invalid characters from a title to make a safe filename."""
    sanitized = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return sanitized[:100] # Limit filename length

def convert_facebook_url(url):
    """Converts new Facebook share URLs to the classic watch URL."""
    if 'facebook.com/share/v/' in url:
        match = re.search(r'facebook\.com/share/v/([^/]+)/', url)
        if match:
            video_id = match.group(1)
            return f'https://www.facebook.com/watch/?v={video_id}'
    return url

def get_standard_label(height):
    """Maps a resolution height to a standard, user-friendly quality label."""
    if height >= 3240: return "4320p (8K)"
    if height >= 1800: return "2160p (4K)"
    if height >= 1260: return "1440p (2K)"
    if height >= 900:  return "1080p (FHD)"
    if height >= 600:  return "720p (HD)"
    if height >= 420:  return "480p (SD)"
    if height >= 300:  return "360p"
    return f"{height}p"

def get_video_info(url):
    """Runs yt-dlp to get video metadata as JSON."""
    processed_url = convert_facebook_url(url)
    command = get_yt_dlp_command(processed_url)
    command.insert(1, '--dump-json')
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"!!!!!!!! YT-DLP STDERR (GET_INFO) !!!!!!!!\n{e.stderr}")
        return None
    except Exception as e:
        print(f"Error running subprocess (get_video_info): {e}")
        return None

def parse_formats(info):
    """Parses the yt-dlp JSON to create a clean list of formats for the frontend."""
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
            'type': 'audio', 'ext': 'mp3',
            'format_id': best_audio.get('format_id'),
            'filename': f"{sanitized_title}.mp3",
            'filesize': filesize_mb
        })

    # Video formats
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

        formats_list.append({
            'label': standard_label,
            'format_id': format_id,
            'type': 'video', 'ext': 'mp4',
            'filename': f"{sanitized_title}_{height}p.mp4",
            'filesize': filesize_mb,
            'height': height
        })

    def sort_key(item):
        if item.get('type') == 'video': return (0, -item.get('height', 0))
        else: return (1, 0)

    return sorted(formats_list, key=sort_key)

# --- API & Core Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
def fetch_info():
    """API endpoint to fetch video info."""
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Could not fetch video information. The link may be private, invalid, or unsupported.'}), 404

    formats = parse_formats(info)
    title = info.get('title', 'Untitled Video')
    thumbnail = info.get('thumbnail')

    return jsonify({
        'title': title,
        'thumbnail': thumbnail,
        'formats': formats,
        'original_url': url
    })

@app.route('/api/download')
def download():
    """API endpoint to download the selected format."""
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
    else: # mp4
        command.extend(['-f', format_id, '--merge-output-format', 'mp4'])

    try:
        subprocess.run(command, check=True, timeout=600) # 10 minute timeout for download
    except subprocess.CalledProcessError as e:
        print(f"!!!!!!!! YT-DLP STDERR (DOWNLOAD) !!!!!!!!\n{e.stderr}")
        return jsonify({'error': 'Download failed. See server logs for details.'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Download timed out.'}), 500

    if not os.path.exists(final_filepath):
        return jsonify({'error': 'Downloaded file not found on server.'}), 500

    @after_this_request
    def cleanup(response):
        try:
            os.remove(final_filepath)
        except Exception as e:
            app.logger.error(f"Error cleaning up file: {e}")
        return response

    return send_from_directory(
        directory=TMP_DIR,
        path=f"{unique_id}.{ext}",
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)