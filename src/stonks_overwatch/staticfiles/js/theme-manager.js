/**
 * ThemeManager - Manages theme switching and system preference detection
 *
 * Handles dark mode, light mode, and auto theme detection based on system preferences.
 * Automatically applies theme changes when system preferences change.
 */
class ThemeManager {
    constructor() {
        this.htmlElement = document.documentElement;
        this.currentTheme = this.htmlElement.getAttribute('data-bs-theme');
        this.init();
    }

    init() {
        // Handle auto theme by listening to system preference changes
        if (this.currentTheme === 'auto') {
            this.applyAutoTheme();
            // Listen for system theme changes
            if (window.matchMedia) {
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                    this.applyAutoTheme();
                });
            }
        }
    }

    applyAutoTheme() {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.htmlElement.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
    }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ThemeManager());
} else {
    new ThemeManager();
}
