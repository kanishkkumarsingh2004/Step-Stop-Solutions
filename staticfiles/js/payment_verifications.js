function handleStatusChange(event, form) {
    event.preventDefault();
    const formData = new FormData(form);
    const status = formData.get('status');
    const select = form.querySelector('select');
    const previousValue = select.value;
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('success', data.message);
            // Update the status in the UI
            select.value = status;
            // Add a visual indicator of the change
            select.classList.add('bg-green-100');
            setTimeout(() => {
                select.classList.remove('bg-green-100');
            }, 1000);
        } else {
            showToast('error', data.message || 'Failed to update status');
            // Reset the select to its previous value
            select.value = previousValue;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('error', 'An error occurred while verifying payment');
        // Reset the select to its previous value
        select.value = previousValue;
    });
    
    return false;
}

function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
} 