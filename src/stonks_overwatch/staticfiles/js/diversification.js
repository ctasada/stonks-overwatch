(function () {
    function readJsonScript(id) {
        const el = document.getElementById(id);
        if (!el) {
            return null;
        }
        try {
            return JSON.parse(el.textContent);
        } catch (error) {
            console.error("Failed to parse JSON script:", id, error);
            return null;
        }
    }

    function drawIfPresent(chartId, title, labelsId, valuesId) {
        if (!document.getElementById(chartId)) {
            return;
        }

        const labels = readJsonScript(labelsId);
        const values = readJsonScript(valuesId);
        if (!labels || !values) {
            return;
        }

        drawDoughnutChart(chartId, title, labels, values);
    }

    drawIfPresent("type-chart", "Type", "diversification-type-labels", "diversification-type-values");
    drawIfPresent("stocks-chart", "Stocks", "diversification-stocks-labels", "diversification-stocks-values");
    drawIfPresent("etfs-chart", "ETFs", "diversification-etfs-labels", "diversification-etfs-values");
    drawIfPresent("crypto-chart", "Crypto", "diversification-crypto-labels", "diversification-crypto-values");
    drawIfPresent("sectors-chart", "Sectors", "diversification-sectors-labels", "diversification-sectors-values");
    drawIfPresent("currencies-chart", "Currencies", "diversification-currencies-labels", "diversification-currencies-values");
    drawIfPresent("countries-chart", "Countries", "diversification-countries-labels", "diversification-countries-values");
})();
