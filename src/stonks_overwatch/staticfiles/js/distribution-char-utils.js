// Customize colors with https://www.npmjs.com/package/@seahsky/chartjs-plugin-autocolors#customize
const autocolors = window['@seahsky/chartjs-plugin-autocolors'];
const currencySymbol = JSON.parse(document.getElementById('currency-symbol').textContent);

// Generalized function to draw a doughnut chart
function drawDoughnutChart(chartId, pieTitle, chartLabels, chartValues) {
    let valuesDict = [
        chartLabels.map(function(label, index) {
            return {
                "label": label,
                "value": chartValues[index]
            };
        })
    ];

    const data = {
        labels: chartLabels,
        datasets: [
            {
                data: chartValues,
                borderWidth: 1,
            }
        ]
    };

    const configDoughnut = {
        type: 'doughnut',
        data: data,
        plugins: [autocolors],
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let value = valuesDict[context.datasetIndex][context.dataIndex].value;
                            value = Intl.NumberFormat().format(value);
                            return currencySymbol + ' ' + value;
                        }
                    }
                },
                title: {
                    display: true,
                    text: pieTitle,
                    font: { size: 20 }
                },
                autocolors: { mode: 'data', offset: 5 }
            }
        }
    };

    new Chart(document.getElementById(chartId).getContext("2d"), configDoughnut);
}