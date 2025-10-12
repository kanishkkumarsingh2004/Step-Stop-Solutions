document.addEventListener('DOMContentLoaded', () => {
    console.log('Script loaded: gym_nfc.js'); // Debug: Script initialization

    // Get DOM elements
    const form = document.getElementById('nfc-form');
    const nfcIdDisplay = document.getElementById('nfc-id-display');
    const errorMessageContainer = document.getElementById('error-message');
    const errorMessageText = errorMessageContainer?.querySelector('p');
    const invalidCardMessage = document.getElementById('invalid-card-message');
    const allocatedUserInfo = document.getElementById('allocated-user-info');
    const allocatedUserName = document.getElementById('allocated-user-name');
    const userInfoContainer = document.getElementById('nfc-user-info');
    const userSelect = document.getElementById('user-select');
    const activateButton = document.getElementById('activate-user-button');
    const deleteButton = document.getElementById('delete-user-button');
    const nfcIdInput = document.getElementById('nfc_id');
    const gymId = document.getElementById('gym_id').value;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const deallocateModal = document.getElementById('deallocate-modal');
    const cancelDeallocate = document.getElementById('cancel-deallocate');
    const confirmDeallocate = document.getElementById('confirm-deallocate');

    console.log('DOM elements initialized:', {
        form: !!form,
        nfcIdDisplay: !!nfcIdDisplay,
        errorMessageContainer: !!errorMessageContainer,
        invalidCardMessage: !!invalidCardMessage,
        allocatedUserInfo: !!allocatedUserInfo,
        userSelect: !!userSelect,
        activateButton: !!activateButton,
        deleteButton: !!deleteButton,
        nfcIdInput: !!nfcIdInput,
        gymId: gymId,
        csrfToken: !!csrfToken,
        deallocateModal: !!deallocateModal
    }); // Debug: Element availability

    // Helper functions for UI updates
    const showError = (message) => {
        console.log('Showing error:', message); // Debug
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.remove('hidden');
            errorMessageText.textContent = message;
        }
    };
    const hideError = () => {
        console.log('Hiding error'); // Debug
        if (errorMessageContainer && errorMessageText) {
            errorMessageContainer.classList.add('hidden');
            errorMessageText.textContent = '';
        }
    };
    const showInvalidCardMessage = () => {
        console.log('Showing invalid card message'); // Debug
        if (invalidCardMessage) {
            invalidCardMessage.classList.remove('hidden');
        }
    };
    const hideInvalidCardMessage = () => {
        console.log('Hiding invalid card message'); // Debug
        if (invalidCardMessage) {
            invalidCardMessage.classList.add('hidden');
        }
    };

    // Handle keyboard-based NFC input (10-digit number)
    let buffer = '';
    let timeout = null;
    document.addEventListener('keydown', (e) => {
        console.log(`Key pressed: ${e.key}, Document has focus: ${document.hasFocus()}`); // Debug
        document.body.focus(); // Ensure focus for NFC reader input
        if (e.key >= '0' && e.key <= '9') {
            e.preventDefault(); // Prevent default to avoid typing in other places
            buffer += e.key;
            console.log(`Buffer updated: ${buffer}`); // Debug
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                console.log('Buffer reset due to timeout');
                buffer = '';
            }, 1000); // 1000ms timeout for reliability
            if (buffer.length === 10) {
                console.log('10 digits reached, processing card ID'); // Debug
                processCardId(buffer);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            console.log(`Enter key pressed, buffer: ${buffer}`); // Debug
            if (buffer.length === 10) {
                console.log('Enter with 10 digits, processing card ID'); // Debug
                processCardId(buffer);
            } else if (buffer.length > 0) {
                showError(`Invalid card ID length: ${buffer.length} digits`);
                console.log(`Invalid buffer length: ${buffer.length}`); // Debug
                buffer = '';
                clearTimeout(timeout);
            }
        } else {
            console.log(`Non-digit key pressed, resetting buffer: ${e.key}`); // Debug
            buffer = '';
            clearTimeout(timeout);
        }
    });

    // Process card ID and check allocation
    const processCardId = async (serialNumber) => {
        serialNumber = serialNumber.trim(); // Normalize input
        console.log(`Processing serial number: ${serialNumber}`); // Debug
        nfcIdInput.value = serialNumber; // Store in hidden input
        console.log(`nfc_id input updated: ${nfcIdInput.value}`); // Debug
        nfcIdDisplay.textContent = serialNumber;
        console.log(`nfc-id-display updated: ${nfcIdDisplay.textContent}`); // Debug
        await checkNfcAllocation(serialNumber);
        buffer = '';
        clearTimeout(timeout);
    };

    // Check NFC allocation (gym workflow)
    async function checkNfcAllocation(serialNumber) {
        try {
            console.log(`Checking allocation for serial number: ${serialNumber}`); // Debug
            const response = await fetch('/gym/check_gym_nfc_allocation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ nfc_serial: serialNumber, gym_id: gymId })
            });
            console.log('checkNfcAllocation fetch sent'); // Debug
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
            }
            const data = await response.json();
            console.log('Allocation response:', data); // Debug
            hideError();
            hideInvalidCardMessage();
            if (data.allocated) {
                console.log('Card is allocated, updating UI'); // Debug
                allocatedUserInfo.classList.remove('hidden');
                allocatedUserName.textContent = data.user_full_name;
                userInfoContainer.innerHTML = `
                    <p class="text-sm text-gray-600 mt-2">Allocated to:</p>
                    <p class="text-lg font-semibold">${data.user_full_name}</p>
                    <p class="text-sm text-gray-600">${data.user_mobile}</p>
                `;
                deleteButton.classList.remove('hidden');
                activateButton.classList.add('hidden');
                console.log('UI updated for allocated card:', {
                    allocatedUserName: allocatedUserName.textContent,
                    deleteButtonVisible: !deleteButton.classList.contains('hidden'),
                    activateButtonHidden: activateButton.classList.contains('hidden')
                }); // Debug
            } else {
                if (data.error) {
                    console.log('Allocation error:', data.error); // Debug
                    showError(data.error);
                    if (data.error.includes('Invalid')) {
                        showInvalidCardMessage();
                    }
                    nfcIdDisplay.textContent = 'Waiting for card...';
                    nfcIdInput.value = '';
                    userInfoContainer.innerHTML = '';
                    console.log('UI reset for invalid card'); // Debug
                    return;
                }
                console.log('Card is unallocated, updating UI'); // Debug
                allocatedUserInfo.classList.add('hidden');
                userInfoContainer.innerHTML = '';
                activateButton.classList.remove('hidden');
                deleteButton.classList.add('hidden');
                console.log('UI updated for unallocated card:', {
                    activateButtonVisible: !activateButton.classList.contains('hidden'),
                    deleteButtonHidden: deleteButton.classList.contains('hidden')
                }); // Debug
            }
        } catch (error) {
            console.error('Error checking NFC allocation:', error); // Debug
            showError(error.message || 'Error checking NFC allocation. Please try again.');
            nfcIdDisplay.textContent = 'Waiting for card...';
            nfcIdInput.value = '';
            userInfoContainer.innerHTML = '';
            hideInvalidCardMessage();
            console.log('UI reset due to allocation error'); // Debug
        }
    }

    // Form submission handler for allocation
    if (form && activateButton && userSelect) {
        console.log('Setting up form submission for allocation'); // Debug
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('Form submission triggered'); // Debug
            const nfcSerial = nfcIdInput.value.trim();
            const userId = userSelect.value.trim();
            console.log('Form data:', { nfcSerial, userId, gymId }); // Debug
            if (!nfcSerial || nfcIdDisplay.textContent === 'Waiting for card...') {
                showError('Please scan an NFC card first.');
                console.log('Form submission failed: No NFC card scanned'); // Debug
                return;
            }
            if (!userId) {
                showError('Please select a user.');
                console.log('Form submission failed: No user selected'); // Debug
                return;
            }
            activateButton.textContent = 'Allocating...';
            activateButton.disabled = true;
            activateButton.classList.remove('bg-green-600', 'hover:bg-green-700');
            activateButton.classList.add('bg-gray-600');
            console.log('Allocation started, button disabled'); // Debug
            try {
                const response = await fetch('/gym/allocate_gym_card/', {
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
                console.log('Allocation fetch sent'); // Debug
                const data = await response.json();
                console.log('Allocation response:', data); // Debug
                if (response.ok) {
                    hideError();
                    console.log('Allocation successful, reloading page'); // Debug
                    window.location.reload();
                } else {
                    showError(data.error || 'Failed to allocate user');
                    console.log('Allocation failed:', data.error); // Debug
                }
            } catch (error) {
                console.error('Error allocating user:', error); // Debug
                showError('An error occurred while allocating the user');
            } finally {
                activateButton.textContent = 'Allocate User';
                activateButton.disabled = false;
                activateButton.classList.remove('bg-gray-600');
                activateButton.classList.add('bg-green-600', 'hover:bg-green-700');
                console.log('Allocation button reset'); // Debug
            }
        });

        // Trigger form submission on activate button click
        activateButton.addEventListener('click', () => {
            console.log('Activate button clicked, triggering form submission'); // Debug
            form.dispatchEvent(new Event('submit'));
        });
    }

    // Deallocate user
    if (deleteButton) {
        deleteButton.addEventListener('click', () => {
            console.log('Delete button clicked, showing deallocate modal'); // Debug
            deallocateModal.classList.remove('hidden');
        });
    }
    if (cancelDeallocate) {
        cancelDeallocate.addEventListener('click', () => {
            console.log('Cancel deallocate clicked, hiding modal'); // Debug
            deallocateModal.classList.add('hidden');
        });
    }
    if (confirmDeallocate) {
        confirmDeallocate.addEventListener('click', async () => {
            console.log('Confirm deallocate clicked'); // Debug
            confirmDeallocate.textContent = 'Deallocating...';
            confirmDeallocate.disabled = true;
            confirmDeallocate.classList.remove('bg-red-600', 'hover:bg-red-700');
            confirmDeallocate.classList.add('bg-gray-600');
            const nfcSerial = nfcIdInput.value.trim();
            console.log(`Deallocating NFC serial: ${nfcSerial}`); // Debug
            try {
                const response = await fetch('/gym/deallocate-nfc/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ nfc_serial: nfcSerial })
                });
                console.log('Deallocation fetch sent'); // Debug
                const data = await response.json();
                console.log('Deallocation response:', data); // Debug
                if (response.ok) {
                    deallocateModal.classList.add('hidden');
                    nfcIdDisplay.textContent = 'Waiting for card...';
                    nfcIdInput.value = '';
                    deleteButton.classList.add('hidden');
                    activateButton.classList.remove('hidden');
                    userInfoContainer.innerHTML = '';
                    allocatedUserInfo.classList.add('hidden');
                    hideError();
                    console.log('Deallocation successful, UI reset'); // Debug
                } else {
                    showError(data.error || 'Failed to deallocate user');
                    console.log('Deallocation failed:', data.error); // Debug
                }
            } catch (error) {
                console.error('Error deallocating NFC ID:', error); // Debug
                showError(error.message || 'An error occurred while deallocating the NFC ID');
            } finally {
                confirmDeallocate.textContent = 'Deallocate';
                confirmDeallocate.disabled = false;
                confirmDeallocate.classList.remove('bg-gray-600');
                confirmDeallocate.classList.add('bg-red-600', 'hover:bg-red-700');
                console.log('Deallocate button reset'); // Debug
            }
        });
    }
});
