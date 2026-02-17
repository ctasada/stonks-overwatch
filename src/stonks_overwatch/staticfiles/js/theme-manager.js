/**
 * ThemeManager - Manages theme switching and system preference detection.
 * Implements singleton pattern to ensure only one instance exists.
 */
class ThemeManager {
    constructor() {
        // Enforce singleton pattern
        if (ThemeManager.instance) {
            return ThemeManager.instance;
        }

        this.htmlElement = document.documentElement;
        this.appearance = this.htmlElement.dataset.appearance
            || this.htmlElement.getAttribute("data-bs-theme")
            || "auto";

        ThemeManager.instance = this;
        this.init();
    }

    init() {
        this.apply(this.appearance);
    }

    apply(newAppearance) {
        if (newAppearance) {
            this.appearance = newAppearance;
        }

        const update = () => {
            if (this.appearance === "auto") {
                const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
                this.htmlElement.setAttribute("data-bs-theme", prefersDark ? "dark" : "light");
            } else {
                this.htmlElement.setAttribute("data-bs-theme", this.appearance);
            }

            // Use CSS variable for chart text color to maintain consistency with design system
            const computedStyle = getComputedStyle(this.htmlElement);
            window.CHART_TEXT_COLOR = computedStyle.getPropertyValue('--text-on-surface').trim();
        };

        if (this._listener) {
            window.matchMedia("(prefers-color-scheme: dark)").removeEventListener("change", this._listener);
            this._listener = null;
        }

        update();

        if (this.appearance === "auto") {
            this._listener = update;
            window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", this._listener);
        }
    }
}

// Initialize immediately and expose to window for external access
window.ThemeManager = new ThemeManager();
