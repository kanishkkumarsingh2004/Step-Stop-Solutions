document.addEventListener('DOMContentLoaded', function () {
    // Helper function to parse data from hidden divs
    function getChartData(containerId) {
        const container = document.getElementById(containerId);
        return {
            labels: container.dataset.labels.split(',').filter(Boolean),
            values: container.dataset.values.split(',').filter(Boolean).map(Number)
        };
    }

    // Initialize Card Allocation Chart
    const cardAllocationData = getChartData('cardAllocationData');
    const cardAllocationCtx = document.getElementById('cardAllocationChart').getContext('2d');
    new Chart(cardAllocationCtx, {
        type: 'bar',
        data: {
            labels: cardAllocationData.labels,
            datasets: [{
                label: 'Allocated Cards',
                data: cardAllocationData.values,
                backgroundColor: 'rgba(79, 70, 229, 0.2)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Cards' },
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    title: { display: true, text: 'Libraries' }
                }
            }
        }
    });

    // Initialize Institution Card Allocation Chart
    const institutionCardData = getChartData('institutionCardAllocationData');
    const institutionCardCtx = document.getElementById('institutionCardAllocationChart').getContext('2d');
    new Chart(institutionCardCtx, {
        type: 'bar',
        data: {
            labels: institutionCardData.labels,
            datasets: [{
                label: 'Allocated Cards',
                data: institutionCardData.values,
                backgroundColor: 'rgba(234, 179, 8, 0.2)',
                borderColor: 'rgba(234, 179, 8, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Cards' },
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    title: { display: true, text: 'Institutions' }
                }
            }
        }
    });

    // Initialize User Status Chart
    const userStatusData = getChartData('userStatusData');
    const userStatusCtx = document.getElementById('userStatusChart').getContext('2d');
    new Chart(userStatusCtx, {
        type: 'doughnut',
        data: {
            labels: userStatusData.labels,
            datasets: [{
                label: 'User Count',
                data: userStatusData.values,
                backgroundColor: [
                    'rgba(79, 70, 229, 0.2)',
                    'rgba(255, 99, 132, 0.2)'
                ],
                borderColor: [
                    'rgba(79, 70, 229, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            }
        }
    });

    // Initialize Subscription Status Chart
    const subscriptionData = getChartData('subscriptionData');
    const subscriptionCtx = document.getElementById('subscriptionChart').getContext('2d');
    new Chart(subscriptionCtx, {
        type: 'pie',
        data: {
            labels: subscriptionData.labels,
            datasets: [{
                label: 'Subscription Count',
                data: subscriptionData.values,
                backgroundColor: [
                    'rgba(79, 70, 229, 0.2)',
                    'rgba(255, 99, 132, 0.2)'
                ],
                borderColor: [
                    'rgba(79, 70, 229, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            }
        }
    });

    // Initialize Cumulative Admin Expense Chart
    const cumulativeExpenseContainer = document.getElementById('cumulativeExpenseData');
    const labels = cumulativeExpenseContainer.dataset.labels.split(',').filter(Boolean);
    const profitValues = cumulativeExpenseContainer.dataset.profit.split(',').filter(Boolean).map(Number);
    const lossValues = cumulativeExpenseContainer.dataset.loss.split(',').filter(Boolean).map(Number);
    const cumulativeExpenseCtx = document.getElementById('cumulativeExpenseChart').getContext('2d');
    new Chart(cumulativeExpenseCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative Profit',
                data: profitValues,
                fill: false,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }, {
                label: 'Cumulative Loss',
                data: lossValues,
                fill: false,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Date' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Cumulative Amount' }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            }
        }
    });

    // Initialize Cumulative Balance Chart
    const cumulativeBalanceContainer = document.getElementById('cumulativeBalanceData');
    const balanceLabels = cumulativeBalanceContainer.dataset.labels.split(',').filter(Boolean);
    const balanceValues = cumulativeBalanceContainer.dataset.balance.split(',').filter(Boolean).map(Number);
    const cumulativeBalanceCtx = document.getElementById('cumulativeBalanceChart').getContext('2d');
    new Chart(cumulativeBalanceCtx, {
        type: 'line',
        data: {
            labels: balanceLabels,
            datasets: [{
                label: 'Cumulative Balance',
                data: balanceValues,
                fill: false,
                borderColor: 'rgba(255, 206, 86, 1)', // Yellow
                backgroundColor: 'rgba(255, 206, 86, 0.2)', // Yellow with transparency
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Date' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Cumulative Balance' }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: { enabled: true }
            }
        }
    });
});
