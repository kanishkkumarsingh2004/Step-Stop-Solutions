document.addEventListener("DOMContentLoaded", async () => {
    const attendanceForm = document.getElementById("attendance-form");
    const nfcIdInput = document.getElementById("nfc_id");
    const attendanceStatus = document.getElementById("attendance-status");
    const nfcError = document.getElementById("nfc-error");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const libraryId = document.getElementById('library_id').value;

    // Function to remove message after 3 seconds
    const removeMessageAfterDelay = (element) => {
        setTimeout(() => {
            element.classList.add("hidden");
            element.textContent = "";
        }, 3000);
    };

    // Show error message
    const showError = (message) => {
        const errorContainer = document.getElementById('nfc-error');
        const errorMessage = document.getElementById('error-message');
        
        errorMessage.textContent = message;
        errorContainer.classList.remove('hidden');
        
        setTimeout(() => {
            errorContainer.classList.add('hidden');
            errorMessage.textContent = '';
        }, 5000);
    };

    // Show attendance status with name, time, and welcome/thank you message
    const showStatus = (message, isSuccess = true) => {
        const statusElement = document.createElement("div");
        statusElement.className = `p-4 mb-4 rounded-lg ${
            isSuccess ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
        }`;
        statusElement.innerHTML = message;
        attendanceStatus.appendChild(statusElement);
        attendanceStatus.classList.remove("hidden");
        setTimeout(() => {
            statusElement.remove();
            if (!attendanceStatus.children.length) {
                attendanceStatus.classList.add("hidden");
            }
        }, 3000);
    };

    // Helper to safely parse JSON, fallback to error if not JSON
    const safeParseJSON = async (response) => {
        const text = await response.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            // If the response starts with '<', it's likely HTML (e.g., error page)
            if (text.trim().startsWith('<')) {
                throw new Error("Server returned an unexpected response. Please try again or contact support.");
            }
            throw new Error("Error processing server response.");
        }
    };

    // Start NFC scan
    if ("NDEFReader" in window) {
        try {
            const ndef = new NDEFReader();
            await ndef.scan();
            
            ndef.onreading = async ({ serialNumber }) => {
                nfcIdInput.value = serialNumber;
                
                try {
                    const response = await fetch("/library/mark-attendance/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken
                        },
                        body: JSON.stringify({
                            nfc_serial: serialNumber,
                            library_id: libraryId
                        })
                    });

                    let data;
                    if (!response.ok) {
                        // Try to parse error JSON, but handle HTML error pages
                        try {
                            data = await safeParseJSON(response);
                            throw new Error(data.error || "Error processing attendance");
                        } catch (err) {
                            throw err;
                        }
                    } else {
                        // Try to parse success JSON, but handle HTML error pages
                        try {
                            data = await safeParseJSON(response);
                        } catch (err) {
                            throw err;
                        }
                    }
                    
                    if (data.action === 'checkin') {
                        showStatus(`
                            <p class="text-xl font-bold">Welcome!</p>
                            <p>${data.message}</p>
                            <p class="text-sm text-gray-600">Date: ${data.date}</p>
                            <p class="text-sm text-gray-600">Time: ${data.time}</p>
                        `);
                    } else if (data.action === 'checkout') {
                        showStatus(`
                            <p class="text-xl font-bold">Thank you!</p>
                            <p>${data.message}</p>
                            <p class="text-sm text-gray-600">Date: ${data.date}</p>
                            <p class="text-sm text-gray-600">Time: ${data.time}</p>
                        `);
                    }
                } catch (error) {
                    showError(error.message);
                }
            };
        } catch (error) {
            showError("NFC scan failed. Make sure you're using Chrome on Android with NFC enabled.");
        }
    } else {
        showError("Your browser doesn't support Web NFC. Try Chrome on Android.");
    }
});
