document.addEventListener('DOMContentLoaded', () => {
    // --- All Element Selections ---
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('urlInput');
    const fetchButton = document.getElementById('fetchButton');
    const downloadButton = document.getElementById('downloadButton');
    const resultContainer = document.getElementById('result-container');
    const skeleton = document.getElementById('skeleton');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    const darkModeToggle = document.getElementById('darkModeToggle');
    const themeIconLight = document.getElementById('theme-icon-light');
    const themeIconDark = document.getElementById('theme-icon-dark');
    
    let currentVideoData = null;

    // --- Dark Mode Logic ---
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            themeIconLight.classList.add('hidden');
            themeIconDark.classList.remove('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            themeIconLight.classList.remove('hidden');
            themeIconDark.classList.add('hidden');
        }
    };
    const toggleTheme = () => {
        const newTheme = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };
    darkModeToggle.addEventListener('click', toggleTheme);
    const initializeTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            applyTheme(savedTheme);
        } else {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark ? 'dark' : 'light');
        }
    };
    initializeTheme();


    // --- Form Submission Logic (Fetch Button) ---
    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) {
            showError("Please paste a URL first.");
            return;
        }

        showSkeleton(); // This function was missing before
        fetchButton.disabled = true;
        fetchButton.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Fetching...</span>`;

        try {
            const response = await fetch('/api/fetch_info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Could not fetch video information.');
            }
            const data = await response.json();
            currentVideoData = data;
            displayResult(data);
        } catch (error) {
            showError(error.message); // This function was also missing
        } finally {
            fetchButton.disabled = false;
            fetchButton.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg><span>Fetch</span>`;
        }
    });

    // --- <<< THE MISSING FUNCTIONS ARE NOW HERE >>> ---
    // --- UI Update Functions ---
    const showSkeleton = () => {
        resultDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
        skeleton.classList.remove('hidden');
    };

    const showError = (message) => {
        skeleton.classList.add('hidden');
        resultDiv.classList.add('hidden');
        errorMessage.textContent = message;
        errorDiv.classList.remove('hidden');
    };

    const displayResult = (data) => {
        skeleton.classList.add('hidden');
        errorDiv.classList.add('hidden');
        document.getElementById('thumbnail').src = data.thumbnail;
        document.getElementById('title').textContent = data.title;
        document.getElementById('meta').textContent = `By ${data.uploader} · ${data.duration}`;
        const formatSelector = document.getElementById('formatSelector');
        formatSelector.innerHTML = '';
        
        const videoFormats = data.formats.filter(f => f.type === 'video');
        const audioFormats = data.formats.filter(f => f.type === 'audio');
        
        if (videoFormats.length > 0) {
            const videoGroup = document.createElement('optgroup');
            videoGroup.label = 'Video (MP4)';
            videoFormats.forEach((format) => {
                const option = document.createElement('option');
                option.value = data.formats.indexOf(format);
                option.textContent = `${format.label} (~${format.filesize})`;
                videoGroup.appendChild(option);
            });
            formatSelector.appendChild(videoGroup);
        }
        
        if (audioFormats.length > 0) {
            const audioGroup = document.createElement('optgroup');
            audioGroup.label = 'Audio';
            audioFormats.forEach((format) => {
                const option = document.createElement('option');
                option.value = data.formats.indexOf(format);
                option.textContent = `${format.label} (~${format.filesize})`;
                audioGroup.appendChild(option);
            });
            formatSelector.appendChild(audioGroup);
        }
        resultDiv.classList.remove('hidden');
    };

    // --- Download Logic with Animation ---
    downloadButton.addEventListener('click', () => {
        const selectedIndex = document.getElementById('formatSelector').value;
        if (selectedIndex === null || !currentVideoData) {
            showError("Please select a format to download.");
            return;
        }
        
        const selectedFormat = currentVideoData.formats[selectedIndex];
        const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoData.original_url)}&format_id=${encodeURIComponent(selectedFormat.format_id)}&filename=${encodeURIComponent(selectedFormat.filename)}&ext=${encodeURIComponent(selectedFormat.ext)}`;

        // 1. Disable the button and show a spinner
        downloadButton.disabled = true;
        downloadButton.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Processing...</span>`;

        // 2. Trigger the download
        window.location.href = downloadUrl;

        // 3. Set a timeout to re-enable the button
        setTimeout(() => {
            downloadButton.disabled = false;
            downloadButton.innerHTML = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg><span>Download Now</span>`;
        }, 15000); // Re-enable after 15 seconds
    });
});