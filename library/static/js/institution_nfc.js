document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    const form = document.getElementById('nfc-form');
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('nfc-error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const invalidCardMessage = document.getElementById('invalid-card-message');
    const allocatedUserInfo = document.getElementById('allocated-user-info');
    const allocatedUserName = document.getElementById('allocated-user-name');
    const userInfoContainer = document.getElementById('nfc-user-info');
    const userSelect = document.getElementById('user-select');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const nfcIdInput = document.getElementById('nfc_id');
    const institutionId = document.getElementById('institution_id').value;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const deallocateModal = document.getElementById('deallocate-modal');
    const cancelDeallocate = document.getElementById('cancel-deallocate');
    const confirmDeallocate = document.getElementById('confirm-deallocate');



    // Helper functions for UI updates
    const showError = (message) => {
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.remove('hidden');
            errorMessageText.textContent = message;
        }
    };
    const hideError = () => {
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.add('hidden');
            errorMessageText.textContent = '';
        }
    };
    const showInvalidCardMessage = () => {
        if (invalidCardMessage) {
            invalidCardMessage.classList.remove('hidden');
        }
    };
    const hideInvalidCardMessage = () => {
        if (invalidCardMessage) {
            invalidCardMessage.classList.add('hidden');
        }
    };

    // Handle keyboard-based NFC input (10-digit number)
    let buffer = '';
    let timeout = null;
    document.addEventListener('keydown', (e) => {
        document.body.focus(); // Ensure focus for NFC reader input
        if (e.key >= '0' && e.key <= '9') {
            e.preventDefault(); // Prevent default to avoid typing in other places
            buffer += e.key;
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                buffer = '';
            }, 1000); // 1000ms timeout for reliability
            if (buffer.length === 10) {
                processCardId(buffer);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            if (buffer.length === 10) {
                processCardId(buffer);
            } else if (buffer.length > 0) {
                showError(`Invalid card ID length: ${buffer.length} digits`);
                buffer = '';
                clearTimeout(timeout);
            }
        } else {
            buffer = '';
            clearTimeout(timeout);
        }
    });

    // Process card ID and check allocation
    const processCardId = async (serialNumber) => {
        serialNumber = serialNumber.trim(); // Normalize input
        nfcIdInput.value = serialNumber; // Store in hidden input
        nfcIdDisplay.textContent = serialNumber;
        await checkNfcAllocation(serialNumber);
        buffer = '';
        clearTimeout(timeout);
    };

    // Check NFC allocation (institution workflow)
    async function checkNfcAllocation(serialNumber) {
        try {
            const response = await fetch('/check_institution_nfc_allocation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: serialNumber, institution_id: institutionId })
            });
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
            }
            const data = await response.json();
            hideError();
            hideInvalidCardMessage();
            if (data.allocated) {
                allocatedUserInfo.classList.remove('hidden');
                allocatedUserName.textContent = data.user_full_name;
                userInfoContainer.innerHTML = `
                    <p class="text-sm text-gray-600 mt-2">Allocated to:</p>
                    <p class="text-lg font-semibold">${data.user_full_name}</p>
                    <p class="text-sm text-gray-600">${data.user_mobile}</p>
                `;
                deleteButton.classList.remove('hidden');
                activateButton.classList.add('hidden');
            } else {
                if (data.error) {
                    showError(data.error);
                    if (data.error.includes('Invalid')) {
                        showInvalidCardMessage();
                    }
                    nfcIdDisplay.textContent = 'Waiting for card...';
                    nfcIdInput.value = '';
                    userInfoContainer.innerHTML = '';
                    return;
                }
                allocatedUserInfo.classList.add('hidden');
                userInfoContainer.innerHTML = '';
                activateButton.classList.remove('hidden');
                deleteButton.classList.add('hidden');
            }
        } catch (error) {
            showError(error.message || 'Error checking NFC allocation. Please try again.');
            nfcIdDisplay.textContent = 'Waiting for card...';
            nfcIdInput.value = '';
            userInfoContainer.innerHTML = '';
            hideInvalidCardMessage();
        }
    }

    // Form submission handler for allocation
    if (form && activateButton && userSelect) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nfcSerial = nfcIdInput.value.trim();
            const userId = userSelect.value.trim();
            if (!nfcSerial || nfcIdDisplay.textContent === 'Waiting for card...') {
                showError('Please scan an NFC card first.');
                return;
            }
            if (!userId) {
                showError('Please select a user.');
                return;
            }
            activateButton.textContent = 'Allocating...';
            activateButton.disabled = true;
            activateButton.classList.remove('bg-green-600', 'hover:bg-green-700');
            activateButton.classList.add('bg-gray-600');
            try {
                const response = await fetch('/allocate_institution_card/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        nfc_serial: nfcSerial,
                        user_id: userId,
                        institution_id: institutionId
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    hideError();
                    window.location.reload();
                } else {
                    showError(data.error || 'Failed to allocate user');
                }
            } catch (error) {
                showError('An error occurred while allocating the user');
            } finally {
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
            }
        });

        // Trigger form submission on activate button click
        activateButton.addEventListener('click', () => {
            form.dispatchEvent(new Event('submit'));
        });
    }

    // Deallocate user
    if (deleteButton) {
        deleteButton.addEventListener('click', () => {
            deallocateModal.classList.remove('hidden');
        });
    }
    if (cancelDeallocate) {
        cancelDeallocate.addEventListener('click', () => {
            deallocateModal.classList.add('hidden');
        });
    }
    if (confirmDeallocate) {
        confirmDeallocate.addEventListener('click', async () => {
            confirmDeallocate.textContent = 'Deallocating...';
            confirmDeallocate.disabled = true;
            confirmDeallocate.classList.remove('bg-red-600', 'hover:bg-red-700');
            confirmDeallocate.classList.add('bg-gray-600');
            const nfcSerial = nfcIdInput.value.trim();
            try {
                const response = await fetch('/deallocate-institution-nfc/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ nfc_serial: nfcSerial })
                });
                const data = await response.json();
                if (response.ok) {
                    deallocateModal.classList.add('hidden');
                    nfcIdDisplay.textContent = 'Waiting for card...';
                    nfcIdInput.value = '';
                    deleteButton.classList.add('hidden');
                    activateButton.classList.remove('hidden');
                    userInfoContainer.innerHTML = '';
                    allocatedUserInfo.classList.add('hidden');
                    hideError();
                } else {
                    showError(data.error || 'Failed to deallocate user');
                }
            } catch (error) {
                showError(error.message || 'An error occurred while deallocating the NFC ID');
            } finally {
                confirmDeallocate.textContent = 'Deallocate';
                confirmDeallocate.disabled = false;
                confirmDeallocate.classList.remove('bg-gray-600');
                confirmDeallocate.classList.add('bg-red-600', 'hover:bg-red-700');
            }
        });
    }
});