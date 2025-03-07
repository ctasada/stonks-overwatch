const PortfolioTypes = {
    VALUE: "value",
    PERFORMANCE: "performance",
}

const TimeRanges = {
    YTD: "YTD",
    MTD: "MTD",
    D1: "1D",
    W1: "1W",
    M1: "1M",
    M3: "3M",
    M6: "6M",
    Y1: "1Y",
    Y3: "3Y",
    Y5: "5Y",
    ALL: "ALL",
}

function getSelectedPortfolioType() {
    let activeTab = $('#portfolioType .nav-link.active');
    let id = activeTab.attr('id');
    if (id === "performancePortfolio") {
        return PortfolioTypes.PERFORMANCE
    }
    return PortfolioTypes.VALUE
}

function getSelectedTimeRange() {
    let activeButton = $('.btn-group input[type="radio"]:checked');
    switch (activeButton.attr('id')) {
        case "YTDButton":
            return TimeRanges.YTD
        case "MTDButton":
            return TimeRanges.MTD
        case "1DButton":
            return TimeRanges.D1
        case "1WButton":
            return TimeRanges.W1
        case "1MButton":
            return TimeRanges.M1
        case "3MButton":
            return TimeRanges.M3
        case "6MButton":
            return TimeRanges.M6
        case "1YButton":
            return TimeRanges.Y1
        case "3YButton":
            return TimeRanges.Y3
        case "5YButton":
            return TimeRanges.Y5
        case "allButton":
        default:
            return TimeRanges.ALL
    }
}

$('#portfolioType a').on('click', function (e) {
    e.preventDefault()
    $(".active").removeClass("active").attr('aria-selected', 'false');
    $(this).addClass("active").attr('aria-selected', 'true');

    drawPortfolio(getSelectedPortfolioType(), getSelectedTimeRange())
})

$('#YTDButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.YTD)
})
$('#MTDButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.MTD)
})
$('#1DButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.D1)
})
$('#1WButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.W1)
})
$('#1MButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.M1)
})
$('#3MButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.M3)
})
$('#6MButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.M6)
})
$('#1YButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y1)
})
$('#3YButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y3)
})
$('#5YButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.Y5)
})
$('#allButton').on('click', function () {
    drawPortfolio(getSelectedPortfolioType(), TimeRanges.ALL)
})
// Customize colors with https://www.npmjs.com/package/@seahsky/chartjs-plugin-autocolors#customize
const autocolors = window['@seahsky/chartjs-plugin-autocolors'];

function getTimeRangeConfig(timeRange, minimumDate) {
    const today = new Date()
    const config = {
        minDate: minimumDate,
        maxDate: today,
        timeUnit: 'month',
        timeRound: 'day'
    }
    switch (timeRange) {
        case TimeRanges.YTD:
            config.minDate = Math.max.apply(null, [minimumDate, new Date(new Date().getFullYear(), 0, 1)])
            config.timeUnit = 'week'
            break
        case TimeRanges.MTD:
            config.minDate = Math.max.apply(null, [minimumDate, new Date(new Date().getFullYear(), new Date().getMonth(), 1)])
            config.timeUnit = 'day'
            break
        case TimeRanges.D1:
            const yesterday = new Date(today)
            yesterday.setDate(today.getDate() - 1)
            config.minDate = Math.max.apply(null, [minimumDate, yesterday])
            config.timeUnit = 'day'
            break
        case TimeRanges.W1:
            const lastWeek = new Date(today)
            lastWeek.setDate(today.getDate() - 7)
            config.minDate = Math.max.apply(null, [minimumDate, lastWeek])
            config.timeUnit = 'day'
            break
        case TimeRanges.M1:
            const oneMonthAgo = new Date(today)
            oneMonthAgo.setMonth(today.getMonth() - 1)
            config.minDate = Math.max.apply(null, [minimumDate, oneMonthAgo])
            config.timeUnit = 'day'
            break
        case TimeRanges.M3:
            const threeMonthsAgo = new Date(today)
            threeMonthsAgo.setMonth(today.getMonth() - 3)
            config.minDate = Math.max.apply(null, [minimumDate, threeMonthsAgo])
            config.timeUnit = 'day'
            break
        case TimeRanges.M6:
            const sixMonthsAgo = new Date(today)
            sixMonthsAgo.setMonth(today.getMonth() - 6)
            config.minDate = Math.max.apply(null, [minimumDate, sixMonthsAgo])
            config.timeUnit = 'week'
            break
        case TimeRanges.Y1:
            const oneYearAgo = new Date(today)
            oneYearAgo.setFullYear(today.getFullYear() - 1)
            config.minDate = Math.max.apply(null, [minimumDate, oneYearAgo])
            config.timeUnit = 'week'
            break
        case TimeRanges.Y3:
            const threeYearsAgo = new Date(today)
            threeYearsAgo.setFullYear(today.getFullYear() - 3)
            config.minDate = Math.max.apply(null, [minimumDate, threeYearsAgo])
            config.timeUnit = 'month'
            break
        case TimeRanges.Y5:
            const fiveYearsAgo = new Date(today)
            fiveYearsAgo.setFullYear(today.getFullYear() - 5)
            config.minDate = Math.max.apply(null, [minimumDate, fiveYearsAgo])
            config.timeUnit = 'month'
            break
        case TimeRanges.ALL:
            config.minDate = minimumDate
            config.timeUnit = 'month'
            break
    }
    return config
}

function getTooltipLabel(portfolioType) {
    if (portfolioType === PortfolioTypes.PERFORMANCE) {
        return function (context) {
            let label = context.dataset.label || '';

            if (label) {
                label += ': ';
            }
            if (context.parsed.y !== null) {
                label += (context.parsed.y * 100).toFixed(2) + "%";
            }
            return label;
        }
    } else {
        return function (context) {
            let label = context.dataset.label || '';

            if (label) {
                label += ': ';
            }
            if (context.parsed.y !== null) {
                label += new Intl.NumberFormat('nl-NL', {style: 'currency', currency: 'EUR'}).format(context.parsed.y);
            }
            return label;
        }
    }
}

function getTicksCallback(portfolioType) {
    if (portfolioType === PortfolioTypes.PERFORMANCE) {
        return function (value, index, ticks) {
            return (value * 100).toFixed(2) + "%";
        }
    } else {
        return function (value, index, ticks) {
            return new Intl.NumberFormat('nl-NL', {style: 'currency', currency: 'EUR'}).format(value);
        }
    }
}

function getPortfolioConfiguration(portfolioType) {
    return {
        type: 'line',
        data: {
            datasets: [
                {
                    data: [],
                    stepped: false,
                    lineTension: 0.1
                },
                ...(portfolioType === PortfolioTypes.VALUE ? [{data: [], stepped: true}] : [])
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: getTicksCallback(portfolioType),
                    }
                }
            },
            elements: {
                point: {
                    radius: 0
                }
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
                            const datasets = legend.legendItems.map((dataset, index) => {
                                return dataset.text;
                            })
                            const index = datasets.indexOf(legendItem.text)
                            if (legend.chart.isDatasetVisible(index) === true) {
                                legend.chart.hide(index);
                            } else {
                                legend.chart.show(index);
                            }
                        },
                        generateLabels: function (chart) {
                            let visibility = [];
                            for (let i = 0; i < chart.data.datasets.length; i++) {
                                if (chart.isDatasetVisible(i) === true) {
                                    visibility.push('rgba(102, 102, 102, 1)');
                                } else {
                                    visibility.push('rgba(102, 102, 102, 0.5)');
                                }
                            }
                            const items = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                            for (let i = 0; i < items.length; i++) {
                                items[i].fontColor = visibility[i];
                                items[i].hidden = false;
                            }
                            return items
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: getTooltipLabel(portfolioType),
                    }
                }
            }
        },
    };
}

function drawPortfolio(portfolioType, timeRange) {
    const configPortfolio = getPortfolioConfiguration(portfolioType);

    let chart = Chart.getChart("portofolio-chart"); // <canvas> id
    if (chart !== undefined) {
        chart.destroy();
    }
    chart = new Chart(document.getElementById("portofolio-chart").getContext("2d"), configPortfolio);

    let url = HOST + URL + "?format=json&type=" + portfolioType + "&interval=" + timeRange
    // Fetch JSON data from a URL and update the chart
    fetch(url) // Replace with your JSON URL
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(json => {
            if (portfolioType === PortfolioTypes.PERFORMANCE) {
                data = json.portfolio.performance
                chart.data.datasets[0].data = data;
                chart.data.datasets[0].data.labels = 'Performance'
                chart.data.datasets[1] = {}
                chart.options.plugins.legend.display = false
            } else {
                data = json.portfolio.portfolio_value
                chart.data.datasets[0].data = data;
                chart.data.datasets[0].label = 'Portfolio Value'
                chart.data.datasets[0].borderColor = GREEN
                chart.data.datasets[0].backgroundColor = GREEN
                chart.data.datasets[1].data = json.portfolio.cash_contributions;
                chart.data.datasets[1].label = 'Cash Contributions'
                chart.data.datasets[1].borderColor = BLUE
                chart.data.datasets[1].backgroundColor = BLUE
                chart.options.plugins.legend.display = true
                chart.options.scales.y.suggestedMin = Math.min.apply(null, data.map(d => d.y))
            }

            const timeRangeConfig = getTimeRangeConfig(timeRange, data[0].x)
            chart.options.scales.x = {
                type: 'time',
                min: timeRangeConfig.minDate,
                max: timeRangeConfig.maxDate,
                time: {
                    // Luxon format string
                    tooltipFormat: 'DD',
                    unit: timeRangeConfig.timeUnit,
                    round: timeRangeConfig.timeRound,
                },
            }

            chart.update();
        })
        .catch(error => {
            console.error('Error fetching the data:', error);
        });
}

drawPortfolio(PortfolioTypes.VALUE, TimeRanges.ALL)