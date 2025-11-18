// On page load, bind click handlers to preview and wayback buttons
document.addEventListener('DOMContentLoaded', () => {
    const previewButton = document.getElementById('preview-button');
    const waybackButton = document.getElementById('wayback-button');
    const urlInput = document.querySelector('input[name="url"]');

    if (previewButton && urlInput) {
        previewButton.onclick = () => {
            const url = urlInput.value;
            if (url.trim() !== "") {
                window.location.href = `/preview?url=${encodeURIComponent(url)}`;
            }
        };
    }

    if (waybackButton && urlInput) {
        waybackButton.onclick = () => {
            const url = urlInput.value;
            if (url.trim() !== "") {
                window.location.href = `https://web.archive.org/web/*/${encodeURIComponent(url)}`;
            }
        };
    }
});
