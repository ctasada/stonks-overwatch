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

    const depositsData = readJsonScript("deposits-growth-data");
    if (!depositsData || depositsData.length === 0) {
        return;
    }

    const baseCurrency = readJsonScript("deposits-base-currency") || "EUR";

    const TimeRanges = {
        YTD: "YTD",
        Y1: "1Y",
        Y3: "3Y",
        Y5: "5Y",
        MAX: "MAX",
    };

    function getSelectedTimeRange() {
        const activeButton = $('.btn-group input[type="radio"]:checked');
        switch (activeButton.attr("id")) {
            case "YTDButton":
                return TimeRanges.YTD;
            case "1YButton":
                return TimeRanges.Y1;
            case "3YButton":
                return TimeRanges.Y3;
            case "5YButton":
                return TimeRanges.Y5;
            case "maxButton":
            default:
                return TimeRanges.MAX;
        }
    }

    $("#YTDButton").on("click", function () {
        drawDeposits(TimeRanges.YTD);
    });
    $("#1YButton").on("click", function () {
        drawDeposits(TimeRanges.Y1);
    });
    $("#3YButton").on("click", function () {
        drawDeposits(TimeRanges.Y3);
    });
    $("#5YButton").on("click", function () {
        drawDeposits(TimeRanges.Y5);
    });
    $("#maxButton").on("click", function () {
        drawDeposits(TimeRanges.MAX);
    });

    // Customize colors with https://www.npmjs.com/package/@seahsky/chartjs-plugin-autocolors#customize
    const autocolors = window["@seahsky/chartjs-plugin-autocolors"];

    function getTimeRangeConfig(timeRange, minimumDate) {
        const config = {
            minDate: minimumDate,
            maxDate: new Date(),
            timeUnit: "month",
            timeRound: "day",
        };
        switch (timeRange) {
            case TimeRanges.YTD:
                config.minDate = Math.max(minimumDate, new Date(new Date().getFullYear(), 0, 1));
                config.timeUnit = "week";
                break;
            case TimeRanges.Y1:
                config.minDate = Math.max(minimumDate, new Date(new Date().getFullYear() - 1, 0, 1));
                config.timeUnit = "week";
                break;
            case TimeRanges.Y3:
                config.minDate = Math.max(minimumDate, new Date(new Date().getFullYear() - 3, 0, 1));
                config.timeUnit = "month";
                break;
            case TimeRanges.Y5:
                config.minDate = Math.max(minimumDate, new Date(new Date().getFullYear() - 5, 0, 1));
                config.timeUnit = "month";
                break;
            case TimeRanges.MAX:
                config.minDate = minimumDate;
                config.timeUnit = "month";
                break;
        }
        return config;
    }

    function drawDeposits(timeRange) {
        const dataValue = {
            datasets: [
                {
                    label: "Deposits",
                    data: depositsData,
                    stepped: true,
                    fill: "start",
                },
            ],
        };

        const minimumDate = new Date(depositsData[0].x);
        redrawDepositsGraph(dataValue, timeRange, minimumDate);
    }

    /**
     * Compute an explicit Y-axis [0, niceMax] range for the deposits chart.
     *
     * Always anchors at zero (cumulative deposits start from nothing) and
     * rounds the ceiling up to a "nice" step boundary so Chart.js places
     * clean, evenly-spaced, always-distinct tick labels (e.g. €0 → €30K →
     * €60K → €90K → €120K) regardless of how many unique data values exist.
     */
    function computeYRange(datasets) {
        const yValues = datasets.datasets
            .flatMap((ds) => ds.data.map((p) => (p != null && typeof p === "object" ? p.y : p)))
            .filter((v) => v != null && isFinite(v));

        const dataMax = yValues.length > 0 ? Math.max(...yValues) : 0;

        if (dataMax <= 0) {
            return { min: 0, max: 100 };
        }

        // Add 20 % headroom then round up to the nearest "nice" step so we
        // always get ~5 evenly-spaced ticks that are clearly distinct.
        const rawMax = dataMax * 1.2;
        const roughStep = rawMax / 5;
        const stepMag = Math.pow(10, Math.floor(Math.log10(roughStep)));
        const niceStep = Math.ceil(roughStep / stepMag) * stepMag;
        const niceMax = Math.ceil(rawMax / niceStep) * niceStep;

        return { min: 0, max: niceMax };
    }

    function redrawDepositsGraph(datasets, timeRange, minimumDate) {
        const timeRangeConfig = getTimeRangeConfig(timeRange, minimumDate);
        const yRange = computeYRange(datasets);

        const configDeposits = {
            type: "line",
            data: datasets,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: "time",
                        min: timeRangeConfig.minDate,
                        max: timeRangeConfig.maxDate,
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            color: window.CHART_TEXT_COLOR || "#666",
                        },
                        time: {
                            tooltipFormat: "DD",
                            unit: timeRangeConfig.timeUnit,
                            round: timeRangeConfig.timeRound,
                        },
                    },
                    y: {
                        min: yRange.min,
                        max: yRange.max,
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            color: window.CHART_TEXT_COLOR || "#666",
                            callback: function (value) {
                                return new Intl.NumberFormat("nl-NL", {
                                    style: "currency",
                                    currency: baseCurrency,
                                    notation: "compact",
                                    maximumFractionDigits: 1,
                                }).format(value);
                            },
                        },
                    },
                },
                elements: {
                    point: {
                        radius: 0,
                    },
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || "";

                                if (label) {
                                    label += ": ";
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat("nl-NL", {
                                        style: "currency",
                                        currency: baseCurrency,
                                        maximumFractionDigits: 2,
                                    }).format(context.parsed.y);
                                }
                                return label;
                            },
                        },
                    },
                },
            },
            plugins: [autocolors].filter(Boolean),
        };

        const chartStatus = Chart.getChart("deposits-chart");
        if (chartStatus) {
            chartStatus.destroy();
        }

        new Chart(document.getElementById("deposits-chart").getContext("2d"), configDeposits);
    }

    drawDeposits(getSelectedTimeRange());
})();
