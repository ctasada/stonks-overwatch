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
        timerBar.style.width = progress + '%';
    }

    /**
     * Show error state
     * @private
     */
    _showError(elements) {
        elements.codeDisplay.textContent = 'Invalid TOTP Key';
        elements.timerBar.style.width = '0%';
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
        elements.timerBar.style.width = '0%';
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
            section.style.display = 'none';
        });
        const brokerSection = document.getElementById(`broker-${brokerName}`);
        if (brokerSection) {
            brokerSection.style.display = 'block';
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
        // Select first broker by default if none selected
        const activeBroker = document.querySelector('.broker-item.active');
        if (!activeBroker) {
            const firstBroker = document.querySelector('.broker-item');
            if (firstBroker) {
                const brokerName = firstBroker.getAttribute('data-broker');
                this.selectBroker(brokerName);
            }
        } else {
            // Re-initialize verification code if DEGIRO is already selected
            const brokerName = activeBroker.getAttribute('data-broker');
            if (brokerName === 'degiro') {
                const degiroTotp = document.getElementById('degiro-totp');
                if (degiroTotp && degiroTotp.value) {
                    this.updateVerificationCode('degiro');
                }
            }
        }

        // Bind event listeners
        this._bindEventListeners();
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
