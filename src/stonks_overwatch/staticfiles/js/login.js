(function () {
    /**
     * Navigate to the broker login page
     * @param {string} url - The broker login URL
     */
    function selectBroker(url) {
        if (!url) {
            console.error("Broker URL is missing");
            return;
        }
        window.location.href = url;
    }

    /**
     * Initialize broker card event listeners
     * Handles both click and keyboard navigation
     */
    function initialize() {
        // Attach event listeners to all broker cards
        document.querySelectorAll(".broker-card[data-url]").forEach((card) => {
            const brokerUrl = card.dataset.url;

            card.addEventListener("click", () => selectBroker(brokerUrl));
            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    selectBroker(brokerUrl);
                }
            });
        });
    }

    // Standard initialization pattern - handles both early and late script loading
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
