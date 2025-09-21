document.addEventListener('DOMContentLoaded', function() {
    // Get all subscription date inputs
    const dateInputs = document.querySelectorAll('.subscription-date');
    
    // Function to show notifications
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} z-50`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    // Function to handle date changes via AJAX
    function updateSubscriptionDate(input) {
        const libraryId = input.dataset.libraryId;
        const field = input.dataset.field;
        const value = input.value;

        const data = {};
        data[`${field}_date`] = value;
        
        fetch(`/admin-dashboard/library/${libraryId}/update-subscription/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Date updated successfully', 'success');
                input.style.borderColor = '#4CAF50';
            } else {
                showNotification(data.error || 'Error updating date', 'error');
                input.style.borderColor = '#FF5252';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error updating date', 'error');
            input.style.borderColor = '#FF5252';
        });
    }
    
    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Add event listeners to all date inputs
    dateInputs.forEach(input => {
        input.addEventListener('change', () => {
            updateSubscriptionDate(input);
        });
    });
});