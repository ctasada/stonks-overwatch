/**
 * Modal Utilities
 * Reusable utilities for Bootstrap modals
 */

/**
 * Modal Script Executor
 * Executes scripts from AJAX-loaded content
 */
class ModalScriptExecutor {
    /**
     * Load and inject HTML content with script execution
     * @param {HTMLElement} container - Container element to inject content into
     * @param {string} html - HTML content to inject
     * @param {Function} onSuccess - Callback after successful injection and script execution
     */
    static injectWithScripts(container, html, onSuccess = null) {
        try {
            // Extract scripts using DOMParser
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const scripts = doc.querySelectorAll('script');

            // Set HTML content without scripts
            const htmlWithoutScripts = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            container.innerHTML = htmlWithoutScripts;

            // Execute scripts after DOM is updated
            scripts.forEach(oldScript => {
                const newScript = document.createElement('script');

                // Copy attributes
                Array.from(oldScript.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });

                // Copy content
                newScript.textContent = oldScript.textContent;

                // Append and immediately remove to execute
                document.body.appendChild(newScript);
                document.body.removeChild(newScript);
            });

            // Call success callback
            if (onSuccess && typeof onSuccess === 'function') {
                onSuccess();
            }
        } catch (error) {
            console.error('Failed to inject content with scripts:', error);
            throw error;
        }
    }

    /**
     * Load content via AJAX and inject into modal
     * @param {string} url - URL to fetch content from
     * @param {HTMLElement} container - Container to inject content into
     * @param {Object} options - Options object
     * @param {Function} options.onSuccess - Callback after successful load
     * @param {Function} options.onError - Callback on error
     * @param {string} options.loadingHTML - HTML to show while loading
     * @param {string} options.errorHTML - HTML to show on error
     */
    static async loadModalContent(url, container, options = {}) {
        const {
            onSuccess = null,
            onError = null,
            loadingHTML = '<div class="text-center py-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>',
            errorHTML = '<div class="alert alert-danger">Failed to load content. Please try again later.</div>'
        } = options;

        // Show loading indicator
        container.innerHTML = loadingHTML;

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'text/html',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const html = await response.text();
            this.injectWithScripts(container, html, onSuccess);
        } catch (error) {
            console.error('Error loading modal content:', error);
            container.innerHTML = errorHTML;
            if (onError && typeof onError === 'function') {
                onError(error);
            }
        }
    }
}

/**
 * Bootstrap Alert Helper
 * Creates and manages Bootstrap alerts
 */
class BootstrapAlertHelper {
    /**
     * Show a Bootstrap alert
     * @param {string} message - Alert message
     * @param {string} type - Alert type (success, danger, warning, info)
     * @param {Object} options - Options object
     * @param {HTMLElement} options.container - Container to append alert to
     * @param {number} options.autoDismiss - Auto-dismiss time in milliseconds (0 = no auto-dismiss)
     * @param {boolean} options.dismissible - Whether alert is dismissible
     */
    static show(message, type = 'info', options = {}) {
        const {
            container = null,
            autoDismiss = null,
            dismissible = true
        } = options;

        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}${dismissible ? ' alert-dismissible' : ''} fade show`;
        alertDiv.innerHTML = `${message}${dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}`;

        // Find container
        const targetContainer = container || this._findDefaultContainer();

        if (targetContainer) {
            targetContainer.insertBefore(alertDiv, targetContainer.firstChild);

            // Auto-dismiss
            const dismissTime = autoDismiss || (type === 'danger' || type === 'warning' ? 7000 : 5000);
            if (dismissTime > 0) {
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, dismissTime);
            }
        }

        return alertDiv;
    }

    /**
     * Find default container for alerts
     * @private
     */
    static _findDefaultContainer() {
        return document.querySelector('.settings-content') ||
               document.querySelector('.modal-body') ||
               document.querySelector('.container-fluid') ||
               document.body;
    }

    /**
     * Show success alert
     */
    static success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    /**
     * Show error alert
     */
    static error(message, options = {}) {
        return this.show(message, 'danger', options);
    }

    /**
     * Show warning alert
     */
    static warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    /**
     * Show info alert
     */
    static info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Export for global use
window.ModalScriptExecutor = ModalScriptExecutor;
window.BootstrapAlertHelper = BootstrapAlertHelper;
