document.addEventListener("DOMContentLoaded", function() {
    const couponForm = document.getElementById("coupon-form");
    const couponInput = document.getElementById("coupon-code");
    const applyBtn = document.getElementById("apply-coupon-btn");
    const couponMessage = document.getElementById("coupon-message");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : "";

    function showMessage(message, isSuccess = true) {
        couponMessage.textContent = message;
        couponMessage.className = isSuccess
            ? "p-2 rounded bg-green-100 text-green-800"
            : "p-2 rounded bg-red-100 text-red-800";
        couponMessage.classList.remove("hidden");
        setTimeout(() => {
            couponMessage.classList.add("hidden");
            couponMessage.textContent = "";
        }, 4000);
    }

    if (couponForm) {
        couponForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            const code = couponInput.value.trim();
            if (!code) {
                showMessage("Please enter a coupon code.", false);
                return;
            }
            applyBtn.disabled = true;
            applyBtn.textContent = "Applying...";
            try {
                const response = await fetch("/apply-coupon/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({ coupon_code: code })
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    showMessage(data.message || "Coupon applied successfully!");
                    // Optionally update price/discount UI here
                } else {
                    showMessage(data.error || "Invalid coupon code.", false);
                }
            } catch (err) {
                showMessage("An error occurred. Please try again.", false);
            }
            applyBtn.disabled = false;
            applyBtn.textContent = "Apply";
        });
    }
});
