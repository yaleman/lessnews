// On page load, bind click handler to preview button
document.addEventListener('DOMContentLoaded', () => {
    const previewButton = document.getElementById('preview-button');
    const urlInput = document.querySelector('input[name="url"]');

    if (previewButton && urlInput) {
        previewButton.onclick = () => {
            const url = urlInput.value;
            if (url.trim() !== "") {
                window.location.href = `/preview?url=${encodeURIComponent(url)}`;
            }
        };
    }
});
