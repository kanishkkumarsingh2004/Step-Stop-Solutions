document.addEventListener('DOMContentLoaded', function() {
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('nfc-error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const userSelect = document.getElementById('user-select');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const libraryId = document.getElementById('library_id').value;

    if (!('NDEFReader' in window)) {
        errorMessageText.textContent = 'NFC is not supported in this browser.';
        errorMessageContainer.classList.remove('hidden');
        return;
    }

    const nfcReader = new NFCReader({
        onReading: (serialNumber) => {
            if (nfcIdDisplay) {
                checkNfcAllocation(serialNumber);
            }
        },
        onError: (error) => {
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error;
            }
            if (nfcIdDisplay) {
                nfcIdDisplay.textContent = 'Waiting for card...';
            }
        }
    });

    async function checkNfcAllocation(nfcSerial) {
        try {
            const response = await fetch('/check_nfc_allocation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: nfcSerial, library_id: libraryId })
            });

            const data = await response.json();

            if (data.allocated) {
                nfcIdDisplay.textContent = nfcSerial;
                activateButton?.classList.add('hidden');
                deleteButton?.classList.remove('hidden');
            } else {
                nfcIdDisplay.textContent = nfcSerial;
                activateButton?.classList.remove('hidden');
                deleteButton?.classList.add('hidden');
            }
        } catch (error) {
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error.message || 'Error checking NFC allocation. Please try again.';
            }
            nfcIdDisplay.textContent = 'Waiting for card...';
        }
    }
    if (activateButton && userSelect) {
        activateButton.addEventListener('click', async () => {
            activateButton.textContent = 'Allocating...';
            activateButton.disabled = true;
            activateButton.classList.remove('bg-green-600', 'hover:bg-green-700');
            activateButton.classList.add('bg-gray-600');

            const nfcSerial = nfcIdDisplay?.textContent?.trim() || '';
            const userId = userSelect.value.trim();
    
            if (nfcSerial === 'Waiting for card...' || !nfcSerial) {
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
    
            if (!userId) {
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
    
            if (!csrfToken) {
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
    
            try {
                const response = await fetch('/allocate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        nfc_serial: nfcSerial,
                        user_id: userId
                    })
                });
    
                const data = await response.json();
    
                if (response.ok) {
                    addLogMessage('User activated successfully!');
                    window.location.reload();
                } else {
                    addLogMessage(data.error || 'Failed to activate user');
                    // Re-enable button on error
                    activateButton.textContent = 'Activate User';
                    activateButton.disabled = false;
                    activateButton.classList.remove('bg-gray-600');
                    activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                }
            } catch (error) {
                addLogMessage('An error occurred while activating the user');
                // Re-enable button on error
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
            }
        });
    }

    // Start scanning automatically when window loads
    window.addEventListener('load', async () => {
        await nfcReader.startReading();
    });
});
