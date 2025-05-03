class NFCReader {
    constructor(options = {}) {
        this.nfcSupported = false;
        this.isReading = false;
        this.options = options;
        this.checkNFCSupport();
    }

    checkNFCSupport() {
        this.nfcSupported = 'NDEFReader' in window;
        const message = this.nfcSupported 
            ? 'Web NFC API is supported in this browser.'
            : 'Web NFC API is not supported in this browser.';
        
        console[this.nfcSupported ? 'log' : 'warn'](message);
        this.options.onLog?.(message);
        if (!this.nfcSupported) this.options.onError?.(message);
        
        return this.nfcSupported;
    }

    async startReading() {
        if (!this.nfcSupported) {
            const message = 'NFC is not supported in this browser.';
            console.warn(message);
            this.options.onError?.(message);
            return false;
        }

        if (this.isReading) {
            const message = 'NFC reader is already active.';
            console.warn(message);
            this.options.onLog?.(message);
            return true;
        }

        try {
            this.reader = new NDEFReader();
            await this.reader.scan();
            
            this.reader.addEventListener("reading", ({ serialNumber }) => {
                console.log(`NFC card detected: ${serialNumber}`);
                this.options.onReading?.(serialNumber);
                this.options.onLog?.(`NFC card detected: ${serialNumber}`);
            });
            
            this.reader.addEventListener("readingerror", (error) => {
                console.error(`Error reading NFC card: ${error}`);
                this.options.onError?.(error.message || 'Error reading NFC card');
                this.options.onLog?.(`Error reading NFC card: ${error.message}`);
            });
            
            this.isReading = true;
            this.options.onLog?.('NFC reader started. Waiting for card...');
            return true;
        } catch (error) {
            console.error(`Error starting NFC reader: ${error}`);
            this.options.onError?.(error.message || 'Error starting NFC reader');
            this.options.onLog?.(`Error starting NFC reader: ${error.message}`);
            return false;
        }
    }

    stopReading() {
        this.isReading = false;
        console.log('NFC reader stopped.');
        this.options.onLog?.('NFC reader stopped.');
    }
}

// Initialize NFC reader when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('nfc-error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const scanButton = document.getElementById('nfc-scan-button');
    const nfcDetails = document.getElementById('nfc-details');
    const logContainer = document.getElementById('nfc-log');
    const activationStatus = document.getElementById('activation-status');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const userSelect = document.getElementById('user-select');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Function to add log messages
    const addLogMessage = (message) => {
        if (!logContainer) return;
        const logEntry = document.createElement('p');
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

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

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.allocated) {
                // Update UI to show allocated user info
                const userInfo = document.createElement('div');
                userInfo.innerHTML = `
                    <p class="text-sm text-gray-600 mt-2">Allocated to:</p>
                    <p class="text-lg font-semibold">${data.user_full_name}</p>
                    <p class="text-sm text-gray-600">${data.user_mobile}</p>
                `;
                
                // Clear previous info and add new
                const infoContainer = document.getElementById('nfc-user-info');
                if (infoContainer) {
                    infoContainer.innerHTML = '';
                    infoContainer.appendChild(userInfo);
                }
                
                // Show deallocate button
                deleteButton?.classList.remove('hidden');
                activateButton?.classList.add('hidden');
            } else {
                // Clear user info if not allocated
                const infoContainer = document.getElementById('nfc-user-info');
                if (infoContainer) infoContainer.innerHTML = '';
                
                // Show activate button
                activateButton?.classList.remove('hidden');
                deleteButton?.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error checking NFC allocation:', error);
            // Show error message to user
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error.message || 'Error checking NFC allocation. Please try again.';
            }
            // Hide card details if there's an error
            if (nfcDetails) {
                nfcDetails.classList.add('hidden');
            }
            if (nfcIdDisplay) {
                nfcIdDisplay.textContent = 'Waiting for card...';
            }
        }
    }

    // Create NFC reader instance with enhanced error handling and UI updates
    const nfcReader = new NFCReader({
        onReading: (serialNumber) => {
            if (nfcIdDisplay) {
                nfcIdDisplay.textContent = serialNumber;
                checkNfcAllocation(serialNumber);   
                if (nfcDetails) {
                    nfcDetails.classList.remove('hidden');
                }
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
            if (nfcDetails) {
                nfcDetails.classList.add('hidden');
            }
        },
        onLog: addLogMessage
    });

    // Start scanning when the button is clicked
    if (scanButton) {
        scanButton.addEventListener('click', async () => {
            const started = await nfcReader.startReading();
            if (started) {
                scanButton.textContent = 'Scanning Active';
                scanButton.disabled = true;
                scanButton.classList.replace('bg-blue-600', 'bg-green-600');
                if (activationStatus) {
                    activationStatus.textContent = 'Scanning for NFC card...';
                }
            }
        });
    }

    // Check NFC support on page load
    if (!nfcReader.nfcSupported) {
        if (scanButton) {
            scanButton.disabled = true;
            scanButton.textContent = 'NFC Not Supported';
            scanButton.classList.replace('bg-blue-600', 'bg-gray-600');
        }
        if (activationStatus) {
            activationStatus.textContent = 'NFC Not Supported';
        }
    } else {
        if (activationStatus) {
            activationStatus.textContent = 'Ready to Scan';
        }
    }

    // Add click handler for delete button
    deleteButton.addEventListener('click', async () => {
        // Disable button and change text
        deleteButton.textContent = 'Delocating...';
        deleteButton.disabled = true;
        deleteButton.classList.remove('bg-red-600', 'hover:bg-red-700');
        deleteButton.classList.add('bg-gray-600');

        const nfcSerial = nfcIdDisplay.textContent.trim();
        
        try {
            const response = await fetch('/deallocate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: nfcSerial })
            });

            const data = await response.json();
            if (response.ok) {
                // Reset UI
                nfcIdDisplay.textContent = 'Waiting for card...';
                deleteButton.classList.add('hidden');
                activateButton.classList.remove('hidden');
            } else {
                throw new Error(data.error || 'Failed to deallocate user');
            }
        } catch (error) {
            console.error('Error:', error);
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error.message;
            }
        } finally {
            // Re-enable button
            deleteButton.textContent = 'Deallocate User';
            deleteButton.disabled = false;
            deleteButton.classList.remove('bg-gray-600');
            deleteButton.classList.add('bg-red-600', 'hover:bg-red-700');
        }
    });

    if (activateButton && userSelect) {
        activateButton.addEventListener('click', async () => {
            // Disable button and change text
            activateButton.textContent = 'Allocating...';
            activateButton.disabled = true;
            activateButton.classList.remove('bg-green-600', 'hover:bg-green-700');
            activateButton.classList.add('bg-gray-600');

            const nfcSerial = nfcIdDisplay?.textContent?.trim() || '';
            const userId = userSelect.value.trim();
    
            if (nfcSerial === 'Waiting for card...' || !nfcSerial) {
                addLogMessage('Please scan an NFC card first');
                // Re-enable button
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
    
            if (!userId) {
                addLogMessage('Please select a user');
                // Re-enable button
                activateButton.textContent = 'Activate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
    
            if (!csrfToken) {
                addLogMessage('CSRF token not found. Please refresh the page and try again.');
                // Re-enable button
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
});