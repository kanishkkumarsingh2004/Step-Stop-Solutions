document.addEventListener('DOMContentLoaded', function() {
    // Handle add expense form submission
    const addForm = document.getElementById('addExpenseForm');
    if (addForm) {
        addForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = {
                expense_name: formData.get('expense_name'),
                amount: formData.get('amount'),
                date: formData.get('date'),
                description: formData.get('description') || ''
            };

            try {
                const response = await fetch('/manage-admin-profit/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.status === 'success') {
                    // Add new profit to the list
                    addProfitToList(result.profit);
                    // Update total profits
                    updateTotalProfits();
                    // Reset form
                    this.reset();
                    customAlert('Profit added successfully');
                } else {
                    customAlert(result.message || 'Error adding profit');
                }
            } catch (error) {
                console.error('Error:', error);
                customAlert('An error occurred while adding the profit');
            }
        });
    }

    // Add event listeners to all edit buttons
    const editButtons = document.querySelectorAll('.edit-expense-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            // Verify all required data attributes are present
            const requiredAttributes = ['expenseId', 'expenseName', 'expenseAmount', 'expenseDate'];
            const missingAttributes = requiredAttributes.filter(attr => !this.dataset[attr]);

            if (missingAttributes.length > 0) {
                console.error('Missing required data attributes:', missingAttributes);
                return;
            }

            openEditModal({
                id: this.dataset.expenseId,
                name: this.dataset.expenseName,
                amount: this.dataset.expenseAmount,
                date: this.dataset.expenseDate,
                description: this.dataset.expenseDescription || ''
            });
        });
    });

    // Add event listeners to all delete buttons with custom confirm modal
    const deleteButtons = document.querySelectorAll('.delete-expense-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const expenseId = this.dataset.expenseId;
            openDeleteModal(expenseId);
        });
    });

    // Custom alert function
    function customAlert(message) {
        // Implement your custom alert UI here
        alert(message); // Placeholder using default alert
    }
    // Handle edit form submission
    const editForm = document.getElementById('editExpenseForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const expenseId = formData.get('expense_id');
            const data = {
                expense_name: formData.get('expense_name'),
                amount: formData.get('amount'),
                date: formData.get('date'),
                description: formData.get('description') || ''
            };
            try {
                const response = await fetch(`/edit-admin-expense/${expenseId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.status === 'success') {
                    // Update the expense in the list
                    updateExpenseInList(result.expense);
                    // Update total losses
                    updateTotalLosses();
                    // Close modal
                    closeEditModal();
                    alert('Expense updated successfully');
                } else {
                    alert(result.message || 'Error updating expense');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while updating the expense');
            }
        });
    }

    // Delete modal functions
    let currentDeleteExpenseId = null;

    function openDeleteModal(expenseId) {
        currentDeleteExpenseId = expenseId;
        const modal = document.getElementById('deleteExpenseModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function closeDeleteModal() {
        currentDeleteExpenseId = null;
        const modal = document.getElementById('deleteExpenseModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Handle delete modal buttons
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (currentDeleteExpenseId) {
                deleteExpense(currentDeleteExpenseId);
                closeDeleteModal();
            }
        });
    }

    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            closeDeleteModal();
        });
    }

    const closeDeleteModalBtn = document.getElementById('closeDeleteModalBtn');
    if (closeDeleteModalBtn) {
        closeDeleteModalBtn.addEventListener('click', function() {
            closeDeleteModal();
        });
    }

    // Edit modal functions
    function openEditModal(expense) {
        const modal = document.getElementById('editExpenseModal');
        if (!modal) {
            console.error('Edit modal not found');
            return;
        }

        // Set form values
        document.getElementById('editExpenseId').value = expense.id;
        document.getElementById('editExpenseName').value = expense.name;
        document.getElementById('editAmount').value = expense.amount;
        document.getElementById('editDate').value = expense.date;
        document.getElementById('editDescription').value = expense.description;

        // Show modal
        modal.classList.remove('hidden');
    }

    function closeEditModal() {
        const modal = document.getElementById('editExpenseModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Function to escape HTML
    function escapeHtml(text) {
        var map = {
            '&': '&amp;',
            '<': '<',
            '>': '>',
            '"': '"',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    // Function to add new expense to the list
    function addExpenseToList(expense) {
        const tbody = document.querySelector('#expensesTable tbody');
        if (!tbody) return;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${escapeHtml(expense.name)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹${expense.amount}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${expense.date}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(expense.description)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button class="edit-expense-btn text-indigo-600 hover:text-indigo-900 mr-2" data-expense-id="${expense.id}" data-expense-name="${escapeHtml(expense.name)}" data-expense-amount="${expense.amount}" data-expense-date="${expense.date}" data-expense-description="${escapeHtml(expense.description)}">Edit</button>
                <button class="delete-expense-btn text-red-600 hover:text-red-900" data-expense-id="${expense.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);

        // Re-attach event listeners to new buttons
        attachEventListeners();
    }

    // Function to update expense in the list
    function updateExpenseInList(expense) {
        const row = document.querySelector(`[data-expense-id="${expense.id}"]`).closest('tr');
        if (!row) return;

        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${escapeHtml(expense.name)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹${expense.amount}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${expense.date}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${escapeHtml(expense.description)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button class="edit-expense-btn text-indigo-600 hover:text-indigo-900 mr-2" data-expense-id="${expense.id}" data-expense-name="${escapeHtml(expense.name)}" data-expense-amount="${expense.amount}" data-expense-date="${expense.date}" data-expense-description="${escapeHtml(expense.description)}">Edit</button>
                <button class="delete-expense-btn text-red-600 hover:text-red-900" data-expense-id="${expense.id}">Delete</button>
            </td>
        `;

        // Re-attach event listeners to updated buttons
        attachEventListeners();
    }

    // Function to delete expense from the list
    async function deleteExpense(expenseId) {
        try {
            const response = await fetch(`/delete-admin-expense/${expenseId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            });

            const result = await response.json();
            if (result.status === 'success') {
                // Remove the expense from the list
                const row = document.querySelector(`[data-expense-id="${expenseId}"]`).closest('tr');
                if (row) row.remove();
                // Update total losses
                updateTotalLosses();
                alert('Expense deleted successfully');
            } else {
                alert(result.message || 'Error deleting expense');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while deleting the expense');
        }
    }

    // Function to update total losses
    async function updateTotalLosses() {
        try {
            const response = await fetch('/manage-admin-loss/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const totalElement = doc.querySelector('#totalLosses');
                if (totalElement) {
                    document.querySelector('#totalLosses').innerText = totalElement.innerText;
                }
            }
        } catch (error) {
            console.error('Error updating total losses:', error);
        }
    }

    // Function to attach event listeners to buttons
    function attachEventListeners() {
        // Re-attach edit buttons
        const editButtons = document.querySelectorAll('.edit-expense-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                openEditModal({
                    id: this.dataset.expenseId,
                    name: this.dataset.expenseName,
                    amount: this.dataset.expenseAmount,
                    date: this.dataset.expenseDate,
                    description: this.dataset.expenseDescription || ''
                });
            });
        });

        // Delete buttons are already attached at the top
    }

    // Make closeEditModal available globally
    window.closeEditModal = closeEditModal;
});
