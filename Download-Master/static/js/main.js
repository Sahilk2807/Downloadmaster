document.addEventListener('DOMContentLoaded', () => {
    // ... All element selections are the same ...
    const downloadButton = document.getElementById('downloadButton');
    let currentVideoData = null;
    // ... All other functions are the same (Dark Mode, Fetch, UI, GSAP helpers) ...

    const button = downloadButton;
    // ... GSAP setup is the same ...
    const resetDownloadButton = () => { /* ... */ };
    resetDownloadButton();

    // <<< THIS IS THE SIMPLIFIED AND FINAL DOWNLOAD LOGIC >>>
    button.addEventListener('click', e => {
        e.preventDefault();
        if(button.classList.contains('loading') || button.classList.contains('success')) return;

        const selectedIndex = document.getElementById('formatSelector').value;
        if (selectedIndex === null || !currentVideoData) {
            showError("Please select a format to download.");
            return;
        }
        const selectedFormat = currentVideoData.formats[selectedIndex];
        
        // --- The logic is now simple: ALWAYS build a link to our own server ---
        console.log("Using internal /api/download endpoint for all platforms.");
        const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoData.original_url)}&format_id=${encodeURIComponent(selectedFormat.format_id)}&filename=${encodeURIComponent(selectedFormat.filename)}&ext=${encodeURIComponent(selectedFormat.ext)}`;

        // The animation logic remains the same
        button.classList.add('loading');
        gsap.to(svgPath, { smoothing: .3, duration: 3000 * .065 / 1000 });
        gsap.to(svgPath, { y: 12, duration: 3000 * .265 / 1000, delay: 3000 * .065 / 1000, ease: Elastic.easeOut.config(1.12, .4) });
        window.location.href = downloadUrl;
        setTimeout(() => {
            button.classList.remove('loading');
            button.classList.add('success');
            button.querySelector('.gsap-button__text').textContent = "Success!";
            button.querySelector('.gsap-button__icon').style.display = 'none';
        }, 3000 / 2);
    });
});