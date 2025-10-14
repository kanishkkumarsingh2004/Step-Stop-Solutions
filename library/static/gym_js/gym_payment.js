document.addEventListener("DOMContentLoaded", function() {
    const transactionIdInput = document.getElementById("transaction_id");
    const paymentModeSelect = document.getElementById("payment_mode");
    const proceedBtn = document.getElementById("proceed-btn");

    function toggleProceedButton() {
        const transactionId = transactionIdInput.value.trim();
        const paymentMode = paymentModeSelect.value;

        if (paymentMode === "CASH") {
            // For cash, generate a transaction ID if not provided
            if (!transactionId) {
                const generatedId = "CASH-" + Date.now();
                transactionIdInput.value = generatedId;
            }
            proceedBtn.disabled = false;
        } else {
            // For UPI, require transaction ID
            proceedBtn.disabled = !transactionId;
        }
    }

    transactionIdInput.addEventListener("input", toggleProceedButton);
    paymentModeSelect.addEventListener("change", toggleProceedButton);

    // Initial check
    toggleProceedButton();
});
