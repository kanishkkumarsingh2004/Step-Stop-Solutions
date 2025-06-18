document.addEventListener('DOMContentLoaded', function() {
    // Income vs Expenses Line Chart
    const incomeExpenseCtx = document.getElementById('incomeExpenseChart').getContext('2d');
    new Chart(incomeExpenseCtx, {
        type: 'line',
        data: {
            labels: JSON.parse(document.getElementById('dates').textContent),
            datasets: [{
                label: 'Income',
                data: JSON.parse(document.getElementById('income_data').textContent),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                tension: 0.1,
                fill: true
            }, {
                label: 'Expenses',
                data: JSON.parse(document.getElementById('expense_data').textContent),
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.raw;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });

    // Expense Types Pie Chart
    const expenseTypeCtx = document.getElementById('expenseTypeChart').getContext('2d');
    new Chart(expenseTypeCtx, {
        type: 'pie',
        data: {
            labels: JSON.parse(document.getElementById('expense_types').textContent),
            datasets: [{
                data: JSON.parse(document.getElementById('expense_type_data').textContent),
                backgroundColor: [
                    'rgb(239, 68, 68)',
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(139, 92, 246)',
                    'rgb(107, 114, 128)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ₹' + context.raw;
                        }
                    }
                }
            }
        }
    });

    // Payment Methods Bar Chart
    const paymentMethodCtx = document.getElementById('paymentMethodChart').getContext('2d');
    new Chart(paymentMethodCtx, {
        type: 'bar',
        data: {
            labels: JSON.parse(document.getElementById('payment_methods').textContent),
            datasets: [{
                label: 'Amount',
                data: JSON.parse(document.getElementById('payment_method_data').textContent),
                backgroundColor: [
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Amount: ₹' + context.raw;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });

    // Expense Categories Bar Chart
    const expenseCategoryCtx = document.getElementById('expenseCategoryBarChart').getContext('2d');
    new Chart(expenseCategoryCtx, {
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
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Amount: ₹' + context.raw;
                        }
                    }
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
                        callback: function(value) {
                            return '₹' + value;
                        },
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Monthly Trend Chart
    const monthlyTrendCtx = document.getElementById('monthlyTrendChart').getContext('2d');
    new Chart(monthlyTrendCtx, {
        type: 'bar',
        data: {
            labels: JSON.parse(document.getElementById('monthly_labels').textContent),
            datasets: [{
                label: 'Income',
                data: JSON.parse(document.getElementById('monthly_income').textContent),
                backgroundColor: 'rgb(34, 197, 94)'
            }, {
                label: 'Expenses',
                data: JSON.parse(document.getElementById('monthly_expenses').textContent),
                backgroundColor: 'rgb(239, 68, 68)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.raw;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}); 