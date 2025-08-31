document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("nfc-form");
    const nfcIdInput = document.getElementById("nfc_id");
    // Note: in coaching_attendance_page.html, the hidden input is "institute_id"
    const instituteId = document.getElementById("institute_id").value;
    const attendanceStatus = document.getElementById("attendance-status");
    const nfcError = document.getElementById("nfc-error");
    const errorMessage = document.getElementById("error-message");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    // --- Utility functions ---
    const showError = (message) => {
        errorMessage.textContent = message;
        nfcError.classList.remove("hidden");
        setTimeout(() => {
            nfcError.classList.add("hidden");
            errorMessage.textContent = "";
        }, 4000);
    };

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

    const isValidSerial = (value) => /^\d{10}$/.test(value);

    // --- Buffer for RFID keyboard input ---
    let buffer = "";
    let timeout = null;
    let isProcessing = false;

    document.addEventListener("keydown", (e) => {
        if (isProcessing) return;

        if (e.key >= "0" && e.key <= "9") {
            buffer += e.key;
            if (timeout) clearTimeout(timeout);

            timeout = setTimeout(() => {
                buffer = "";
            }, 1000);

            if (buffer.length === 10) {
                processCardId(buffer);
            }
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (buffer.length === 10) {
                processCardId(buffer);
            } else if (buffer.length > 0) {
                showError(`Invalid card ID length: ${buffer.length} digits`);
                buffer = "";
            }
        } else {
            buffer = "";
        }
    });

    // --- Web NFC support (for Chrome on Android) ---
    if ("NDEFReader" in window) {
        try {
            const ndef = new NDEFReader();
            ndef.scan().then(() => {
                ndef.onreading = ({ serialNumber }) => {
                    processCardId(serialNumber);
                };
            }).catch((error) => {
                showError("NFC scan failed. Make sure you're using Chrome on Android with NFC enabled.");
            });
        } catch (error) {
            showError("NFC scan failed. Make sure you're using Chrome on Android with NFC enabled.");
        }
    } else {
        // Not a fatal error, fallback to keyboard input
        // Optionally, show a warning if you want
        // showError("Your browser doesn't support Web NFC. Try Chrome on Android.");
    }

    // --- Process card ID ---
    async function processCardId(serialNumber) {
        if (isProcessing) return;
        isProcessing = true;

        serialNumber = serialNumber.trim();
        if (!isValidSerial(serialNumber)) {
            showError("Invalid Card ID. Must be 10 digits.");
            buffer = "";
            isProcessing = false;
            return;
        }

        nfcIdInput.value = serialNumber;

        try {
            const response = await fetch("/mark-institute-attendance/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    nfc_serial: serialNumber,
                    institute_id: instituteId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Error processing attendance");
            }

            const data = await response.json();

            if (data.action === "checkin") {
                showStatus(`
                    <p class="text-xl font-bold">Welcome!</p>
                    <p>${data.message}</p>
                    <p class="text-sm text-gray-600">Date: ${data.date}</p>
                    <p class="text-sm text-gray-600">Time: ${data.time}</p>
                `);
            } else if (data.action === "checkout") {
                showStatus(`
                    <p class="text-xl font-bold">Thank you!</p>
                    <p>${data.message}</p>
                    <p class="text-sm text-gray-600">Date: ${data.date}</p>
                    <p class="text-sm text-gray-600">Time: ${data.time}</p>
                `);
            } else {
                showError("Unexpected server response.");
            }
        } catch (err) {
            showError(err.message);
        } finally {
            nfcIdInput.value = "";
            buffer = "";
            isProcessing = false;
        }
    }
});
