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

    // --- Dark Mode, Fetch, UI update, and GSAP helper functions are all correct and unchanged ---
    const applyTheme = (theme) => { /* ... */ };
    const toggleTheme = () => { /* ... */ };
    const initializeTheme = () => { /* ... */ };
    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) { showError("Please paste a URL first."); return; }
        resetDownloadButton();
        showSkeleton();
        fetchButton.disabled = true;
        const originalFetchText = fetchButton.innerHTML;
        fetchButton.innerHTML = `<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Fetching...</span>`;
        try {
            const response = await fetch('/api/fetch_info', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }), });
            if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.error || 'Could not fetch video information.'); }
            const data = await response.json();
            currentVideoData = data;
            displayResult(data);
        } catch (error) { showError(error.message); }
        finally { fetchButton.disabled = false; fetchButton.innerHTML = originalFetchText; }
    });
    const showSkeleton = () => { resultDiv.classList.add('hidden'); errorDiv.classList.add('hidden'); skeleton.classList.remove('hidden'); };
    const showError = (message) => { skeleton.classList.add('hidden'); resultDiv.classList.add('hidden'); errorMessage.textContent = message; errorDiv.classList.remove('hidden'); };
    const displayResult = (data) => {
        skeleton.classList.add('hidden');
        errorDiv.classList.add('hidden');
        document.getElementById('thumbnail').src = data.thumbnail;
        document.getElementById('title').textContent = data.title;
        const metaInfo = [];
        if (data.uploader) metaInfo.push(`By ${data.uploader}`);
        if (data.duration) metaInfo.push(data.duration);
        document.getElementById('meta').textContent = metaInfo.join(' · ');
        const formatSelector = document.getElementById('formatSelector');
        formatSelector.innerHTML = '';
        data.formats.forEach((format, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${format.label} (~${format.filesize})`;
            formatSelector.appendChild(option);
        });
        resultDiv.classList.remove('hidden');
    };
    function getPoint(point, i, a, smoothing) { /* ... */ }
    function getPath(update, smoothing, pointsNew) { /* ... */ }

    // --- GSAP Animation Logic for Download Button ---
    const button = downloadButton;
    const buttonText = button.querySelector('.gsap-button__text');
    const buttonIcon = button.querySelector('.gsap-button__icon');
    let duration = 3000, svg = button.querySelector('svg'), svgPath = new Proxy({ y: null, smoothing: null }, { set(target, key, value) { target[key] = value; if(target.y !== null && target.smoothing !== null) { svg.innerHTML = getPath(target.y, target.smoothing, null); } return true; }, get(target, key) { return target[key]; } });
    const resetDownloadButton = () => { button.classList.remove('loading', 'success'); button.disabled = false; buttonText.textContent = "Download Now"; buttonIcon.style.display = 'inline-flex'; svg.innerHTML = `<path d="M5,20h14a1,1,0,0,0,0-2H5a1,1,0,0,0,0,2Zm7-3a1,1,0,0,0,.71-.29l5-5a1,1,0,0,0-1.42-1.42L13,13.59V4a1,1,0,0,0-2,0V13.59L7.71,10.29a1,1,0,1,0-1.42,1.42l5,5A1,1,0,0,0,12,17Z"/>`; };
    resetDownloadButton();

    // <<< THIS IS THE ONLY MODIFIED PART >>>
    button.addEventListener('click', e => {
        e.preventDefault();
        if(button.classList.contains('loading') || button.classList.contains('success')) return;

        const selectedIndex = document.getElementById('formatSelector').value;
        if (selectedIndex === null || !currentVideoData) { showError("Please select a format to download."); return; }
        const selectedFormat = currentVideoData.formats[selectedIndex];
        
        // --- THE NEW HYBRID LOGIC ---
        let downloadUrl;
        if (selectedFormat.direct_url) {
            // This is a YouTube video from the external API, use the direct link
            console.log("Using direct download URL from API:", selectedFormat.direct_url);
            downloadUrl = selectedFormat.direct_url;
        } else {
            // This is another platform (TikTok, FB), use our own server's download endpoint
            console.log("Using internal /api/download endpoint");
            downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoData.original_url)}&format_id=${encodeURIComponent(selectedFormat.format_id)}&filename=${encodeURIComponent(selectedFormat.filename)}&ext=${encodeURIComponent(selectedFormat.ext)}`;
        }

        // The animation logic from your file remains the same
        button.classList.add('loading');
        gsap.to(svgPath, { smoothing: .3, duration: duration * .065 / 1000 });
        gsap.to(svgPath, { y: 12, duration: duration * .265 / 1000, delay: duration * .065 / 1000, ease: Elastic.easeOut.config(1.12, .4) });
        window.location.href = downloadUrl;
        setTimeout(() => {
            button.classList.remove('loading');
            button.classList.add('success');
            buttonText.textContent = "Success!";
            buttonIcon.style.display = 'none';
        }, duration / 2);
    });
});