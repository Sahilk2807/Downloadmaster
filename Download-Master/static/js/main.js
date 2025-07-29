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

        resetDownloadButton();
        showSkeleton();
        fetchButton.disabled = true;
        const originalFetchText = fetchButton.innerHTML;
        fetchButton.innerHTML = `<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Fetching...</span>`;

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
            showError(error.message);
        } finally {
            fetchButton.disabled = false;
            fetchButton.innerHTML = originalFetchText;
        }
    });

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
        
        data.formats.forEach((format, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${format.label} (~${format.filesize})`;
            formatSelector.appendChild(option);
        });

        resultDiv.classList.remove('hidden');
    };

    // --- GSAP Animation Logic for Download Button ---
    function getPoint(point, i, a, smoothing) {
        let cp = (current, previous, next, reverse) => {
            let p = previous || current, n = next || current,
                o = { length: Math.sqrt(Math.pow(n[0] - p[0], 2) + Math.pow(n[1] - p[1], 2)), angle: Math.atan2(n[1] - p[1], n[0] - p[0]) },
                angle = o.angle + (reverse ? Math.PI : 0),
                length = o.length * smoothing;
            return [current[0] + Math.cos(angle) * length, current[1] + Math.sin(angle) * length];
        };
        let cps = cp(a[i - 1], a[i - 2], point, false);
        let cpe = cp(point, a[i - 1], a[i + 1], true);
        return `C ${cps[0]},${cps[1]} ${cpe[0]},${cpe[1]} ${point[0]},${point[1]}`;
    }

    function getPath(update, smoothing, pointsNew) {
        let points = pointsNew ? pointsNew : [[4, 12], [12, update], [20, 12]];
        let d = points.reduce((acc, point, i, a) => i === 0 ? `M ${point[0]},${point[1]}` : `${acc} ${getPoint(point, i, a, smoothing)}`, '');
        return `<path d="${d}" />`;
    }

    const button = downloadButton;
    const buttonText = button.querySelector('.gsap-button__text');
    const buttonIcon = button.querySelector('.gsap-button__icon');
    let duration = 3000,
        svg = button.querySelector('svg'),
        svgPath = new Proxy({ y: null, smoothing: null }, {
            set(target, key, value) {
                target[key] = value;
                if(target.y !== null && target.smoothing !== null) { svg.innerHTML = getPath(target.y, target.smoothing, null); }
                return true;
            },
            get(target, key) { return target[key]; }
        });
    
    const resetDownloadButton = () => {
        button.classList.remove('loading', 'success');
        button.disabled = false;
        buttonText.textContent = "Download Now";
        buttonIcon.style.display = 'inline-flex'; // Show the icon
        svg.innerHTML = `<path d="M5,20h14a1,1,0,0,0,0-2H5a1,1,0,0,0,0,2Zm7-3a1,1,0,0,0,.71-.29l5-5a1,1,0,0,0-1.42-1.42L13,13.59V4a1,1,0,0,0-2,0V13.59L7.71,10.29a1,1,0,1,0-1.42,1.42l5,5A1,1,0,0,0,12,17Z"/>`;
    };

    // Initialize the button state
    resetDownloadButton();

    button.addEventListener('click', e => {
        e.preventDefault();

        if(button.classList.contains('loading') || button.classList.contains('success')) return;

        const selectedIndex = document.getElementById('formatSelector').value;
        if (selectedIndex === null || !currentVideoData) {
            showError("Please select a format to download.");
            return;
        }
        const selectedFormat = currentVideoData.formats[selectedIndex];
        const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoData.original_url)}&format_id=${encodeURIComponent(selectedFormat.format_id)}&filename=${encodeURIComponent(selectedFormat.filename)}&ext=${encodeURIComponent(selectedFormat.ext)}`;

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