document.addEventListener('DOMContentLoaded', function() {
    // Handle add profit form submission
    const addForm = document.getElementById('addProfitForm');
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
                    closeAddProfitModal();
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
    const editButtons = document.querySelectorAll('.edit-profit-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            openEditProfitModal({
                id: this.dataset.profitId,
                name: this.dataset.profitName,
                amount: this.dataset.profitAmount,
                date: this.dataset.profitDate,
                description: this.dataset.profitDescription || ''
            });
        });
    });

    // Add event listeners to all delete buttons with custom confirm modal
    const deleteButtons = document.querySelectorAll('.delete-profit-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const profitId = this.dataset.profitId;
            openDeleteProfitModal(profitId);
        });
    });

    // Custom alert function
    function customAlert(message) {
        alert(message); // Placeholder using default alert
    }

    // Handle edit form submission
    const editForm = document.getElementById('editProfitForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const profitId = formData.get('profit_id');
            const data = {
                expense_name: formData.get('expense_name'),
                amount: formData.get('amount'),
                date: formData.get('date'),
                description: formData.get('description') || ''
            };
            try {
                const response = await fetch(`/edit-admin-profit/${profitId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.status === 'success') {
                    // Update the profit in the list
                    updateProfitInList(result.profit);
                    // Update total profits
                    updateTotalProfits();
                    // Close modal
                    closeEditProfitModal();
                    customAlert('Profit updated successfully');
                } else {
                    customAlert(result.message || 'Error updating profit');
                }
            } catch (error) {
                console.error('Error:', error);
                customAlert('An error occurred while updating the profit');
            }
        });
    }

    // Delete modal functions
    let currentDeleteProfitId = null;

    function openDeleteProfitModal(profitId) {
        currentDeleteProfitId = profitId;
        const modal = document.getElementById('deleteProfitModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function closeDeleteProfitModal() {
        currentDeleteProfitId = null;
        const modal = document.getElementById('deleteProfitModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Handle delete modal buttons
    const confirmDeleteBtn = document.getElementById('confirmDeleteProfitBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (currentDeleteProfitId) {
                deleteProfit(currentDeleteProfitId);
                closeDeleteProfitModal();
            }
        });
    }

    const cancelDeleteBtn = document.getElementById('cancelDeleteProfitBtn');
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            closeDeleteProfitModal();
        });
    }

    // Edit modal functions
    function openEditProfitModal(profit) {
        const modal = document.getElementById('editProfitModal');
        if (!modal) {
            console.error('Edit modal not found');
            return;
        }

        // Set form values
        document.getElementById('editProfitId').value = profit.id;
        document.getElementById('editProfitName').value = profit.name;
        document.getElementById('editProfitAmount').value = profit.amount;
        document.getElementById('editProfitDate').value = profit.date;
        document.getElementById('editProfitDescription').value = profit.description;

        // Show modal
        modal.classList.remove('hidden');
    }

    function closeEditProfitModal() {
        const modal = document.getElementById('editProfitModal');
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

    // Function to add new profit to the list
    function addProfitToList(profit) {
        const tbody = document.querySelector('#profitsTable tbody');
        if (!tbody) return;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-4 py-2 text-sm text-gray-700">${tbody.children.length + 1}</td>
            <td class="px-4 py-2 text-sm font-medium text-gray-800">${escapeHtml(profit.name)}</td>
            <td class="px-4 py-2 text-sm font-semibold text-green-600">₹${profit.amount}</td>
            <td class="px-4 py-2 text-sm text-gray-500">${profit.date}</td>
            <td class="px-4 py-2 text-sm text-gray-600">${escapeHtml(profit.description)}</td>
            <td class="px-4 py-2 text-sm text-gray-500">Admin</td>
            <td class="px-4 py-2 text-sm font-medium">
                <button class="edit-profit-btn text-indigo-600 hover:text-indigo-900 mr-2" data-profit-id="${profit.id}" data-profit-name="${escapeHtml(profit.name)}" data-profit-amount="${profit.amount}" data-profit-date="${profit.date}" data-profit-description="${escapeHtml(profit.description)}">Edit</button>
                <button class="delete-profit-btn text-red-600 hover:text-red-900" data-profit-id="${profit.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);

        // Re-attach event listeners to new buttons
        attachEventListeners();
    }

    // Function to update profit in the list
    function updateProfitInList(profit) {
        const row = document.querySelector(`[data-profit-id="${profit.id}"]`).closest('tr');
        if (!row) return;

        row.innerHTML = `
            <td class="px-4 py-2 text-sm text-gray-700">${row.cells[0].textContent}</td>
            <td class="px-4 py-2 text-sm font-medium text-gray-800">${escapeHtml(profit.name)}</td>
            <td class="px-4 py-2 text-sm font-semibold text-green-600">₹${profit.amount}</td>
            <td class="px-4 py-2 text-sm text-gray-500">${profit.date}</td>
            <td class="px-4 py-2 text-sm text-gray-600">${escapeHtml(profit.description)}</td>
            <td class="px-4 py-2 text-sm text-gray-500">Admin</td>
            <td class="px-4 py-2 text-sm font-medium">
                <button class="edit-profit-btn text-indigo-600 hover:text-indigo-900 mr-2" data-profit-id="${profit.id}" data-profit-name="${escapeHtml(profit.name)}" data-profit-amount="${profit.amount}" data-profit-date="${profit.date}" data-profit-description="${escapeHtml(profit.description)}">Edit</button>
                <button class="delete-profit-btn text-red-600 hover:text-red-900" data-profit-id="${profit.id}">Delete</button>
            </td>
        `;

        // Re-attach event listeners to updated buttons
        attachEventListeners();
    }

    // Function to delete profit from the list
    async function deleteProfit(profitId) {
        try {
            const response = await fetch(`/delete-admin-profit/${profitId}/`, {
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
                // Remove the profit from the list
                const row = document.querySelector(`[data-profit-id="${profitId}"]`).closest('tr');
                if (row) row.remove();
                // Update total profits
                updateTotalProfits();
                customAlert('Profit deleted successfully');
            } else {
                customAlert(result.message || 'Error deleting profit');
            }
        } catch (error) {
            console.error('Error:', error);
            customAlert('An error occurred while deleting the profit');
        }
    }

    // Function to update total profits
    async function updateTotalProfits() {
        try {
            const response = await fetch('/manage-admin-profit/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const totalElement = doc.querySelector('#totalProfits');
                if (totalElement) {
                    document.querySelector('#totalProfits').innerText = totalElement.innerText;
                }
            }
        } catch (error) {
            console.error('Error updating total profits:', error);
        }
    }

    // Function to attach event listeners to buttons
    function attachEventListeners() {
        // Re-attach edit buttons
        const editButtons = document.querySelectorAll('.edit-profit-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                openEditProfitModal({
                    id: this.dataset.profitId,
                    name: this.dataset.profitName,
                    amount: this.dataset.profitAmount,
                    date: this.dataset.profitDate,
                    description: this.dataset.profitDescription || ''
                });
            });
        });

        // Re-attach delete buttons
        const deleteButtons = document.querySelectorAll('.delete-profit-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const profitId = this.dataset.profitId;
                openDeleteProfitModal(profitId);
            });
        });
    }

    // Make close functions available globally
    window.closeAddProfitModal = function() {
        const modal = document.getElementById('addProfitModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    };

    window.closeEditProfitModal = closeEditProfitModal;

    // Open Add Profit Modal
    var openBtn = document.getElementById('openAddProfitModalBtn');
    if (openBtn) {
        openBtn.addEventListener('click', function() {
            const modal = document.getElementById('addProfitModal');
            if (modal) {
                modal.classList.remove('hidden');
            }
        });
    }
});
