class GymNFCReader {
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

document.addEventListener('DOMContentLoaded', () => {
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('nfc-error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const userSelect = document.getElementById('user-select');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const gymId = document.getElementById('gym_id').value;
    const userInfo = document.createElement('div');

    function showError(message) {
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.remove('hidden');
            errorMessageText.textContent = message;
        }
    }
    function hideError() {
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.add('hidden');
            errorMessageText.textContent = '';
        }
    }

    async function checkNfcAllocation(nfcSerial) {
        try {
            const response = await fetch(`/gyms/${gymId}/check-gym-nfc-allocation/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: nfcSerial, gym_id: gymId })
            });
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
            }
            const data = await response.json();
            hideError();
            if (data.allocated) {
                nfcIdDisplay.textContent = nfcSerial;
                userInfo.innerHTML = `
                    <p class="text-sm text-gray-600 mt-2">Allocated to:</p>
                    <p class="text-lg font-semibold">${data.user_full_name}</p>
                    <p class="text-sm text-gray-600">${data.user_email}</p>
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
                    showError(data.error);
                    if (nfcIdDisplay) nfcIdDisplay.textContent = 'Waiting for card...';
                    return;
                }
                const infoContainer = document.getElementById('nfc-user-info');
                if (infoContainer) infoContainer.innerHTML = '';
                nfcIdDisplay.textContent = nfcSerial;
                activateButton?.classList.remove('hidden');
                deleteButton?.classList.add('hidden');
            }
        } catch (error) {
            showError(error.message || 'Error checking NFC allocation. Please try again.');
            if (nfcIdDisplay) nfcIdDisplay.textContent = 'Waiting for card...';
        }
    }

    const nfcReader = new GymNFCReader({
        onReading: (serialNumber) => {
            if (nfcIdDisplay) {
                checkNfcAllocation(serialNumber);
            }
        },
        onError: (error) => {
            showError(error);
            if (nfcIdDisplay) {
                nfcIdDisplay.textContent = 'Waiting for card...';
            }
        }
    });

    window.addEventListener('load', async () => {
        await nfcReader.startReading();
    });

    deleteButton?.addEventListener('click', async () => {
        deleteButton.textContent = 'Deallocating...';
        deleteButton.disabled = true;
        deleteButton.classList.remove('bg-red-600', 'hover:bg-red-700');
        deleteButton.classList.add('bg-gray-600');
        const nfcSerial = nfcIdDisplay.textContent.trim();
        try {
            const response = await fetch(`/gyms/${gymId}/deallocate-gym-nfc/`, {
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
                hideError();
            } else {
                showError(data.error || 'Failed to deallocate user');
            }
        } catch (error) {
            showError(error.message || 'An error occurred while deallocating the NFC ID');
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
                showError('Please scan an NFC card first.');
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
            if (!userId) {
                showError('Please select a user.');
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
            if (!csrfToken) {
                showError('CSRF token missing.');
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                return;
            }
            try {
                const response = await fetch(`/gyms/${gymId}/allocate-gym-nfc/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        nfc_serial: nfcSerial,
                        user_id: userId,
                        gym_id: gymId
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    hideError();
                    window.location.reload();
                } else {
                    showError(data.error || 'Failed to allocate user');
                    activateButton.textContent = 'Allocate User';
                    activateButton.disabled = false;
                    activateButton.classList.remove('bg-gray-600');
                    activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                }
            } catch (error) {
                showError('An error occurred while allocating the user');
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
            }
        });
    }
}); 