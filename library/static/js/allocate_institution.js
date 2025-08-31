document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const form = document.getElementById('allocate-form');
    const selectAllCheckbox = document.getElementById('select-all');
    const cardCheckboxes = document.querySelectorAll('.card-checkbox');
    const selectedCardsContainer = document.getElementById('selected-cards-container');
    const selectedCardsList = document.getElementById('selected-cards-list');
    const selectedCount = document.getElementById('selected-count');
    const errorMessageDiv = document.getElementById('error-message');
    const institutionSelect = document.getElementById('institution');
    const nfcIdInput = document.getElementById('nfc_id');
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
    const updateSelectedCardsDisplay = () => {
        const selectedCards = Array.from(cardCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        const count = selectedCards.length;
        selectedCount.textContent = count;
        selectedCardsList.innerHTML = selectedCards.map(card => `
            <span class="bg-green-100 text-green-800 text-sm px-2 py-1 rounded whitespace-nowrap">${card}</span>
        `).join('');
        selectedCardsContainer.classList.toggle('hidden', count === 0);
    };

    // Handle keyboard-based NFC input (10-digit number)
    let buffer = '';
    let timeout = null;
    document.addEventListener('keydown', (e) => {
        console.log(`Key pressed: ${e.key}`); // Debug: Log each key press
        if (e.key >= '0' && e.key <= '9') {
            e.preventDefault(); // Prevent default to avoid typing in other places
            buffer += e.key;
            console.log(`Buffer: ${buffer}`); // Debug: Log current buffer
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                console.log('Buffer reset due to timeout');
                buffer = '';
            }, 500); // Reset buffer after 500ms inactivity
        } else if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            console.log(`Enter key pressed, buffer: ${buffer}`); // Debug
            if (buffer.length === 10) {
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

    // Process card ID and check matching checkbox
    const processCardId = (cardId) => {
        cardId = cardId.trim(); // Normalize input
        console.log(`Processing card ID: ${cardId}`); // Debug
        hideError();
        nfcIdInput.value = cardId; // Store in hidden input (optional)
        const correspondingCheckbox = Array.from(cardCheckboxes).find(checkbox => 
            checkbox.value.trim() === cardId
        );
        if (correspondingCheckbox) {
            correspondingCheckbox.checked = true;
            console.log(`Selected checkbox for card ID: ${cardId}`); // Debug
            updateSelectedCardsDisplay();
            const row = correspondingCheckbox.closest('tr');
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            row.classList.add('bg-yellow-100');
            setTimeout(() => {
                row.classList.remove('bg-yellow-100');
            }, 1000); // Remove highlight after 1 second
        } else {
            showError(`Card ID ${cardId} not found in the list.`);
            console.log(`No checkbox found for card ID: ${cardId}`); // Debug
            console.log('Available card IDs:', Array.from(cardCheckboxes).map(cb => cb.value)); // Debug: Log all card IDs
        }
        buffer = '';
        clearTimeout(timeout);
    };

    // Form submission
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const institutionId = institutionSelect.value;
            const selectedCards = Array.from(cardCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            if (!institutionId) {
                showError('Please select an institution.');
                return;
            }

            if (selectedCards.length === 0) {
                showError('Please select at least one card.');
                return;
            }

            hideError();
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Allocating...';

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        institution_id: institutionId,
                        nfc_serials: selectedCards
                    })
                });

                const data = await response.json();
                if (response.ok && data.status === 'success') {
                    alert(data.message || 'Cards allocated successfully!');
                    window.location.reload();
                } else {
                    throw new Error(data.message || 'Failed to allocate cards');
                }
            } catch (error) {
                console.error('Submission error:', error);
                showError(error.message || 'A network error occurred. Please try again.');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Allocate Selected Cards';
            }
        });

        // Select All functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                cardCheckboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                    const row = checkbox.closest('tr');
                    row.style.backgroundColor = this.checked ? '#E8F0FE' : '';
                });
                updateSelectedCardsDisplay();
            });
        }

        // Handle individual card selection
        cardCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const row = this.closest('tr');
                row.style.backgroundColor = this.checked ? '#E8F0FE' : '';
                if (!this.checked && selectAllCheckbox.checked) {
                    selectAllCheckbox.checked = false;
                }
                updateSelectedCardsDisplay();
            });
        });

        // Handle row click to toggle checkbox
        document.querySelectorAll('.card-row').forEach(row => {
            row.addEventListener('click', function(e) {
                if (e.target.type === 'checkbox') return;
                const checkbox = this.querySelector('.card-checkbox');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        });
    }

    // Initial update of selected cards display
    updateSelectedCardsDisplay();
});