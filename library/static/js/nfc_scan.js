document.addEventListener('DOMContentLoaded', () => {
    // Get all DOM elements
    const nfcForm = document.getElementById('nfc-form');
    const nfcIdInput = document.getElementById('nfc_id');
    const cardDisplay = document.getElementById('card-display');
    const errorMessageDiv = document.getElementById('error-message');
    const addCardBtn = document.getElementById('add-card-btn');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Helper functions for UI updates
    const showError = (message) => {
        errorMessageDiv.textContent = message;
        errorMessageDiv.classList.remove('hidden');
    };
    const hideError = () => {
        errorMessageDiv.classList.add('hidden');
        errorMessageDiv.textContent = '';
    };
    const showSuccessAndReset = (message) => {
        alert(message); // Simple success feedback
        nfcIdInput.value = '';
        cardDisplay.textContent = '';
        cardDisplay.classList.add('hidden');
        addCardBtn.disabled = true;
        addCardBtn.classList.add('opacity-50', 'cursor-not-allowed');
    };

    // NFC Reader Logic
    const initNFC = async () => {
        if (!('NDEFReader' in window)) {
            showError('Web NFC is not supported on this device or browser. Please use Chrome on Android.');
            return;
        }
        try {
            const ndef = new NDEFReader();
            await ndef.scan();
            ndef.addEventListener('reading', ({ serialNumber }) => {
                hideError();
                nfcIdInput.value = serialNumber;
                cardDisplay.textContent = `Scanned Card ID: ${serialNumber}`;
                cardDisplay.classList.remove('hidden');
                addCardBtn.disabled = false;
                addCardBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            });
            ndef.addEventListener('readingerror', () => {
                showError('Could not read NFC card. Please try again.');
            });
        } catch (error) {
            console.error(`Error starting NFC scan: ${error}`);
            alert(error)
            showError(`${error}`)

            // showError('Could not start NFC scanning. Check browser  and ensure a secure (HTTPS) connection.');
        }   
    };

    // AJAX Form Submission
    nfcForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cardId = nfcIdInput.value;
        if (!cardId) {
            showError('Please scan a card before submitting.');
            return;
        }

        hideError();
        addCardBtn.disabled = true;
        addCardBtn.textContent = 'Adding...';

        try {
            const response = await fetch(nfcForm.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ card_id: cardId }),
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                showSuccessAndReset(result.message);
            } else {
                showError(result.message || 'An unknown error occurred.');
                addCardBtn.disabled = false; // Re-enable on failure
            }
        } catch (networkError) {
            console.error('Network or submission error:', networkError);
            showError('A network error occurred. Please check your connection and try again.');
            addCardBtn.disabled = false; // Re-enable on failure
        } finally {
            if (!addCardBtn.disabled) {
                addCardBtn.textContent = 'Add Card';
            }
        }
    });
    document.getElementById('nfcread').addEventListener('click', async (event)=> {
        alert('NFC started scanning. Please tap your card.')
        await initNFC()
    });
});

