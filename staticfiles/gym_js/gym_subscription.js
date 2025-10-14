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

    function updatePrices(subscriptions) {
        subscriptions.forEach(plan => {
            const planDiv = document.querySelector(`[data-plan-id="${plan.id}"]`);
            if (planDiv) {
                const discountPriceSpan = planDiv.querySelector('.discount-price');
                const normalPriceSpan = planDiv.querySelector('.normal-price');
                const diffBadge = planDiv.querySelector('.diff-badge');

                if (discountPriceSpan) {
                    discountPriceSpan.innerHTML = plan.discount_price_display;
                }
                if (normalPriceSpan) {
                    normalPriceSpan.innerHTML = plan.normal_price_display;
                }
                if (diffBadge) {
                    if (plan.diff_display) {
                        diffBadge.innerHTML = plan.diff_display;
                        diffBadge.classList.remove('hidden');
                    } else {
                        diffBadge.classList.add('hidden');
                    }
                }
            }
        });
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
                const response = await fetch(window.location.href, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: new URLSearchParams({
                        'coupon_code': code,
                        'apply_to_all': '1'
                    })
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    showMessage(data.message || "Coupon applied successfully!");
                    if (data.subscriptions) {
                        updatePrices(data.subscriptions);
                    }
                } else {
                    showMessage(data.error || "Invalid coupon code.", false);
                }
            } catch (err) {
                showMessage("An error occurred. Please try again.", false);
            }
            applyBtn.disabled = false;
            applyBtn.textContent = "Apply to All";
        });
    }
});
