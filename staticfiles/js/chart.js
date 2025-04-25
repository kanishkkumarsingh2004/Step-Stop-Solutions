document.addEventListener('DOMContentLoaded', function() {
    // Helper function to extract chart data from canvas elements
    function getChartData(canvasId) {
        const canvas = document.getElementById(canvasId);
        return {
            labels: JSON.parse(canvas.dataset.labels),
            values: JSON.parse(canvas.dataset.values)
        };
    }

    // Unified chart configuration for consistent professional appearance
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    font: {
                        size: 12,
                        family: 'Inter, sans-serif',
                        weight: '500'
                    },
                    padding: 12,
                    color: '#374151'
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0,0,0,0.85)',
                titleFont: { size: 14, weight: '600' },
                bodyFont: { size: 12, weight: '500' },
                padding: 12,
                cornerRadius: 6,
                displayColors: true,
                bodySpacing: 4,
                titleSpacing: 4
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#e5e7eb',
                    borderDash: [5, 5],
                    drawBorder: false
                },
                ticks: {
                    font: {
                        size: 12,
                        weight: '500'
                    },
                    padding: 8,
                    color: '#6b7280',
                    callback: function(value) {
                        return '₹' + value.toLocaleString();
                    }
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false
                },
                ticks: {
                    font: {
                        size: 12,
                        weight: '500'
                    },
                    padding: 8,
                    color: '#6b7280'
                }
            }
        }
    };

    // Chart configurations with enhanced visual hierarchy
    const charts = {
        earningsBarChart: {
            type: 'bar',
            data: {
                labels: ["Total Earnings", "Valid Transactions", "Invalid Transactions"],
                datasets: [{
                    label: 'Amount (₹)',
                    data: [
                        parseFloat(document.getElementById('totalEarnings').textContent),
                        parseFloat(document.getElementById('validTransactions').textContent),
                        parseFloat(document.getElementById('invalidTransactions').textContent)
                    ],
                    backgroundColor: ['#3b82f6', '#10b981', '#ef4444'],
                    borderColor: ['#2563eb', '#059669', '#dc2626'],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: commonOptions
        },
        expenseTransactionPieChart: {
            type: 'pie',
            data: {
                labels: ['Total Earnings', 'Valid Transactions', 'Total Expenses', 'Invalid Transactions'],
                datasets: [{
                    data: [
                        parseFloat(document.getElementById('totalEarnings').textContent),
                        parseFloat(document.getElementById('validTransactions').textContent),
                        parseFloat(document.getElementById('totalExpenses').textContent),
                        parseFloat(document.getElementById('invalidTransactions').textContent)
                    ],
                    backgroundColor: ['#3b82f6', '#10b981', '#f97316', '#ef4444'],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                },
                plugins: {
                    ...commonOptions.plugins,
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 16
                        }
                    }
                }
            }
        },
        expenseCategoryBarChart: {
            type: 'bar',
            data: {
                labels: JSON.parse(document.getElementById('expenseCategories').textContent),
                datasets: [{
                    label: 'Amount (₹)',
                    data: JSON.parse(document.getElementById('expenseAmounts').textContent),
                    backgroundColor: '#8b5cf6',
                    borderColor: '#7c3aed',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: commonOptions
        },
        expenseOverTimeLineChart: {
            type: 'line',
            data: {
                labels: JSON.parse(document.getElementById('dateLabels').textContent),
                datasets: [{
                    label: 'Expenses (₹)',
                    data: JSON.parse(document.getElementById('dateAmounts').textContent),
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#f59e0b',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.3
                }]
            },
            options: commonOptions
        },
        profitOverTimeLineChart: {
            type: 'line',
            data: {
                labels: JSON.parse(document.getElementById('profitLabels').textContent),
                datasets: [{
                    label: 'Profit (₹)',
                    data: JSON.parse(document.getElementById('profitValues').textContent),
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#3b82f6',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.3
                }]
            },
            options: commonOptions
        }
    };

    // Initialize all charts with enhanced error handling
    Object.entries(charts).forEach(([chartId, config]) => {
        const canvas = document.getElementById(chartId);
        if (canvas) {
            new Chart(canvas, config);
        } else {
            console.error(`Chart canvas not found: ${chartId}`);
        }
    });
});