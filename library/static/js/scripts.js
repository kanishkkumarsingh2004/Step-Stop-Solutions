// Allocate Cards to Library functionality
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('allocate-form');
    const selectedCardsContainer = document.createElement('div');
    selectedCardsContainer.className = 'mb-6 bg-gray-50 p-4 rounded-lg';
    selectedCardsContainer.innerHTML = '<p class="text-sm font-medium text-gray-700 mb-2">Selected Cards:</p>';
    form.insertBefore(selectedCardsContainer, form.querySelector('.mb-6'));

    function updateSelectedCardsDisplay() {
        const selectedCards = Array.from(document.querySelectorAll('input[name="nfc_serials"]:checked'))
            .map(checkbox => checkbox.value);
        
        const count = selectedCards.length;
        selectedCardsContainer.innerHTML = `
            <p class="text-sm font-medium text-gray-700 mb-2">
                Selected Cards (${count}):
            </p>
            <div class="flex flex-nowrap gap-2 overflow-x-auto pb-2">
                ${selectedCards.map(card => `
                    <span class="bg-green-100 text-green-800 text-sm px-2 py-1 rounded whitespace-nowrap">${card}</span>
                `).join('')}
            </div>
        `;
    }

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const libraryId = document.getElementById('library').value;
            const selectedCards = Array.from(document.querySelectorAll('input[name="nfc_serials"]:checked'))
                .map(checkbox => checkbox.value);

            if (!libraryId || selectedCards.length === 0) {
                alert('Please select a library and at least one card.');
                return;
            }

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        library_id: libraryId,
                        nfc_serials: selectedCards
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    alert('Cards allocated successfully!');
                    window.location.reload();
                } else {
                    throw new Error(data.error || 'Failed to allocate cards');
                }
            } catch (error) {
                alert(error.message);
            }
        });

        // Select All functionality
        const selectAllCheckbox = document.getElementById('select-all');
        const cardCheckboxes = document.querySelectorAll('input[name="nfc_serials"]');
        
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                cardCheckboxes.forEach(checkbox => {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                updateSelectedCardsDisplay();
            });
        }

        // Handle individual card selection
        cardCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Uncheck select-all if any checkbox is unchecked
                if (!this.checked && selectAllCheckbox.checked) {
                    selectAllCheckbox.checked = false;
                }
                updateSelectedCardsDisplay();
            });
        });

        // Handle card tap (assuming NFC scanning functionality)
        if (typeof NDEFReader !== 'undefined') {
            const ndef = new NDEFReader();
            ndef.scan().then(() => {
                ndef.onreading = ({ serialNumber }) => {
                    const correspondingCheckbox = document.querySelector(`input[value="${serialNumber}"]`);
                    if (correspondingCheckbox) {
                        correspondingCheckbox.checked = true;
                        updateSelectedCardsDisplay();
                    }
                };
            }).catch(error => {
                console.error('Error scanning NFC:', error);
            });
        }
    }
});
