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

    const page = document.getElementById("dividends-page");
    if (!page) {
        return;
    }

    const dataUrl = page.dataset.url;
    const host = window.location.origin;
    const dividendsGrowth = readJsonScript("dividends-growth-data") || {};
    const diversificationOptions = readJsonScript("dividends-diversification-options") || [];
    const selectedDiversificationOption = readJsonScript("dividends-selected-diversification-option");
    const availableYears = readJsonScript("dividends-calendar-years") || [];
    const selectedCalendarYear = readJsonScript("dividends-selected-calendar-year");
    const diversificationLabels = readJsonScript("dividends-diversification-labels") || [];
    const diversificationValues = readJsonScript("dividends-diversification-values") || [];

    const autocolors = window["@seahsky/chartjs-plugin-autocolors"];

    function getDividendsPerMonth() {
        const months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ];

        const datasets = Object.entries(dividendsGrowth).map(([label, values]) => ({
            label: label,
            data: values,
            borderWidth: 1,
        }));

        return {
            labels: months,
            datasets: datasets,
        };
    }

    function getDividendsPerYear() {
        const years = [];
        const values = [];

        Object.entries(dividendsGrowth).forEach(([year, data]) => {
            const sum = data.reduce((acc, val) => acc + val, 0);
            years.push(Number(year));
            values.push(sum);
        });

        return {
            labels: years,
            datasets: [
                {
                    data: values,
                    borderWidth: 1,
                },
            ],
        };
    }

    function drawDividends(datatype) {
        const config = {
            type: "bar",
            data: datatype === "Month" ? getDividendsPerMonth() : getDividendsPerYear(),
            plugins: [autocolors].filter(Boolean),
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
                maintainAspectRatio: false,
                responsive: true,
                plugins: {
                    legend: {
                        display: false,
                        position: "top",
                    },
                    title: {
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
        };

        const chartStatus = Chart.getChart("dividends-growth");
        if (chartStatus !== undefined) {
            chartStatus.destroy();
        }

        new Chart(document.getElementById("dividends-growth").getContext("2d"), config);
    }

    function updateNavigationButtons(currentYearIndex) {
        const prevButton = $("#dividendsPrevYearButton");
        const nextButton = $("#dividendsNextYearButton");

        if (currentYearIndex >= availableYears.length - 1) {
            prevButton.prop("disabled", true).addClass("disabled");
        } else {
            prevButton.prop("disabled", false).removeClass("disabled");
        }

        if (currentYearIndex <= 0) {
            nextButton.prop("disabled", true).addClass("disabled");
        } else {
            nextButton.prop("disabled", false).removeClass("disabled");
        }
    }

    function loadCalendarYear(year) {
        $("#dividendsYearsDropdownButton").text(year);

        $("#dividendsYearsDropdown .dropdown-item").removeClass("active");
        $("#dividendsYearsDropdown .dropdown-item").each(function () {
            if (parseInt($(this).text()) === year) {
                $(this).addClass("active");
            }
        });

        const url = `${host}${dataUrl}?calendar_year=${year}&html_only=true`;

        fetch(url, {
            method: "GET",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
        })
            .then((response) => response.text())
            .then((html) => {
                const calendarContainer = document.getElementById("dividends-calendar-container");
                if (calendarContainer) {
                    calendarContainer.innerHTML = html;

                    const yearTotalElement = calendarContainer.querySelector("#calendar-year-total");
                    if (yearTotalElement) {
                        const yearTotal = yearTotalElement.dataset.yearTotal;
                        const visibleYearTotal = document.getElementById("dividendsYearTotal");
                        if (visibleYearTotal) {
                            visibleYearTotal.textContent = yearTotal;
                        }
                    }
                }
            })
            .catch((error) => {
                console.error("Error fetching calendar HTML:", error);
            });
    }

    function loadDiversification(option) {
        $("#dividendsDiversificationDropdownButton").text(option);

        $("#dividendsDiversificationDropdown .dropdown-item").removeClass("active");
        $("#dividendsDiversificationDropdown .dropdown-item").each(function () {
            if ($(this).text() === option) {
                $(this).addClass("active");
            }
        });

        const url = `${host}${dataUrl}?diversification_option=${encodeURIComponent(option)}`;

        fetch(url, {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                const container = document.getElementById("dividends-diversification-container");
                if (container) {
                    container.innerHTML = data.html;
                }

                const chart = Chart.getChart("dividends-chart");
                if (chart) {
                    chart.destroy();
                }

                drawDoughnutChart("dividends-chart", "", data.chartData.labels, data.chartData.values);
            })
            .catch((error) => {
                console.error("Error fetching dividends diversification:", error);
            });
    }

    $("#yearButton").on("click", function () {
        drawDividends("Year");
    });

    $("#monthButton").on("click", function () {
        drawDividends("Month");
    });

    drawDividends("Month");
    drawDoughnutChart("dividends-chart", "", diversificationLabels, diversificationValues);

    let currentYearIndex = availableYears.indexOf(selectedCalendarYear);
    if (currentYearIndex < 0) {
        currentYearIndex = 0;
    }

    updateNavigationButtons(currentYearIndex);

    $("#dividendsPrevYearButton").on("click", function (event) {
        event.preventDefault();
        if (currentYearIndex < availableYears.length - 1) {
            currentYearIndex += 1;
            const newYear = availableYears[currentYearIndex];
            loadCalendarYear(newYear);
            updateNavigationButtons(currentYearIndex);
        }
    });

    $("#dividendsNextYearButton").on("click", function (event) {
        event.preventDefault();
        if (currentYearIndex > 0) {
            currentYearIndex -= 1;
            const newYear = availableYears[currentYearIndex];
            loadCalendarYear(newYear);
            updateNavigationButtons(currentYearIndex);
        }
    });

    $("#dividendsYearsDropdown .dropdown-item").on("click", function (event) {
        event.preventDefault();
        const year = parseInt($(this).text());
        currentYearIndex = availableYears.indexOf(year);
        loadCalendarYear(year);
        updateNavigationButtons(currentYearIndex);
    });

    $("#dividendsDiversificationDropdown .dropdown-item").on("click", function (event) {
        event.preventDefault();
        loadDiversification($(this).text());
    });

    if (selectedDiversificationOption) {
        const selectedIndex = diversificationOptions.indexOf(selectedDiversificationOption);
        if (selectedIndex >= 0) {
            $("#dividendsDiversificationDropdown .dropdown-item").eq(selectedIndex).addClass("active");
        }
    }
})();
