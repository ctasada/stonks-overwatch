(function () {
    function isColumnVisible(field) {
        try {
            const visibleColumns = $("#transactions-table").bootstrapTable("getVisibleColumns");
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

    window.isCurrencyColumnVisible = function () {
        return isColumnVisible("currency");
    };

    window.isTotalCurrencyColumnVisible = function () {
        return isColumnVisible("total_currency");
    };

    window.isBaseCurrencyColumnVisible = function () {
        return isColumnVisible("base_currency");
    };

    window.isFeesCurrencyColumnVisible = function () {
        return isColumnVisible("fees_currency");
    };

    window.priceFormatter = function (value, row) {
        if (window.isCurrencyColumnVisible()) {
            return value;
        }
        return row.formatted_price;
    };

    window.totalFormatter = function (value, row) {
        if (window.isTotalCurrencyColumnVisible()) {
            return value;
        }
        return row.formatted_total;
    };

    window.totalInBaseCurrencyFormatter = function (value, row) {
        if (window.isBaseCurrencyColumnVisible()) {
            return value;
        }
        return row.formatted_total_in_base_currency;
    };

    window.feesFormatter = function (value, row) {
        if (window.isFeesCurrencyColumnVisible()) {
            return value;
        }
        return row.formatted_fees;
    };
})();
