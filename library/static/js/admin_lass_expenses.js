document.addEventListener('DOMContentLoaded', function() {
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

    // Handle form submission
    const editForm = document.getElementById('editExpenseForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const expenseId = formData.get('expense_id');

            try {
                const response = await fetch(`/edit-admin-expense/${expenseId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    },
                    body: formData
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Error updating expense');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while updating the expense');
            }
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

    // Make closeEditModal available globally
    window.closeEditModal = closeEditModal;
});