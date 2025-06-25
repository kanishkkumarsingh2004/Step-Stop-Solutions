function openUpiModal() {
    document.getElementById('upiModal').classList.remove('hidden');
}
function closeUpiModal() {
    document.getElementById('upiModal').classList.add('hidden');
    document.getElementById('upiFormMsg').textContent = '';
}

document.addEventListener('DOMContentLoaded', function () {
    var upiForm = document.getElementById('upiForm');
    if (upiForm) {
        upiForm.onsubmit = function(e) {
            e.preventDefault();
            const form = e.target;
            const data = new FormData(form);
            fetch(form.getAttribute('data-action'), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: new URLSearchParams(data)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('upiFormMsg').textContent = 'UPI details updated!';
                    document.getElementById('upi-id-display').textContent = data.upi_id || '—';
                    document.getElementById('recipient-name-display').textContent = data.recipient_name || '—';
                    document.getElementById('thank-you-message-display').textContent = data.thank_you_message || '—';
                    setTimeout(closeUpiModal, 1000);
                } else {
                    document.getElementById('upiFormMsg').textContent = 'Failed to update UPI details.';
                }
            })
            .catch(() => {
                document.getElementById('upiFormMsg').textContent = 'An error occurred.';
            });
        };
    }
}); 