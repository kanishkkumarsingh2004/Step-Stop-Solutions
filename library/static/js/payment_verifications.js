document.addEventListener('DOMContentLoaded', function () {
    const dateInputs = document.querySelectorAll('.date-input');
    const statusSelects = document.querySelectorAll('.status-select');
    const toastContainer = document.getElementById('toast-container');

    dateInputs.forEach(input => {
        input.addEventListener('change', function () {
            const subscriptionId = this.dataset.subscriptionId;
            const dateType = this.dataset.dateType;
            const newDate = this.value;

            fetch(`/update_subscription_date/${subscriptionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({
                    date_type: dateType,
                    new_date: newDate,
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                showToast('An error occurred while updating the date.', 'error');
            });
        });
    });

    statusSelects.forEach(select => {
        select.addEventListener('change', function (event) {
            event.preventDefault();
            const transactionId = this.dataset.transactionId;
            const newStatus = this.value;

            const formData = new FormData();
            formData.append('status', newStatus);

            fetch(`/transactions/${transactionId}/update-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Accept': 'application/json',
                },
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                showToast('An error occurred while updating the status.', 'error');
            });
        });
    });

    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `p-4 mb-4 text-sm rounded-lg ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

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
});
