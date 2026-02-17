(function () {
    /**
     * Validates and loads a cryptographic key file into a textarea
     * @param {HTMLInputElement} fileInput - The file input element
     * @param {string} textareaId - ID of the target textarea
     */
    function loadKeyFromFile(fileInput, textareaId) {
        const file = fileInput.files[0];
        if (!file) {
            return;
        }

        // Validate file extension
        const validExtensions = [".pem", ".key", ".crt"];
        const fileName = file.name.toLowerCase();
        const hasValidExtension = validExtensions.some((ext) => fileName.endsWith(ext));

        if (!hasValidExtension) {
            showError("Invalid file type. Please select a PEM, KEY, or CRT file.");
            fileInput.value = "";
            return;
        }

        // Validate file size (100KB max to prevent memory issues)
        const MAX_FILE_SIZE = 100 * 1024; // 100KB in bytes
        if (file.size > MAX_FILE_SIZE) {
            showError(
                `File is too large (${formatFileSize(file.size)}). Maximum allowed size is ${formatFileSize(
                    MAX_FILE_SIZE
                )}.`
            );
            fileInput.value = "";
            return;
        }

        // Check if file might be binary (rough heuristic)
        if (file.type && !file.type.startsWith("text/") && file.type !== "application/x-pem-file") {
            showError(
                "File appears to be binary. Please select a text-based PEM key file."
            );
            fileInput.value = "";
            return;
        }

        const reader = new FileReader();

        reader.onload = function (event) {
            const content = event.target.result;

            // Validate PEM format
            if (!isPemFormat(content)) {
                showError(
                    'Invalid PEM format. File must contain "-----BEGIN" and "-----END" markers.'
                );
                fileInput.value = "";
                return;
            }

            // Additional check for empty or whitespace-only content
            if (!content.trim()) {
                showError("File is empty or contains only whitespace.");
                fileInput.value = "";
                return;
            }

            const textarea = document.getElementById(textareaId);
            if (textarea) {
                textarea.value = content;

                const container = document.getElementById(`${textareaId}-container`);
                const toggleBtn = document.getElementById(`${textareaId}-toggle`);

                if (container && container.classList.contains("d-none")) {
                    container.classList.remove("d-none");
                    if (toggleBtn) {
                        toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                        toggleBtn.setAttribute("aria-expanded", "true");
                    }
                }
            }
        };

        reader.onerror = function () {
            showError("Error reading file. The file may be corrupted or inaccessible.");
            fileInput.value = "";
        };

        reader.readAsText(file);
    }

    /**
     * Validates if content is in PEM format
     * @param {string} content - File content to validate
     * @returns {boolean} True if valid PEM format
     */
    function isPemFormat(content) {
        if (!content || typeof content !== "string") {
            return false;
        }

        const trimmedContent = content.trim();
        const hasBeginMarker = trimmedContent.includes("-----BEGIN");
        const hasEndMarker = trimmedContent.includes("-----END");

        return hasBeginMarker && hasEndMarker;
    }

    /**
     * Formats file size in human-readable format
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + " bytes";
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(1) + " KB";
        } else {
            return (bytes / (1024 * 1024)).toFixed(1) + " MB";
        }
    }

    /**
     * Displays an error message to the user with proper accessibility
     * @param {string} message - Error message to display
     */
    function showError(message) {
        // Use Bootstrap alert if available, otherwise fall back to alert()
        const messagesContainer = document.querySelector(".messages");
        if (messagesContainer) {
            const alertDiv = document.createElement("div");
            alertDiv.className = "alert alert-danger alert-dismissible fade show";
            alertDiv.setAttribute("role", "alert");
            // aria-live ensures screen readers announce the error
            // polite waits for current speech to finish before announcing
            alertDiv.setAttribute("aria-live", "polite");
            // aria-atomic ensures the entire message is read, not just changes
            alertDiv.setAttribute("aria-atomic", "true");

            // Create icon element
            const icon = document.createElement("i");
            icon.className = "bi bi-exclamation-triangle-fill me-2";
            icon.setAttribute("aria-hidden", "true");

            // Create message span with textContent for XSS safety
            const messageSpan = document.createElement("span");
            messageSpan.textContent = message;

            // Create close button
            const closeButton = document.createElement("button");
            closeButton.type = "button";
            closeButton.className = "btn-close";
            closeButton.setAttribute("data-bs-dismiss", "alert");
            closeButton.setAttribute("aria-label", "Close");

            // Assemble alert
            alertDiv.appendChild(icon);
            alertDiv.appendChild(messageSpan);
            alertDiv.appendChild(closeButton);
            messagesContainer.appendChild(alertDiv);

            // Auto-dismiss after 8 seconds (longer for accessibility)
            // Gives screen reader users enough time to hear the full message
            setTimeout(() => {
                // Fade out smoothly for better UX
                alertDiv.classList.remove("show");
                setTimeout(() => {
                    alertDiv.remove();
                }, 150); // Wait for fade animation
            }, 8000);
        } else {
            // Fallback to browser alert
            alert(message);
        }
    }

    function clearKey(textareaId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            return;
        }

        if (textarea.value && !confirm("Are you sure you want to clear the key? This action cannot be undone.")) {
            return;
        }

        textarea.value = "";

        const container = document.getElementById(`${textareaId}-container`);
        const toggleBtn = document.getElementById(`${textareaId}-toggle`);

        if (container) {
            container.classList.add("d-none");
        }

        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i> Show';
            toggleBtn.setAttribute("aria-expanded", "false");
        }
    }

    /**
     * Initialize all key management buttons (load, toggle, clear)
     * Called once on page load via the standard initialization pattern
     */
    function initializeKeyManagementButtons() {
        // Load key from file buttons
        document.querySelectorAll('[data-action="load-key-file"]').forEach((btn) => {
            btn.addEventListener("click", function (event) {
                const fileInput = document.getElementById(event.currentTarget.dataset.target);
                if (fileInput) {
                    fileInput.click();
                }
            });
        });

        // File input change handlers
        document.querySelectorAll('input[type="file"][data-textarea-target]').forEach((fileInput) => {
            fileInput.addEventListener("change", function () {
                const textareaId = this.dataset.textareaTarget;
                if (textareaId) {
                    loadKeyFromFile(this, textareaId);
                }
            });
        });

        // Toggle key visibility buttons
        document.querySelectorAll('[data-action="toggle-key"]').forEach((btn) => {
            btn.addEventListener("click", function (event) {
                const button = event.currentTarget;
                const container = document.getElementById(button.dataset.container);

                if (!container) {
                    return;
                }

                const isHidden = container.classList.contains("d-none");

                if (isHidden) {
                    container.classList.remove("d-none");
                    button.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                    button.setAttribute("aria-expanded", "true");
                } else {
                    container.classList.add("d-none");
                    button.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i> Show';
                    button.setAttribute("aria-expanded", "false");
                }
            });
        });

        // Clear key buttons
        document.querySelectorAll('[data-action="clear-key"]').forEach((btn) => {
            btn.addEventListener("click", function (event) {
                clearKey(event.currentTarget.dataset.target);
            });
        });
    }

    /**
     * Show prefilled IBKR keys using shared utility
     * Falls back to inline implementation if utility not loaded
     */
    function showPrefilledKeys() {
        if (window.KeyFieldUtils) {
            window.KeyFieldUtils.showPrefilledIbkrKeys();
        } else {
            // Fallback: inline implementation if utility not loaded
            console.warn('KeyFieldUtils not loaded, using fallback implementation');
            const encryptionKey = document.getElementById("ibkr-encryption-key");
            if (encryptionKey && encryptionKey.value.trim()) {
                const container = document.getElementById("ibkr-encryption-key-container");
                const toggleBtn = document.getElementById("ibkr-encryption-key-toggle");
                if (container && container.classList.contains("d-none")) {
                    container.classList.remove("d-none");
                    if (toggleBtn) {
                        toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                        toggleBtn.setAttribute("aria-expanded", "true");
                    }
                }
            }

            const signatureKey = document.getElementById("ibkr-signature-key");
            if (signatureKey && signatureKey.value.trim()) {
                const container = document.getElementById("ibkr-signature-key-container");
                const toggleBtn = document.getElementById("ibkr-signature-key-toggle");
                if (container && container.classList.contains("d-none")) {
                    container.classList.remove("d-none");
                    if (toggleBtn) {
                        toggleBtn.innerHTML = '<i class="bi bi-eye-slash" aria-hidden="true"></i> Hide';
                        toggleBtn.setAttribute("aria-expanded", "true");
                    }
                }
            }
        }
    }

    function initialize() {
        initializeKeyManagementButtons();
        showPrefilledKeys();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
