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
        
        if (!this.nfcSupported) this.options.onError?.(message);
        
        return this.nfcSupported;
    }

    async startReading() {
        if (!this.nfcSupported) {
            const message = 'NFC is not supported in this browser.';
            this.options.onError?.(message);
            return false;
        }

        if (this.isReading) {
            const message = 'NFC reader is already active.';
            return true;
        }

        try {
            this.reader = new NDEFReader();
            await this.reader.scan();
            
            this.reader.addEventListener("reading", ({ serialNumber }) => {
                this.options.onReading?.(serialNumber);
            });
            
            this.reader.addEventListener("readingerror", (error) => {
                this.options.onError?.(error.message || 'Error reading NFC card');
            });
            
            this.isReading = true;
            return true;
        } catch (error) {
            this.options.onError?.(error.message || 'Error starting NFC reader');
            return false;
        }
    }

    stopReading() {
        this.isReading = false;
    }
}

// Initialize NFC reader when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('nfc-error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const scanButton = document.getElementById('nfc-scan-button');
    const nfcDetails = document.getElementById('nfc-details');
    const activationStatus = document.getElementById('activation-status');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const userSelect = document.getElementById('user-select');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const libraryId = document.getElementById('library_id').value;
    const userInfo = document.createElement('div');

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

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
            }

            const data = await response.json();

            if (data.allocated) {
                nfcIdDisplay.textContent = nfcSerial;
                if (nfcDetails) {
                    nfcDetails.classList.remove('hidden');
                }
                nfcIdDisplay.textContent = serialNumber;
                userInfo.innerHTML = `
                    <p class="text-sm text-gray-600 mt-2">Allocated to:</p>
                    <p class="text-lg font-semibold">${data.user_full_name}</p>
                    <p class="text-sm text-gray-600">${data.user_mobile}</p>
                `;
                
                const infoContainer = document.getElementById('nfc-user-info');
                if (infoContainer) {
                    infoContainer.innerHTML = '';
                    infoContainer.appendChild(userInfo);
                }
                
                deleteButton?.classList.remove('hidden');
                activateButton?.classList.add('hidden');
            } else {
                if (data.error) {
                    throw new Error(data.error);
                }
                else {
                    const infoContainer = document.getElementById('nfc-user-info');
                    if (infoContainer) infoContainer.innerHTML = '';
                    if (nfcDetails) {
                        nfcDetails.classList.remove('hidden');
                    }
                    nfcIdDisplay.textContent = serialNumber;
                    activateButton?.classList.remove('hidden');
                    deleteButton?.classList.add('hidden');
                }
            }            
        } catch (error) {
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error.message || 'Error checking NFC allocation. Please try again.';
            }
            if (nfcDetails) {
                nfcDetails.classList.add('hidden');
            }
            if (nfcIdDisplay) {
                nfcIdDisplay.textContent = 'Waiting for card...';
            }
        }
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
            if (nfcDetails) {
                nfcDetails.classList.add('hidden');
            }
        }
    });

    // Start scanning automatically when window loads
    window.addEventListener('load', async () => {
        const started = await nfcReader.startReading();
        if (started && activationStatus) {
            activationStatus.textContent = 'Scanning for NFC card...';
        }
    });

    if (!nfcReader.nfcSupported) {
        if (activationStatus) {
            activationStatus.textContent = 'NFC Not Supported';
        }
    } else {
        if (activationStatus) {
            activationStatus.textContent = 'Ready to Scan';
        }
    }

    deleteButton.addEventListener('click', async () => {
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
                nfcIdDisplay.textContent = 'Waiting for card...';
                deleteButton.classList.add('hidden');
                activateButton.classList.remove('hidden');
            } else {
                throw new Error(data.error || 'Failed to deallocate user');
            }
        } catch (error) {
            if (errorMessageContainer && errorMessageText) {
                errorMessageContainer.classList.remove('hidden');
                errorMessageText.textContent = error.message;
            }
        } finally {
            deleteButton.textContent = 'Deallocate User';
            deleteButton.disabled = false;
            deleteButton.classList.remove('bg-gray-600');
            deleteButton.classList.add('bg-red-600', 'hover:bg-red-700');
        }
    });

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
});