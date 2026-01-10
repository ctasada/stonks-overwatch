/**
 * Auto-submit the login form after a short delay.
 * Used for the loading/success state to transition to the dashboard.
 */
document.addEventListener('DOMContentLoaded', function () {
    const autoSubmitForm = document.getElementById('login-form');
    if (autoSubmitForm) {
        // Find the hidden input that indicates we should update portfolio
        const updatePortfolioInput = autoSubmitForm.querySelector('input[name="update_portfolio"]');

        // Only auto-submit if we are in the loading/update state
        if (updatePortfolioInput && updatePortfolioInput.value === 'true') {
            setTimeout(function () {
                autoSubmitForm.submit();
            }, 2000);
        }
    }
});
