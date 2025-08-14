document.addEventListener('DOMContentLoaded', () => {
    // --- All Element Selections ---
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('urlInput');
    const fetchButton = document.getElementById('fetchButton');
    const downloadButton = document.getElementById('downloadButton');
    // ... all other selections are the same
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
    urlForm.addEventListener('submit', async (e) => { /* ... */ });
    const showSkeleton = () => { /* ... */ };
    const showError = (message) => { /* ... */ };
    const displayResult = (data) => {
        skeleton.classList.add('hidden');
        errorDiv.classList.add('hidden');
        document.getElementById('thumbnail').src = data.thumbnail;
        document.getElementById('title').textContent = data.title;
        // Check for uploader/duration which might not come from the API
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
    let duration = 3000,
        svg = button.querySelector('svg'),
        svgPath = new Proxy({ y: null, smoothing: null }, { /* ... */ });
    
    const resetDownloadButton = () => {
        button.classList.remove('loading', 'success');
        button.disabled = false;
        buttonText.textContent = "Download Now";
        buttonIcon.style.display = 'inline-flex';
        svg.innerHTML = `<path d="M5,20h14a1,1,0,0,0,0-2H5a1,1,0,0,0,0,2Zm7-3a1,1,0,0,0,.71-.29l5-5a1,1,0,0,0-1.42-1.42L13,13.59V4a1,1,0,0,0-2,0V13.59L7.71,10.29a1,1,0,1,0-1.42,1.42l5,5A1,1,0,0,0,12,17Z"/>`;
    };
    resetDownloadButton();


    // <<< THIS IS THE ONLY MODIFIED PART >>>
    button.addEventListener('click', e => {
        e.preventDefault();

        if(button.classList.contains('loading') || button.classList.contains('success')) return;

        const selectedIndex = document.getElementById('formatSelector').value;
        if (selectedIndex === null || !currentVideoData) {
            showError("Please select a format to download.");
            return;
        }
        const selectedFormat = currentVideoData.formats[selectedIndex];
        
        // --- THE NEW LOGIC ---
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
            buttonIcon.style.display = 'none'; // Hide the icon on success
        }, duration / 2);
    });
});