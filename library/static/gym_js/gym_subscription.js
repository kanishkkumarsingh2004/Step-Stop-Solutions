// Gym subscription coupon logic, similar to library/static/js/subscription.js

document.addEventListener('DOMContentLoaded', function() {
    const applyBtn = document.getElementById('apply-coupon-btn');
    const couponInput = document.getElementById('coupon-code');
    const couponMsg = document.getElementById('coupon-message');
    const gymUid = document.body.innerHTML.match(/gyms\/(.*?)\//)[1]; // crude but works for now
    const applyCouponUrl = `/gyms/${gymUid}/apply-coupon/`;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    applyBtn.addEventListener('click', function() {
        const code = couponInput.value.trim();
        if (!code) {
            couponMsg.textContent = 'Please enter a coupon code';
            couponMsg.className = 'text-red-500';
            return;
        }
        couponMsg.textContent = 'Applying coupon...';
        fetch(applyCouponUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `coupon_code=${encodeURIComponent(code)}`
        })
        .then(res => res.json())
        .then(data => {
            couponMsg.textContent = data.message;
            if (data.success && data.discounts) {
                for (const planId in data.discounts) {
                    const el = document.getElementById(`plan-discounted-${planId}`);
                    const couponDiscount = document.getElementById(`coupon_discount_${planId}`);
                    if (el) {
                        el.textContent = `₹${parseFloat(data.discounts[planId]).toFixed(2)}`;
                        el.classList.add('text-green-700', 'font-bold');
                        if (couponDiscount) {
                            couponDiscount.textContent = '(Coupon applied!)';
                            couponDiscount.classList.remove('hidden');
                        }
                    }
                }
            } else {
                // Reset all coupon discounts
                document.querySelectorAll('.price-display').forEach(el => {
                    el.classList.remove('text-green-700', 'font-bold');
                });
                document.querySelectorAll('[id^="coupon_discount_"]').forEach(el => {
                    el.classList.add('hidden');
                });
            }
        })
        .catch(() => {
            couponMsg.textContent = 'An error occurred while applying the coupon.';
            couponMsg.className = 'text-red-500';
        });
    });
}); 