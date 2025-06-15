const ALL_TIME_PERFORMANCE_GROUP = "ALLTIME"

function getSelectedPerformanceGroup(selectedElement) {
    let id = selectedElement.id;

    if (id === "allTime") {
        return ALL_TIME_PERFORMANCE_GROUP
    }
    return id.replace("performanceByYear-", "")
}

$('#performanceYearsDropdown .dropdown-item').on('click', function (e) {
    e.preventDefault();
    // Remove active class from all items
    $('#performanceYearsDropdown .dropdown-item').removeClass('active');
    // Add active class to clicked item
    $(this).addClass('active');
    // Update the dropdown button text
    $('#performanceYearsDropdownButton').text($(this).text());
    drawPerformance(getSelectedPerformanceGroup(e.currentTarget), getSelectedTimeRange());
});

function drawPerformance(performanceGroup, timeRange) {
    const datasets = {
        datasets: [
            {
                data: [],
                backgroundColor: function(context) {
                    if (!context || !context.parsed)
                        return
                    const value = context.parsed.y;
                    return value < 0 ? RED : GREEN;
                },
                borderRadius: 5,
            }
        ],
    };

    const configPortfolio = {
        type: 'bar',
        data: datasets,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    ticks: {
                        callback: function (value, index, ticks) {
                            return (value * 100).toFixed(2) + "%";
                        },
                    }
                }
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';

                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += (context.parsed.y * 100).toFixed(2) + "%";
                            }
                            return label;
                        },
                    }
                }
            }
        },
    };

    let chart = Chart.getChart("grouped-performance-chart"); // <canvas> id
    if (chart === undefined) {
        chart = new Chart(document.getElementById("grouped-performance-chart").getContext("2d"), configPortfolio);
    } else {
        chart.data = configPortfolio.data
        chart.options = configPortfolio.options
    }

    let url = HOST + URL + "?interval=" + timeRange
    // Fetch JSON data from a URL and update the chart
    fetch(url,{
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(json => {
            if (performanceGroup === ALL_TIME_PERFORMANCE_GROUP) {
                data = json.portfolio.annual_twr
            } else {
                data = json.portfolio.monthly_twr[performanceGroup]
            }
            chart.data.datasets[0].data = data

            chart.update();
        })
        .catch(error => {
            console.error('Error fetching the data:', error);
        });
}

drawPerformance(ALL_TIME_PERFORMANCE_GROUP, TimeRanges.ALL)
