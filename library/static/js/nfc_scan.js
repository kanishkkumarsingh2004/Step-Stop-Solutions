document.addEventListener('DOMContentLoaded', () => {
    // Get all DOM elements
    const nfcForm = document.getElementById('nfc-form');
    const nfcIdInput = document.getElementById('nfc_id');
    const cardDisplay = document.getElementById('card-display');
    const errorMessageDiv = document.getElementById('error-message');
    const addCardBtn = document.getElementById('add-card-btn');
    const nfcReadBtn = document.getElementById('nfc-read');
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

    // Handle HID-like keyboard input from card reader (10-digit number)
    let buffer = '';
    let timeout = null;
    document.addEventListener('keydown', (e) => {
        if (e.key >= '0' && e.key <= '9') {
            e.preventDefault(); // Prevent default to avoid typing in other places
            buffer += e.key;
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => { buffer = ''; }, 500); // Reset buffer after 500ms inactivity (adjust as needed)

            if (buffer.length === 10) {
                hideError();
                nfcIdInput.value = buffer;
                cardDisplay.textContent = `Scanned Card ID: ${buffer}`;
                cardDisplay.classList.remove('hidden');
                addCardBtn.disabled = false;
                addCardBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                buffer = '';
                clearTimeout(timeout);
            }
        } else {
            buffer = ''; // Reset on non-digit key
        }
    });

    // NFC Reader Logic (kept as fallback or for true NFC tags)
    const initNFC = async () => {
        if (!('NDEFReader' in window)) {
            showError('Web NFC is not supported on this device or browser. Please use Chrome on Android.');
            return;
        }
        try {
            const ndef = new NDEFReader();
            await ndef.scan();
            nfcReadBtn.textContent = 'Scanning...';
            nfcReadBtn.disabled = true;
            nfcReadBtn.classList.add('opacity-50', 'cursor-not-allowed');

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
                nfcReadBtn.textContent = 'Start NFC Scan';
                nfcReadBtn.disabled = false;
                nfcReadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            });
        } catch (error) {
            console.error(`Error starting NFC scan: ${error}`);
            if (error.name === 'NotAllowedError') {
                showError('NFC permission denied. Please allow NFC access and try again.');
            } else {
                showError('Could not start NFC scanning. Ensure a secure (HTTPS) connection and try again.');
            }
            nfcReadBtn.textContent = 'Start NFC Scan';
            nfcReadBtn.disabled = false;
            nfcReadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
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
                nfcReadBtn.textContent = 'Start NFC Scan';
                nfcReadBtn.disabled = false;
                nfcReadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                showError(result.message || 'An unknown error occurred.');
                addCardBtn.disabled = false;
                addCardBtn.textContent = 'Add Card';
            }
        } catch (networkError) {
            console.error('Network or submission error:', networkError);
            showError('A network error occurred. Please check your connection and try again.');
            addCardBtn.disabled = false;
            addCardBtn.textContent = 'Add Card';
        }
    });

    // Start NFC scanning when the button is clicked
    if (nfcReadBtn) {
        nfcReadBtn.addEventListener('click', async () => {
            alert('NFC started scanning. Please tap your card.');
            await initNFC();
        });
    } else {
        console.error('NFC read button not found.');
    }
});