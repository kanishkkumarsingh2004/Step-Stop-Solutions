document.addEventListener('DOMContentLoaded', function () {
    function handleStatusChange(event, form) {
        event.preventDefault();
        const formData = new FormData(form);
        const status = formData.get('status');
        const actionUrl = form.action;

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
                'Accept': 'application/json',
            },
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert('Payment status updated successfully.');
            } else {
                alert('Failed to update payment status: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            alert('Error updating payment status: ' + error.message);
        });
    }

    window.handleStatusChange = handleStatusChange;
});
