document.addEventListener('DOMContentLoaded', function() {
    const nfcForm = document.getElementById('nfc-form');
    const nfcInput = document.getElementById('nfc_id');
    const cardDisplay = document.getElementById('card-display');
    const addCardBtn = document.getElementById('add-card-btn');
    const errorMessage = document.getElementById('error-message');
    let lastScannedCard = null;

    if (!('NDEFReader' in window)) {
        errorMessage.textContent = 'NFC is not supported in this browser.';
        errorMessage.classList.remove('hidden');
        return;
    }

    const nfcReader = new NDEFReader();

    async function startNFCScan() {
        try {
            await nfcReader.scan();
            console.log('NFC scan started successfully');
        } catch (error) {
            console.error('Error starting NFC scan:', error);
            errorMessage.textContent = 'Error starting NFC scan. Please try again.';
            errorMessage.classList.remove('hidden');
        }
    }

    nfcReader.onreading = (event) => {
        const serialNumber = event.serialNumber;
        
        // Check for duplicate scan
        if (lastScannedCard === serialNumber) {
            errorMessage.textContent = 'This card has already been scanned. Please scan a different card.';
            errorMessage.classList.remove('hidden');
            return;
        }
        
        // Update last scanned card
        lastScannedCard = serialNumber;
        
        // Clear any previous error messages
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
        
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
    });
});