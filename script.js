const DOWNLOAD_URL =
    "https://github.com/Along-the-skies/VARVIS/releases/download/Setup.exe/Varvis_Setup.exe";

const downloadButton =
    document.getElementById("downloadButton");


downloadButton.addEventListener("click", () => {

    // Change button state
    downloadButton.innerHTML = `
        <span class="download-icon">✓</span>
        <span>Starting Download...</span>
    `;

    downloadButton.style.pointerEvents = "none";


    // Start download
    window.location.href = DOWNLOAD_URL;


    // Restore button after a short delay
    setTimeout(() => {

        downloadButton.innerHTML = `
            <span class="download-icon">↓</span>
            <span>Download VARVIS</span>
        `;

        downloadButton.style.pointerEvents = "auto";

    }, 3000);

});
const sourceToggle =
    document.getElementById("sourceToggle");

const sourceContent =
    document.getElementById("sourceContent");

const sourceArrow =
    document.getElementById("sourceArrow");


sourceToggle.addEventListener("click", () => {

    sourceContent.classList.toggle("show");

    if (sourceContent.classList.contains("show")) {

        sourceArrow.textContent = "↑";

    } else {

        sourceArrow.textContent = "↓";

    }

});