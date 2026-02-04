(function () {
    /**
     * Prevents context menu on release notes content
     *
     * Note: This is scoped only to .release-notes-content to avoid impacting
     * the rest of the application. Users can still use browser keyboard shortcuts
     * and other navigation methods.
     */
    function initializeContextMenuProtection() {
        const releaseNotesContent = document.querySelector(".release-notes-content");

        if (!releaseNotesContent) {
            // No release notes on this page, skip initialization
            return;
        }

        releaseNotesContent.addEventListener("contextmenu", (event) => {
            event.preventDefault();
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeContextMenuProtection);
    } else {
        initializeContextMenuProtection();
    }
})();
