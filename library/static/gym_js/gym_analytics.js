// gym_analytics.js
// Renders all gym analytics charts using Chart.js and data from hidden divs

document.addEventListener('DOMContentLoaded', function() {
    try {
        // Get data from hidden divs
        const dataElements = document.querySelectorAll('#gymAnalyticsData > span');
        const data = {};
        
        dataElements.forEach(element => {
            const key = element.id.replace('Data', '');
            try {
                data[key] = JSON.parse(element.textContent);
            } catch (error) {
                console.error(`Error parsing data for ${key}:`, error);
                data[key] = null;
            }
        });

        // Helper function to create charts
        const createChart = (elementId, config) => {
            const ctx = document.getElementById(elementId).getContext('2d');
            return new Chart(ctx, config);
        };

        // 1. Income vs Expenses Over Time (Line Chart)
        if (data.incomeExpense) {
            createChart('income-expense-line', {
                type: 'line',
                data: {
                    labels: data.incomeExpense.labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data.incomeExpense.income,
                            borderColor: '#16a34a',
                            backgroundColor: 'rgba(22,163,74,0.1)',
                            fill: true,
                            tension: 0.4,
                        },
                        {
                            label: 'Expenses',
                            data: data.incomeExpense.expenses,
                            borderColor: '#dc2626',
                            backgroundColor: 'rgba(220,38,38,0.1)',
                            fill: true,
                            tension: 0.4,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } },
                    scales: { 
                        x: { title: { display: true, text: 'Date' } }, 
                        y: { title: { display: true, text: 'Amount (₹)' } } 
                    }
                }
            });
        }

        // 2. Profit vs Loss Pie
        if (data.profitLoss) {
            createChart('profit-loss-pie', {
                type: 'pie',
                data: {
                    labels: ['Profit', 'Loss'],
                    datasets: [{
                        data: [data.profitLoss.profit, data.profitLoss.loss],
                        backgroundColor: ['#16a34a', '#dc2626'],
                    }]
                },
                options: { 
                    responsive: true, 
                    plugins: { legend: { position: 'bottom' } } 
                }
            });
        }

        // 3. Monthly Income & Expenses Trend (Bar)
        if (data.monthlyTrend) {
            createChart('monthly-trend-bar', {
                type: 'bar',
                data: {
                    labels: data.monthlyTrend.labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data.monthlyTrend.income,
                            backgroundColor: '#16a34a',
                        },
                        {
                            label: 'Expenses',
                            data: data.monthlyTrend.expenses,
                            backgroundColor: '#dc2626',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } },
                    scales: { 
                        x: { title: { display: true, text: 'Month' } }, 
                        y: { title: { display: true, text: 'Amount (₹)' } } 
                    }
                }
            });
        }

        // 4. Payment Method Breakdown (Bar)
        if (data.paymentMethod) {
            createChart('payment-method-bar', {
                type: 'bar',
                data: {
                    labels: data.paymentMethod.labels,
                    datasets: [{
                        label: 'Amount',
                        data: data.paymentMethod.amounts,
                        backgroundColor: ['#16a34a', '#2563eb', '#f59e42'],
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { 
                        x: { title: { display: true, text: 'Payment Method' } }, 
                        y: { title: { display: true, text: 'Amount (₹)' } } 
                    }
                }
            });
        }

        // 5. Expense Category Bar
        if (data.expenseCategory) {
            createChart('expense-category-bar', {
                type: 'bar',
                data: {
                    labels: data.expenseCategory.labels,
                    datasets: [{
                        label: 'Expenses',
                        data: data.expenseCategory.amounts,
                        backgroundColor: '#dc2626',
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { 
                        x: { title: { display: true, text: 'Category' } }, 
                        y: { title: { display: true, text: 'Amount (₹)' } } 
                    }
                }
            });
        }

        // 6. Cumulative Balance Over Time (Line)
        if (data.cumulativeBalance) {
            createChart('cumulative-balance-line', {
                type: 'line',
                data: {
                    labels: data.cumulativeBalance.labels,
                    datasets: [{
                        label: 'Cumulative Balance',
                        data: data.cumulativeBalance.balances,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37,99,235,0.1)',
                        fill: true,
                        tension: 0.4,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } },
                    scales: { 
                        x: { title: { display: true, text: 'Date' } }, 
                        y: { title: { display: true, text: 'Balance (₹)' } } 
                    }
                }
            });
        }

        // 7. Recent Transactions Table
        if (data.recentTransactions) {
            const tableDiv = document.getElementById('recent-transactions-table');
            const tableHtml = `
                <table class="min-w-full divide-y divide-gray-200 text-xs md:text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-2 py-1 text-left">Date</th>
                            <th class="px-2 py-1 text-left">Type</th>
                            <th class="px-2 py-1 text-left">Description</th>
                            <th class="px-2 py-1 text-right">Amount</th>
                            <th class="px-2 py-1 text-right">Balance</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-100">
                        ${data.recentTransactions.map(txn => `
                            <tr>
                                <td class="px-2 py-1 whitespace-nowrap">${txn.date}</td>
                                <td class="px-2 py-1">${txn.type === 'profit' ? '<span class="text-green-700">Profit</span>' : '<span class="text-red-600">Loss</span>'}</td>
                                <td class="px-2 py-1">${txn.description}</td>
                                <td class="px-2 py-1 text-right font-mono ${txn.type === 'profit' ? 'text-green-700' : 'text-red-600'}">₹${txn.amount}</td>
                                <td class="px-2 py-1 text-right font-mono">₹${txn.balance}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            tableDiv.innerHTML = tableHtml;
        }
    } catch (error) {
        console.error('Error loading analytics data:', error);
        // Display error message to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded';
        errorDiv.textContent = 'Failed to load analytics data. Please try again later.';
        document.querySelector('.container').prepend(errorDiv);
    }
});