document.addEventListener('DOMContentLoaded', () => {
    const deleteButton = document.getElementById('delete-user-button');
    const deallocateModal = document.getElementById('deallocate-modal');
    const confirmDeallocate = document.getElementById('confirm-deallocate');
    const cancelDeallocate = document.getElementById('cancel-deallocate');
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const infoContainer = document.getElementById('nfc-user-info');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    const handleDeallocate = async () => {
        const nfcSerial = nfcIdDisplay?.textContent?.trim();
        
        if (!nfcSerial || nfcSerial === 'Waiting for card...') {
            alert('Please scan an NFC card first');
            return;
        }

        try {
            confirmDeallocate.disabled = true;
            confirmDeallocate.textContent = 'Deallocating...';

            const response = await fetch('/deallocate-nfc/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: nfcSerial })
            });

            const data = await response.json();

            if (response.ok) {
                alert('NFC ID deallocated successfully');
                nfcIdDisplay.textContent = 'Waiting for card...';
                deleteButton?.classList.add('hidden');
                activateButton?.classList.remove('hidden');
                
                // Clear user info
                if (infoContainer) infoContainer.innerHTML = '';
            } else {
                alert('Error: ' + (data.error || 'Failed to deallocate NFC ID'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while deallocating the NFC ID');
        } finally {
            confirmDeallocate.disabled = false;
            confirmDeallocate.textContent = 'Deallocate';
            deallocateModal?.classList.add('hidden');
        }
    };

    deleteButton?.addEventListener('click', () => deallocateModal?.classList.remove('hidden'));
    cancelDeallocate?.addEventListener('click', () => deallocateModal?.classList.add('hidden'));
    confirmDeallocate?.addEventListener('click', handleDeallocate);
});
