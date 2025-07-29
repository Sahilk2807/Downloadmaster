# Download Master 🚀

**Download Master** is a modern, mobile-first web application that allows users to download videos and audio from all major platforms. It's built with a Python Flask backend, a sleek Tailwind CSS frontend, and is powered by the robust `yt-dlp` download engine.

This version is optimized for search engines (SEO) and ready for easy verification with Google Search Console.

 <!-- Replace with a screenshot of your app -->

## ✨ Features

- **Mobile-First Design**: Clean, responsive UI that works perfectly on any device.
- **Wide Platform Support**:
  - YouTube (up to 8K)
  - TikTok (watermark-free)
  - Instagram (Reels, Posts, IGTV)
  - Facebook, Twitter (X), Vimeo, Dailymotion, Reddit, SoundCloud, and more.
- **Dynamic Previews**: See video thumbnail, title, and duration before downloading.
- **Multiple Formats**: Choose from various video qualities (144p to 8K) or download as audio-only (MP3).
- **Intelligent Merging**: Automatically merges the best video and audio streams for high-quality downloads.
- **User-Friendly Interface**:
  - Skeleton loading screens for a smooth user experience.
  - Dark mode toggle.
  - Clear error handling.
- **SEO Optimized**: Includes `robots.txt`, `sitemap.xml`, and necessary meta tags for easy indexing and verification on Google.
- **Ad Placeholders**: Ready for Adsterra banner and social bar ads.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Download Engine**: `yt-dlp`
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **Dependencies**: `ffmpeg` (required by yt-dlp for merging/conversion)

---

## 🚀 Deployment & Setup

This app is designed for easy deployment on platforms like **Render**, **Replit**, or any VPS.

### Prerequisites

You must have **Python 3**, **pip**, and **FFmpeg** installed on your system.

```bash
# On Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-pip ffmpeg -y

# On macOS (using Homebrew)
brew install python ffmpeg
```

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Download-Master.git
    cd Download-Master
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install `yt-dlp` (it's in requirements, but ensure it's up-to-date):**
    ```bash
    pip install --upgrade yt-dlp
    ```
    
4.  **Run the Flask App:**
    ```bash
    python app.py
    ```
    The app will be running at `http://127.0.0.1:5001`.

### 🔍 Google Search Console & SEO Setup

To get your site indexed and verified by Google, follow these steps:

**Step 1: Update Your Domain**

You **must** replace the placeholder `https://YOUR_DOMAIN.com` with your actual domain in the following files:
- `templates/index.html` (for canonical and Open Graph URLs)
- `static/robots.txt`
- `static/sitemap.xml`

**Step 2: Verify Ownership with Google**

1. Go to [Google Search Console](https://search.google.com/search-console/about) and add your domain as a new property.
2. Google will ask you to verify ownership. Choose the **HTML tag** method.
3. Google will provide a meta tag that looks like this:
   `<meta name="google-site-verification" content="YourUniqueVerificationString" />`
4. Copy this entire line.
5. Open `templates/index.html`.
6. Paste the meta tag where you see the comment: `<!--! PASTE GOOGLE SEARCH CONSOLE VERIFICATION META TAG HERE -->`.
7. Save the file and redeploy your application.
8. Go back to Google Search Console and click "Verify". Google will now be able to find the tag on your homepage and confirm your ownership.

**Step 3: Submit Your Sitemap**

Once verified, go to the "Sitemaps" section in your Google Search Console dashboard. Enter `sitemap.xml` as the sitemap URL and submit it. This will help Google crawl your site more effectively.

### Deployment to Render (Free Tier)

1.  Fork this repository to your own GitHub account.
2.  Go to [Render](https://render.com/) and create a new "Web Service".
3.  Connect your GitHub account and select your forked `Download-Master` repository.
4.  Render will auto-detect a Python app. Configure it with the following settings:
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `gunicorn app:app` (Gunicorn is a production-ready server)
    - **Add Environment Variable**: Set `PYTHON_VERSION` to a recent version like `3.10.6`.
5.  Click "Create Web Service". Render will deploy your app. Don't forget to add FFmpeg via a buildpack or Docker if Render's native environment doesn't include it.

---

## 📄 License

This project is open-source and available under the MIT License.