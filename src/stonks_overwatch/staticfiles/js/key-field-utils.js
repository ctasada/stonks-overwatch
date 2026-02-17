/**
 * Shared utilities for key field management
 * Provides reusable functions for showing/hiding key fields across login and settings pages
 */
const KeyFieldUtils = {
    /**
     * Show a key field container if it has prefilled content
     * @param {string} fieldId - ID of the textarea element
     * @returns {boolean} True if field was shown, false otherwise
     */
    showPrefilledKey(fieldId) {
        const textarea = document.getElementById(fieldId);
        if (!textarea || !textarea.value.trim()) {
            return false;
        }

        const container = document.getElementById(`${fieldId}-container`);
        const toggleBtn = document.getElementById(`${fieldId}-toggle`);

        if (!container) {
            console.warn(`Container not found for field: ${fieldId}`);
            return false;
        }

        // Only show if currently hidden
        if (container.classList.contains('d-none')) {
            container.classList.remove('d-none');

            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                toggleBtn.setAttribute('aria-expanded', 'true');
            }
        }

        return true;
    },

    /**
     * Show all prefilled IBKR keys (encryption and signature)
     * Checks if IBKR section exists before attempting to show keys
     */
    showPrefilledIbkrKeys() {
        // Check if IBKR section exists first (might not be configured)
        const ibkrSection = document.getElementById('broker-ibkr');
        if (!ibkrSection) {
            return; // IBKR not configured, skip silently
        }

        this.showPrefilledKey('ibkr-encryption-key');
        this.showPrefilledKey('ibkr-signature-key');
    }
};

// Export to window for use in other files
window.KeyFieldUtils = KeyFieldUtils;
