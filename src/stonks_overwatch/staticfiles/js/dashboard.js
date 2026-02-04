(function () {
    const page = document.getElementById("dashboard-page");
    if (!page) {
        return;
    }

    const dataUrl = page.dataset.url;
    const host = window.location.origin;

    const RED = "rgba(239, 83, 67, 0.75)";
    const GREEN = "rgba(38, 169, 79, 0.75)";
    const BLUE = "rgba(92, 157, 233, 0.75)";

    const PortfolioTypes = {
        VALUE: "value",
        PERFORMANCE: "performance",
    };

    const TimeRanges = {
        YTD: "YTD",
        MTD: "MTD",
        M1: "1M",
        M3: "3M",
        M6: "6M",
        Y1: "1Y",
        Y3: "3Y",
        Y5: "5Y",
        ALL: "ALL",
    };

    const ALL_TIME_PERFORMANCE_GROUP = "ALLTIME";

    function getSelectedPortfolioType() {
        const activeTab = $("#portfolioType .nav-link.active");
        const id = activeTab.attr("id");
        if (id === "performancePortfolio") {
            return PortfolioTypes.PERFORMANCE;
        }
        return PortfolioTypes.VALUE;
    }

    function getSelectedTimeRange() {
        const activeButton = $('.btn-group input[type="radio"]:checked');
        switch (activeButton.attr("id")) {
            case "YTDButton":
                return TimeRanges.YTD;
            case "MTDButton":
                return TimeRanges.MTD;
            case "1MButton":
                return TimeRanges.M1;
            case "3MButton":
                return TimeRanges.M3;
            case "6MButton":
                return TimeRanges.M6;
            case "1YButton":
                return TimeRanges.Y1;
            case "3YButton":
                return TimeRanges.Y3;
            case "5YButton":
                return TimeRanges.Y5;
            case "allButton":
            default:
                return TimeRanges.ALL;
        }
    }

    $("#portfolioType a").on("click", function (event) {
        event.preventDefault();
        $("#portfolioType .nav-link.active").removeClass("active").attr("aria-selected", "false");
        $(this).addClass("active").attr("aria-selected", "true");

        drawPortfolio(getSelectedPortfolioType(), getSelectedTimeRange());
    });

    $("#YTDButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.YTD);
    });
    $("#MTDButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.MTD);
    });
    $("#1MButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.M1);
    });
    $("#3MButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.M3);
    });
    $("#6MButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.M6);
    });
    $("#1YButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y1);
    });
    $("#3YButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y3);
    });
    $("#5YButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y5);
    });
    $("#allButton").on("click", function () {
        drawPortfolio(getSelectedPortfolioType(), TimeRanges.ALL);
    });

    const autocolors = window["@seahsky/chartjs-plugin-autocolors"];

    function getTimeRangeConfig(timeRange, minimumDate) {
        const today = new Date();
        const config = {
            minDate: minimumDate,
            maxDate: today,
            timeUnit: "month",
            timeRound: "day",
        };

        switch (timeRange) {
            case TimeRanges.YTD:
                config.minDate = new Date(
                    Math.max(new Date(minimumDate).getTime(), new Date(new Date().getFullYear(), 0, 1).getTime()),
                );
                config.timeUnit = "week";
                break;
            case TimeRanges.MTD:
                config.minDate = new Date(
                    Math.max(
                        new Date(minimumDate).getTime(),
                        new Date(new Date().getFullYear(), new Date().getMonth(), 1).getTime(),
                    ),
                );
                config.timeUnit = "day";
                break;
            case TimeRanges.M1: {
                const oneMonthAgo = new Date(today);
                oneMonthAgo.setMonth(today.getMonth() - 1);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), oneMonthAgo.getTime()));
                config.timeUnit = "day";
                break;
            }
            case TimeRanges.M3: {
                const threeMonthsAgo = new Date(today);
                threeMonthsAgo.setMonth(today.getMonth() - 3);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), threeMonthsAgo.getTime()));
                config.timeUnit = "day";
                break;
            }
            case TimeRanges.M6: {
                const sixMonthsAgo = new Date(today);
                sixMonthsAgo.setMonth(today.getMonth() - 6);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), sixMonthsAgo.getTime()));
                config.timeUnit = "week";
                break;
            }
            case TimeRanges.Y1: {
                const oneYearAgo = new Date(today);
                oneYearAgo.setFullYear(today.getFullYear() - 1);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), oneYearAgo.getTime()));
                config.timeUnit = "week";
                break;
            }
            case TimeRanges.Y3: {
                const threeYearsAgo = new Date(today);
                threeYearsAgo.setFullYear(today.getFullYear() - 3);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), threeYearsAgo.getTime()));
                config.timeUnit = "month";
                break;
            }
            case TimeRanges.Y5: {
                const fiveYearsAgo = new Date(today);
                fiveYearsAgo.setFullYear(today.getFullYear() - 5);
                config.minDate = new Date(Math.max(new Date(minimumDate).getTime(), fiveYearsAgo.getTime()));
                config.timeUnit = "month";
                break;
            }
            case TimeRanges.ALL:
                config.minDate = minimumDate;
                config.timeUnit = "month";
                break;
        }
        return config;
    }

    function getTooltipLabel(portfolioType) {
        if (portfolioType === PortfolioTypes.PERFORMANCE) {
            return function (context) {
                let label = context.dataset.label || "";

                if (label) {
                    label += ": ";
                }
                if (context.parsed.y !== null) {
                    label += (context.parsed.y * 100).toFixed(2) + "%";
                }
                return label;
            };
        }
        return function (context) {
            let label = context.dataset.label || "";

            if (label) {
                label += ": ";
            }
            if (context.parsed.y !== null) {
                label += new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR" }).format(
                    context.parsed.y,
                );
            }
            return label;
        };
    }

    function getYAxisTicksCallback(portfolioType) {
        if (portfolioType === PortfolioTypes.PERFORMANCE) {
            return function (value) {
                return (value * 100).toFixed(2) + "%";
            };
        }
        return function (value) {
            return new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR" }).format(value);
        };
    }

    function getPortfolioConfiguration(portfolioType) {
        return {
            type: "line",
            data: {
                datasets: [
                    {
                        data: [],
                        stepped: false,
                        lineTension: 0.1,
                    },
                    ...(portfolioType === PortfolioTypes.VALUE ? [{ data: [], stepped: true }] : []),
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            callback: getYAxisTicksCallback(portfolioType),
                            color: window.CHART_TEXT_COLOR || "#666",
                        },
                    },
                    x: {
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            color: window.CHART_TEXT_COLOR || "#666",
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
                        labels: {
                            font: {
                                family: "'Poppins', 'sans-serif'",
                                size: 14,
                            },
                            onClick: function (click, legendItem, legend) {
                                const datasets = legend.legendItems.map((dataset) => dataset.text);
                                const index = datasets.indexOf(legendItem.text);
                                if (legend.chart.isDatasetVisible(index) === true) {
                                    legend.chart.hide(index);
                                } else {
                                    legend.chart.show(index);
                                }
                            },
                            generateLabels: function (chart) {
                                const visibility = [];
                                for (let i = 0; i < chart.data.datasets.length; i += 1) {
                                    if (chart.isDatasetVisible(i) === true) {
                                        visibility.push(window.CHART_TEXT_COLOR || "#666");
                                    } else {
                                        visibility.push(
                                            window.CHART_TEXT_COLOR === "#e0e0e0"
                                                ? "rgba(255, 255, 255, 0.3)"
                                                : "rgba(0, 0, 0, 0.3)",
                                        );
                                    }
                                }
                                const items = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                for (let i = 0; i < items.length; i += 1) {
                                    items[i].fontColor = visibility[i];
                                    items[i].hidden = false;
                                }
                                return items;
                            },
                        },
                    },
                    zoom: {
                        limits: {
                            x: {
                                min: null,
                                max: null,
                                minRange: 1000 * 60 * 60 * 24 * 7,
                            },
                            y: {
                                min: null,
                                max: null,
                            },
                        },
                        pan: {
                            enabled: true,
                            mode: "x",
                            modifierKey: null,
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.1,
                            },
                            pinch: {
                                enabled: true,
                            },
                            mode: "x",
                            onZoomComplete({ chart }) {
                                chart.update("none");
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: getTooltipLabel(portfolioType),
                        },
                    },
                },
            },
        };
    }

    function drawPortfolio(portfolioType, timeRange) {
        const configPortfolio = getPortfolioConfiguration(portfolioType);

        let chart = Chart.getChart("portofolio-chart");
        if (chart !== undefined) {
            chart.destroy();
        }
        chart = new Chart(document.getElementById("portofolio-chart").getContext("2d"), configPortfolio);

        chart.options.onClick = (event) => {
            if (event.native?.detail === 2) {
                chart.resetZoom();
            }
        };

        const url = `${host}${dataUrl}?type=${portfolioType}&interval=${timeRange}`;
        fetch(url, {
            headers: {
                Accept: "application/json",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok ${response.statusText}`);
                }
                return response.json();
            })
            .then((json) => {
                let data = [];
                if (portfolioType === PortfolioTypes.PERFORMANCE) {
                    data = json.portfolio.performance;
                    chart.data.datasets[0].data = data;
                    chart.data.datasets[0].data.labels = "Performance";
                    chart.data.datasets[1] = {};
                    chart.options.plugins.legend.display = false;
                } else {
                    data = json.portfolio.portfolio_value;
                    chart.data.datasets[0].data = data;
                    chart.data.datasets[0].label = "Portfolio Value";
                    chart.data.datasets[0].borderColor = GREEN;
                    chart.data.datasets[0].backgroundColor = GREEN;
                    chart.data.datasets[1].data = json.portfolio.cash_contributions;
                    chart.data.datasets[1].label = "Cash Contributions";
                    chart.data.datasets[1].borderColor = BLUE;
                    chart.data.datasets[1].backgroundColor = BLUE;
                    chart.options.plugins.legend.display = true;
                    chart.options.scales.y.suggestedMin = Math.min.apply(
                        null,
                        data.map((item) => item.y),
                    );
                }

                const timeRangeConfig = getTimeRangeConfig(timeRange, data[0].x);
                chart.options.scales.x = {
                    type: "time",
                    min: timeRangeConfig.minDate,
                    max: timeRangeConfig.maxDate,
                    time: {
                        tooltipFormat: "DD",
                        unit: timeRangeConfig.timeUnit,
                        round: timeRangeConfig.timeRound,
                    },
                };

                chart.options.plugins.zoom.limits = {
                    x: {
                        min: data[0].x,
                        max: new Date(),
                        minRange: 1000 * 60 * 60 * 24 * 7,
                    },
                };
                chart.update();
            })
            .catch((error) => {
                console.error("Error fetching the data:", error);
            });
    }

    function getSelectedPerformanceGroup(selectedElement) {
        const id = selectedElement.id;
        if (id === "allTime") {
            return ALL_TIME_PERFORMANCE_GROUP;
        }
        return id.replace("performanceByYear-", "");
    }

    $("#performanceYearsDropdown .dropdown-item").on("click", function (event) {
        event.preventDefault();
        $("#performanceYearsDropdown .dropdown-item").removeClass("active");
        $(this).addClass("active");
        $("#performanceYearsDropdownButton").text($(this).text());
        drawPerformance(getSelectedPerformanceGroup(event.currentTarget), getSelectedTimeRange());
    });

    function drawPerformance(performanceGroup, timeRange) {
        const datasets = {
            datasets: [
                {
                    data: [],
                    backgroundColor: function (context) {
                        if (!context || !context.parsed) {
                            return null;
                        }
                        const value = context.parsed.y;
                        return value < 0 ? RED : GREEN;
                    },
                    borderRadius: 5,
                },
            ],
        };

        const configPortfolio = {
            type: "bar",
            data: datasets,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            callback: function (value) {
                                return (value * 100).toFixed(2) + "%";
                            },
                            color: window.CHART_TEXT_COLOR || "#666",
                        },
                    },
                    x: {
                        grid: {
                            color:
                                window.CHART_TEXT_COLOR === "#e0e0e0"
                                    ? "rgba(255, 255, 255, 0.1)"
                                    : "rgba(0, 0, 0, 0.1)",
                        },
                        ticks: {
                            color: window.CHART_TEXT_COLOR || "#666",
                        },
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
                                    label += (context.parsed.y * 100).toFixed(2) + "%";
                                }
                                return label;
                            },
                        },
                    },
                },
            },
        };

        let chart = Chart.getChart("grouped-performance-chart");
        if (chart === undefined) {
            chart = new Chart(document.getElementById("grouped-performance-chart").getContext("2d"), configPortfolio);
        } else {
            chart.data = configPortfolio.data;
            chart.options = configPortfolio.options;
        }

        const url = `${host}${dataUrl}?interval=${timeRange}`;
        fetch(url, {
            headers: {
                Accept: "application/json",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok ${response.statusText}`);
                }
                return response.json();
            })
            .then((json) => {
                const data = performanceGroup === ALL_TIME_PERFORMANCE_GROUP
                    ? json.portfolio.annual_twr
                    : json.portfolio.monthly_twr[performanceGroup];
                chart.data.datasets[0].data = data;
                chart.update();
            })
            .catch((error) => {
                console.error("Error fetching the data:", error);
            });
    }

    drawPortfolio(PortfolioTypes.VALUE, TimeRanges.ALL);
    drawPerformance(ALL_TIME_PERFORMANCE_GROUP, TimeRanges.ALL);
})();
