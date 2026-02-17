/**
 * Sidebar state - applies collapsed state before render.
 */
(function () {
    if (localStorage.getItem("sidebarCollapsed") === "true") {
        document.documentElement.style.setProperty("--sidebar-immediate-state", "sidebar-collapsed");
    }
})();
