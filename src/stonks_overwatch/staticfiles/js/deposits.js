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

    function redrawDepositsGraph(datasets, timeRange, minimumDate) {
        const timeRangeConfig = getTimeRangeConfig(timeRange, minimumDate);

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
                        beginAtZero: false,
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
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
                                        currency: "EUR",
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
