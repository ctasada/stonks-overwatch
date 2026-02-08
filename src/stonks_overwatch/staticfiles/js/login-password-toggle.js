(function () {
    /**
     * Toggle password visibility for password input fields
     * @param {HTMLElement} toggleBtn - The toggle button element
     */
    function setupPasswordToggle(toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const targetId = this.dataset.target;
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) {
                console.warn(`Password input with id "${targetId}" not found`);
                return;
            }

            // Toggle input type
            const currentType = passwordInput.getAttribute("type");
            const newType = currentType === "password" ? "text" : "password";
            passwordInput.setAttribute("type", newType);

            // Toggle icon
            const icon = this.querySelector("i");
            if (icon) {
                if (icon.classList.contains("bi-eye-slash-fill")) {
                    icon.classList.remove("bi-eye-slash-fill");
                    icon.classList.add("bi-eye-fill");
                } else {
                    icon.classList.remove("bi-eye-fill");
                    icon.classList.add("bi-eye-slash-fill");
                }
            }
        });
    }

    /**
     * Initialize all password toggle buttons on the page
     */
    function initialize() {
        document.querySelectorAll(".toggle-password").forEach((toggleBtn) => {
            setupPasswordToggle(toggleBtn);
        });
    }

    // Standard initialization pattern - handles both early and late script loading
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
