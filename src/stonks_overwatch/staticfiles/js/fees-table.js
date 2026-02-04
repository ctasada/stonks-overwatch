(function () {
    function isTimeColumnVisible() {
        try {
            const visibleColumns = $("#fees-table").bootstrapTable("getVisibleColumns");
            return visibleColumns && visibleColumns.some((col) => col.field === "time");
        } catch (error) {
            return false;
        }
    }

    window.dateTimeFormatter = function (value, row) {
        if (isTimeColumnVisible()) {
            return value;
        }
        return `${value}<br><small class=\"fw-lighter\">${row.time}</small>`;
    };
})();
