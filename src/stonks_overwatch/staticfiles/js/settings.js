/**
 * Settings Modal Management
 * Handles broker settings form, TOTP verification, and modal interactions
 */

/**
 * TOTP Verification Manager
 * Manages TOTP code generation and progress bar updates
 */
class TOTPVerificationManager {
    constructor(settingsUrl, csrfToken) {
        this.settingsUrl = settingsUrl;
        this.csrfToken = csrfToken;
        this.timers = {};
    }

    /**
     * Start TOTP verification for a broker
     * @param {string} brokerName - Name of the broker (e.g., 'degiro')
     * @param {string} totpSecret - TOTP secret key
     */
    start(brokerName, totpSecret) {
        const elements = this._getElements(brokerName);
        if (!elements || !totpSecret) {
            this._hideContainer(brokerName);
            return;
        }

        this.stop(brokerName);
        elements.container.style.display = 'block';

        // Calculate time until next 30-second boundary
        const now = new Date();
        const seconds = now.getSeconds();
        const millisecondsIntoInterval = (seconds % 30) * 1000 + now.getMilliseconds();
        const millisecondsUntilNext = 30000 - millisecondsIntoInterval;

        // Fetch immediately
        this._fetchTotpCode(brokerName, totpSecret, elements);

        // Update progress bar immediately and every second
        this._updateProgressBar(elements.timerBar);
        const progressTimer = setInterval(() => this._updateProgressBar(elements.timerBar), 1000);

        // Schedule first fetch at next 30-second boundary, then every 30 seconds
        const initialTimeout = setTimeout(() => {
            this._fetchTotpCode(brokerName, totpSecret, elements);
            // Now set up regular 30-second interval
            const codeTimer = setInterval(() => this._fetchTotpCode(brokerName, totpSecret, elements), 30000);
            this.timers[brokerName].codeTimer = codeTimer;
        }, millisecondsUntilNext);

        // Store both timers and the initial timeout
        this.timers[brokerName] = {
            codeTimer: null,  // Will be set after initial timeout
            progressTimer: progressTimer,
            initialTimeout: initialTimeout
        };
    }

    /**
     * Stop TOTP verification for a broker
     * @param {string} brokerName - Name of the broker
     */
    stop(brokerName) {
        if (!this.timers[brokerName]) return;

        if (this.timers[brokerName].codeTimer) {
            clearInterval(this.timers[brokerName].codeTimer);
        }
        if (this.timers[brokerName].progressTimer) {
            clearInterval(this.timers[brokerName].progressTimer);
        }
        if (this.timers[brokerName].initialTimeout) {
            clearTimeout(this.timers[brokerName].initialTimeout);
        }
        delete this.timers[brokerName];
    }

    /**
     * Stop all TOTP verifications
     */
    stopAll() {
        Object.keys(this.timers).forEach(brokerName => this.stop(brokerName));
    }

    /**
     * Get DOM elements for TOTP display
     * @private
     */
    _getElements(brokerName) {
        const totpInput = document.getElementById(`${brokerName}-totp`);
        const container = document.getElementById(`${brokerName}-verification-container`);
        const codeDisplay = document.getElementById(`${brokerName}-verification-code`);
        const timerBar = document.getElementById(`${brokerName}-verification-timer`);

        if (!totpInput || !container || !codeDisplay || !timerBar) {
            return null;
        }

        return { totpInput, container, codeDisplay, timerBar };
    }

    /**
     * Fetch TOTP code from backend
     * @private
     */
    async _fetchTotpCode(brokerName, secret, elements) {
        try {
            const response = await fetch(this.settingsUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    action: 'generate_totp',
                    secret: secret
                })
            });

            const data = await response.json();
            if (data.code) {
                elements.codeDisplay.textContent = data.code;
            } else {
                this._showError(elements);
            }
        } catch (error) {
            console.error('Failed to fetch TOTP code:', error);
            this._showError(elements);
        }
    }

    /**
     * Update progress bar to show TOTP validity
     * @private
     */
    _updateProgressBar(timerBar) {
        const now = new Date();
        const seconds = now.getSeconds();
        const progress = (seconds % 30) / 30 * 100;
        // Circumference of circle (2 * π * r) where r = 16
        const circumference = 2 * Math.PI * 16;
        // Calculate stroke-dashoffset: when progress is 100%, offset is 0; when 0%, offset is circumference
        const offset = circumference * (1 - progress / 100);
        timerBar.style.strokeDashoffset = offset;
    }

    /**
     * Show error state
     * @private
     */
    _showError(elements) {
        elements.codeDisplay.textContent = 'Invalid TOTP Key';
        const circumference = 2 * Math.PI * 16;
        elements.timerBar.style.strokeDashoffset = circumference;
    }

    /**
     * Hide verification container
     * @private
     */
    _hideContainer(brokerName) {
        const elements = this._getElements(brokerName);
        if (!elements) return;

        elements.container.style.display = 'none';
        elements.codeDisplay.textContent = '';
        const circumference = 2 * Math.PI * 16;
        elements.timerBar.style.strokeDashoffset = circumference;
    }
}

/**
 * Settings Manager
 * Handles broker selection, form initialization, and saving
 */
class SettingsManager {
    constructor(settingsUrl, csrfToken) {
        this.settingsUrl = settingsUrl;
        this.csrfToken = csrfToken;
        this.totpManager = new TOTPVerificationManager(settingsUrl, csrfToken);
    }

    /**
     * Select a broker and show its settings
     * @param {string} brokerName - Name of the broker to select
     */
    selectBroker(brokerName) {
        // Update sidebar active state
        document.querySelectorAll('.broker-item').forEach(item => {
            item.classList.remove('active');
        });
        const selectedItem = document.querySelector(`[data-broker="${brokerName}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }

        // Show/hide broker sections
        document.querySelectorAll('.broker-section').forEach(section => {
            section.classList.remove('active');
        });
        const brokerSection = document.getElementById(`broker-${brokerName}`);
        if (brokerSection) {
            brokerSection.classList.add('active');
        }

        // Initialize verification code if DEGIRO
        if (brokerName === 'degiro') {
            this.updateVerificationCode('degiro');
        }
    }

    /**
     * Update TOTP verification code for a broker
     * @param {string} brokerName - Name of the broker
     */
    updateVerificationCode(brokerName) {
        const totpInput = document.getElementById(`${brokerName}-totp`);
        if (!totpInput) return;

        const totpSecret = totpInput.value.trim();
        if (totpSecret) {
            this.totpManager.start(brokerName, totpSecret);
        } else {
            this.totpManager.stop(brokerName);
        }
    }

    /**
     * Initialize settings content after AJAX load
     */
    initialize() {
        // Always select the active broker or first broker to ensure proper display
        const activeBroker = document.querySelector('.broker-item.active');
        if (activeBroker) {
            const brokerName = activeBroker.getAttribute('data-broker');
            this.selectBroker(brokerName);
        } else {
            const firstBroker = document.querySelector('.broker-item');
            if (firstBroker) {
                const brokerName = firstBroker.getAttribute('data-broker');
                this.selectBroker(brokerName);
            }
        }

        // Bind event listeners
        this._bindEventListeners();

        // Initialize key management buttons for dynamically loaded content
        initializeKeyManagementButtons();
    }

    /**
     * Validate settings form before saving
     * @returns {Object|null} Validation result with isValid and errors
     * @private
     */
    _validateSettings(brokerName, credentials, updateFrequency) {
        const errors = [];

        // Validate broker-specific fields
        if (brokerName === 'degiro') {
            if (!credentials.username || !credentials.username.trim()) {
                errors.push('Username is required for DEGIRO');
            }
            if (!credentials.password || !credentials.password.trim()) {
                errors.push('Password is required for DEGIRO');
            }
        } else if (brokerName === 'bitvavo') {
            if (!credentials.apikey || !credentials.apikey.trim()) {
                errors.push('API Key is required for Bitvavo');
            }
            if (!credentials.apisecret || !credentials.apisecret.trim()) {
                errors.push('API Secret is required for Bitvavo');
            }
        } else if (brokerName === 'ibkr') {
            if (!credentials.access_token || !credentials.access_token.trim()) {
                errors.push('Access Token is required for IBKR');
            }
            if (!credentials.access_token_secret || !credentials.access_token_secret.trim()) {
                errors.push('Access Token Secret is required for IBKR');
            }
            if (!credentials.consumer_key || !credentials.consumer_key.trim()) {
                errors.push('Consumer Key is required for IBKR');
            }
            if (!credentials.dh_prime || !credentials.dh_prime.trim()) {
                errors.push('DH Prime is required for IBKR');
            }
            // Validate that at least one encryption key option is provided
            if ((!credentials.encryption_key || !credentials.encryption_key.trim()) &&
                (!credentials.encryption_key_fp || !credentials.encryption_key_fp.trim())) {
                errors.push('Encryption Key is required for IBKR (either direct content or file path)');
            }
            // Validate that at least one signature key option is provided
            if ((!credentials.signature_key || !credentials.signature_key.trim()) &&
                (!credentials.signature_key_fp || !credentials.signature_key_fp.trim())) {
                errors.push('Signature Key is required for IBKR (either direct content or file path)');
            }
        }

        // Validate update frequency
        if (isNaN(updateFrequency) || updateFrequency < 1 || updateFrequency > 60) {
            errors.push('Update frequency must be between 1 and 60 minutes');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Bind event listeners for TOTP inputs
     * @private
     */
    _bindEventListeners() {
        // DEGIRO TOTP input
        const degiroTotp = document.getElementById('degiro-totp');
        if (degiroTotp) {
            degiroTotp.addEventListener('input', () => {
                this.updateVerificationCode('degiro');
            });
        }
    }

    /**
     * Clean up resources
     */
    cleanup() {
        this.totpManager.stopAll();
    }
}

// Export for global use
window.SettingsManager = SettingsManager;

/**
 * IBKR Key Management Functions
 * Global functions for handling PEM key file uploads, visibility toggling, and validation
 */

/**
 * Load PEM key from file and populate textarea
 * @param {HTMLInputElement} fileInput - The file input element
 * @param {string} textareaId - ID of the textarea to populate
 */
function loadKeyFromFile(fileInput, textareaId) {
    const file = fileInput.files[0];
    if (!file) {
        return;
    }

    // Validate file extension
    const validExtensions = ['.pem', '.key', '.crt'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
        alert('Invalid file type. Please select a PEM, KEY, or CRT file.');
        fileInput.value = '';
        return;
    }

    // Read file content
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const textarea = document.getElementById(textareaId);

        if (textarea) {
            textarea.value = content;
            validateKey(textareaId);

            // Show the container if it's hidden
            const containerId = textareaId + '-container';
            const container = document.getElementById(containerId);
            const toggleId = textareaId + '-toggle';

            if (container && container.classList.contains('d-none')) {
                toggleKeyVisibility(containerId, toggleId);
            }
        }
    };

    reader.onerror = function() {
        alert('Error reading file. Please try again.');
    };

    reader.readAsText(file);
    fileInput.value = ''; // Clear input to allow re-uploading same file
}

/**
 * Clear key textarea content
 * @param {string} textareaId - ID of the textarea to clear
 */
function clearKey(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) {
        return;
    }

    if (textarea.value && !confirm('Are you sure you want to clear the key? This action cannot be undone.')) {
        return;
    }

    textarea.value = '';
    validateKey(textareaId);

    // Hide the container and reset the toggle button after clearing
    const container = document.getElementById(textareaId + '-container');
    const toggleBtn = document.getElementById(textareaId + '-toggle');

    if (container) {
        container.classList.add('d-none');
        container.style.display = 'none';
    }

    if (toggleBtn) {
        toggleBtn.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i> Show';
        toggleBtn.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Validate PEM key format and update status badge
 * @param {string} textareaId - ID of the textarea to validate
 */
function validateKey(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) {
        return;
    }

    const content = textarea.value.trim();
    const statusBadge = document.getElementById(textareaId + '-status');

    if (statusBadge) {
        statusBadge.classList.remove('status-badge-loaded', 'status-badge-warning', 'status-badge-not-set');

        if (content) {
            // Basic PEM format validation
            const isPemFormat = content.includes('-----BEGIN') && content.includes('-----END');
            if (isPemFormat) {
                statusBadge.classList.add('status-badge-loaded');
                statusBadge.innerHTML = '<i class="bi bi-check-circle" aria-hidden="true"></i> Loaded';
            } else {
                statusBadge.classList.add('status-badge-warning');
                statusBadge.innerHTML = '<i class="bi bi-exclamation-triangle" aria-hidden="true"></i> Invalid Format';
            }
        } else {
            statusBadge.classList.add('status-badge-not-set');
            statusBadge.innerHTML = '<i class="bi bi-dash-circle" aria-hidden="true"></i> Not Set';
        }
    }
}

// Make functions globally available
window.loadKeyFromFile = loadKeyFromFile;
window.clearKey = clearKey;
window.validateKey = validateKey;

/**
 * Initialize key management button event listeners
 * Replaces inline onclick handlers for CSP compliance
 * Uses data-initialized flag to prevent duplicate listeners
 */
function initializeKeyManagementButtons() {
    // Load key from file buttons
    document.querySelectorAll('[data-action="load-key-file"]').forEach(btn => {
        if (btn.dataset.initialized === 'true') return;
        btn.dataset.initialized = 'true';

        btn.addEventListener('click', function(e) {
            const fileInput = document.getElementById(e.currentTarget.dataset.target);
            if (fileInput) {
                fileInput.click();
            }
        });
    });

    // File input change handlers
    document.querySelectorAll('input[type="file"][data-textarea-target]').forEach(fileInput => {
        if (fileInput.dataset.initialized === 'true') return;
        fileInput.dataset.initialized = 'true';

        fileInput.addEventListener('change', function() {
            const textareaId = this.dataset.textareaTarget;
            if (textareaId) {
                loadKeyFromFile(this, textareaId);
            }
        });
    });

    // Toggle key visibility buttons
    document.querySelectorAll('[data-action="toggle-key"]').forEach(btn => {
        if (btn.dataset.initialized === 'true') return;
        btn.dataset.initialized = 'true';

        btn.addEventListener('click', function(e) {
            const button = e.currentTarget;
            const container = document.getElementById(button.dataset.container);

            if (!container) return;

            const isHidden = container.classList.contains('d-none');

            if (isHidden) {
                container.classList.remove('d-none');
                container.style.display = '';
                button.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                button.setAttribute('aria-expanded', 'true');
            } else {
                container.classList.add('d-none');
                container.style.display = 'none';
                button.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i> Show';
                button.setAttribute('aria-expanded', 'false');
            }
        });
    });

    // Clear key buttons
    document.querySelectorAll('[data-action="clear-key"]').forEach(btn => {
        if (btn.dataset.initialized === 'true') return;
        btn.dataset.initialized = 'true';

        btn.addEventListener('click', function(e) {
            clearKey(e.currentTarget.dataset.target);
        });
    });

    // Key textarea input handlers
    document.querySelectorAll('.key-textarea').forEach(textarea => {
        if (textarea.dataset.initialized === 'true') return;
        textarea.dataset.initialized = 'true';

        textarea.addEventListener('input', function() {
            validateKey(this.id);
        });
    });

    // TOTP input handlers
    document.querySelectorAll('.totp-input').forEach(input => {
        if (input.dataset.initialized === 'true') return;
        input.dataset.initialized = 'true';

        input.addEventListener('input', function() {
            const brokerName = this.dataset.broker;
            if (brokerName) {
                updateVerificationCode(brokerName);
            }
        });
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeKeyManagementButtons);
} else {
    initializeKeyManagementButtons();
}

// Export for potential re-initialization
window.initializeKeyManagementButtons = initializeKeyManagementButtons;

/**
 * Initialize Bootstrap tooltips
 * Must be called after DOM is ready to enable tooltips on elements with data-bs-toggle="tooltip"
 */
function initializeTooltips() {
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.warn('Bootstrap is not loaded. Tooltips will not be initialized.');
        return;
    }

    const sidebar = document.getElementById('sidebar');
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true'
        || (sidebar && sidebar.classList.contains('sidebar-collapsed'));

    // Initialize all tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => {
        const existing = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
        const tooltip = existing || new bootstrap.Tooltip(tooltipTriggerEl);

        // Sidebar nav tooltips should only show when sidebar is collapsed
        if (tooltipTriggerEl.classList.contains('sidebar-nav-link') && !sidebarCollapsed) {
            tooltip.disable();
        }

        return tooltip;
    });

    console.log(`Initialized ${tooltipList.length} tooltips`);
}

// Initialize tooltips when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTooltips);
} else {
    initializeTooltips();
}

// Export for potential re-initialization
window.initializeTooltips = initializeTooltips;
