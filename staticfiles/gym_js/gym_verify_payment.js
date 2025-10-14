function verifyPayment(transactionId, status) {
    if (!status) return; // Ignore if no status selected

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const gymId = document.querySelector('[data-gym-id]').getAttribute('data-gym-id');

    fetch(`/gym/verify-payment-status/${gymId}/${transactionId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `status=${status}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update the select to show the selected status
            const select = document.querySelector(`tr[data-transaction-id="${transactionId}"] select`);
            if (select) {
                select.value = status;
            }
            // Show success message
            showMessage(data.message, 'success');
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage(`An error occurred while verifying the payment: ${error.message}`, 'error');
    });
}

function showMessage(message, type) {
    // Create a temporary message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `fixed top-4 right-4 px-4 py-2 rounded-md text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} z-50`;
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);

    // Remove the message after 3 seconds
    setTimeout(() => {
        document.body.removeChild(messageDiv);
    }, 3000);
}

function filterTransactions() {
    const statusFilter = document.getElementById('statusFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    const rows = document.querySelectorAll('.transaction-row');

    rows.forEach(row => {
        const status = row.getAttribute('data-status');
        const date = row.getAttribute('data-date');
        let showRow = true;

        if (statusFilter && status !== statusFilter) {
            showRow = false;
        }

        if (dateFilter && date !== dateFilter) {
            showRow = false;
        }

        row.style.display = showRow ? '' : 'none';
    });
}
