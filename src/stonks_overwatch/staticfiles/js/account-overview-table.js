(function () {
    function isColumnVisible(field) {
        try {
            const visibleColumns = $("#account-overview-table").bootstrapTable("getVisibleColumns");
            return visibleColumns && visibleColumns.some((col) => col.field === field);
        } catch (error) {
            return false;
        }
    }

    window.isTimeColumnVisible = function () {
        return isColumnVisible("time");
    };

    window.dateTimeFormatter = function (value, row) {
        if (window.isTimeColumnVisible()) {
            return value;
        }
        return `${value}<br><small class=\"fw-lighter\">${row.time}</small>`;
    };

    window.isNameColumnVisible = function () {
        return isColumnVisible("name");
    };

    window.symbolNameFormatter = function (value, row) {
        if (window.isNameColumnVisible()) {
            return value;
        }
        return `${value}<br><small class=\"fw-lighter\">${row.name}</small>`;
    };
})();
