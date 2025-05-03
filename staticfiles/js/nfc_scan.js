document.addEventListener('DOMContentLoaded', function() {
    const nfcForm = document.getElementById('nfc-form');
    const nfcInput = document.getElementById('nfc_id');
    const cardDisplay = document.getElementById('card-display');
    const addCardBtn = document.getElementById('add-card-btn');
    const errorMessage = document.getElementById('error-message');

    // Check if browser supports Web NFC API
    if (!('NDEFReader' in window)) {
        errorMessage.textContent = 'NFC is not supported in this browser. Please use Chrome on Android.';
        errorMessage.classList.remove('hidden');
        return;
    }

    const nfcReader = new NDEFReader();

    async function startNFCScan() {
        try {
            // Check if NFC is available
            if (!nfcReader) {
                throw new Error('NFC reader not initialized');
            }

            // Request NFC permissions
            const permissionStatus = await navigator.permissions.query({ name: 'nfc' });
            if (permissionStatus.state === 'denied') {
                throw new Error('NFC permission denied. Please enable NFC in your device settings.');
            }

            await nfcReader.scan();
            console.log('NFC scan started successfully');
        } catch (error) {
            console.error('Error starting NFC scan:', error);
            errorMessage.textContent = error.message || 'Error starting NFC scan. Please ensure NFC is enabled and try again.';
            errorMessage.classList.remove('hidden');
            
            // Disable the Add Card button
            addCardBtn.disabled = true;
            addCardBtn.classList.add('opacity-50');
            addCardBtn.classList.remove('hover:bg-blue-700');
        }
    }

    nfcReader.onreading = (event) => {
        const decoder = new TextDecoder();
        const serialNumber = event.serialNumber;
        
        // Display the card number
        cardDisplay.textContent = `Card Number: ${serialNumber}`;
        cardDisplay.classList.remove('hidden');
        
        // Enable the Add Card button
        addCardBtn.disabled = false;
        addCardBtn.classList.remove('opacity-50');
        addCardBtn.classList.add('hover:bg-blue-700');
        
        // Set the NFC ID in the form
        nfcInput.value = serialNumber;
    };

    nfcReader.onreadingerror = (error) => {
        console.error('Error reading NFC card:', error);
        errorMessage.textContent = 'Error reading NFC card. Please try again.';
        errorMessage.classList.remove('hidden');
    };

    // Start NFC scan when page loads
    startNFCScan();

    // Handle form submission
    nfcForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        addCardBtn.disabled = true;
        addCardBtn.textContent = 'Adding...';
        
        try {
            const response = await fetch(nfcForm.action, {
                method: 'POST',
                body: new FormData(nfcForm),
                headers: {
                    'X-CSRFToken': nfcForm.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();
            
            if (response.ok) {
                window.location.reload();
            } else {
                throw new Error(data.error || 'Failed to add card');
            }
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = error.message;
            errorMessage.classList.remove('hidden');
            addCardBtn.disabled = false;
            addCardBtn.textContent = 'Add Card';
        }
    });
}); 