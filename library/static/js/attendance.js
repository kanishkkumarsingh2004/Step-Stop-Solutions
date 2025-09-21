// static/js/attendance.js
document.addEventListener("DOMContentLoaded", () => {
    console.log("attendance.js loaded");

    const form = document.getElementById("nfc-form");
    const nfcIdInput = document.getElementById("nfc_id");
    const libraryId = document.getElementById("library_id").value;
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
        // Clear previous messages
        while (attendanceStatus.firstChild) {
            attendanceStatus.removeChild(attendanceStatus.firstChild);
        }

        const statusElement = document.createElement("div");
        statusElement.className = `p-6 rounded-lg ${
            isSuccess ? "bg-white" : "bg-red-50"
        } shadow-lg transform transition-all duration-300 ease-in-out scale-100`;
        statusElement.innerHTML = message;
        attendanceStatus.appendChild(statusElement);
        attendanceStatus.classList.remove("hidden");

        // Add a fade-in effect
        requestAnimationFrame(() => {
            statusElement.style.opacity = "0";
            requestAnimationFrame(() => {
                statusElement.style.opacity = "1";
            });
        });

        // Keep the message visible for longer (5 seconds)
        setTimeout(() => {
            statusElement.style.opacity = "0";
            statusElement.style.transform = "scale(0.95)";
            setTimeout(() => {
                statusElement.remove();
                if (!attendanceStatus.children.length) {
                    attendanceStatus.classList.add("hidden");
                }
            }, 300);
        }, 5000);
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

    // --- Process card ID ---
    const processCardId = async (serialNumber) => {
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

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Error processing attendance");
            }

            const data = await response.json();

            if (data.action === "checkin" || data.action === "checkout") {
                const isCheckin = data.action === "checkin";
                // Create the profile image HTML
                const profileHtml = data.user_image_id ? `
                    <img src="https://drive.google.com/thumbnail?id=${data.user_image_id}&sz=s800" 
                         alt="${data.message}"
                         class="w-32 h-32 rounded-full object-cover border-4 ${isCheckin ? "border-green-500" : "border-red-500"} shadow-lg transform transition-all duration-300 hover:scale-105">`
                    : `
                    <div class="w-32 h-32 rounded-full bg-gray-100 border-4 ${isCheckin ? "border-green-500" : "border-red-500"} flex items-center justify-center shadow-lg">
                        <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>`;

                const statusIcon = isCheckin ? `
                    <svg class="w-8 h-8 text-green-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697A9.001 9.001 0 0112 3c4.97 0 9 4.03 9 9s-4.03 9-9 9-9-4.03-9-9c0-1.57.407-3.046 1.12-4.303"/>
                    </svg>` : `
                    <svg class="w-8 h-8 text-red-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l-4-4m0 0l-4-4m4 4l4-4m-4 4l-4 4"/>
                    </svg>`;

                showStatus(`
                    <div class="flex flex-col items-center space-y-6">
                        ${statusIcon}
                        ${profileHtml}
                        <div class="text-center space-y-3">
                            <p class="text-3xl font-bold ${isCheckin ? "text-green-600" : "text-red-600"}">
                                ${isCheckin ? "Welcome to the Library! Please keep Silence!" : "Goodbye! See you again!"}
                            </p>
                            <p class="text-xl text-gray-800">${data.message}</p>
                            <div class="text-xl text-gray-600  ${isCheckin ? "bg-green-100" : "bg-red-100"} bg-gray-50 py-2 px-4 rounded-lg inline-block">
                                <p class="font-bold">Date: ${data.date}</p>
                                <p class="font-bold">Time: ${data.time}</p>
                            </div>
                        </div>
                    </div>
                `, true);
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
    };
});
