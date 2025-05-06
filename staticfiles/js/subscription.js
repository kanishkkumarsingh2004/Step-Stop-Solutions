function handlePaymentSuccess(response) {
    const csrfToken = '{{ csrf_token }}';
    const couponId = new URLSearchParams(window.location.search).get('coupon');

    if (couponId) {
        fetch('/handle-payment-success/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                coupon_id: couponId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Coupon usage recorded successfully');
            } else {
                console.error('Error recording coupon usage:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const couponCode = document.getElementById('coupon_code').value;
        if (couponCode) {
            const action = this.getAttribute('action');
            this.setAttribute('action', `${action}?coupon=${couponCode}`);
        }
    });
});

function applyCoupon() {
    const couponCode = document.getElementById('coupon_code').value;
    const messageDiv = document.getElementById('coupon_message');
    const libraryId = parseInt(document.getElementById('libid').textContent);

    if (!couponCode) {
        messageDiv.textContent = "Please enter a coupon code";
        messageDiv.className = "text-red-500";
        return;
    }

    fetch('/apply-coupon/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
            coupon_code: couponCode,
            library_id: libraryId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            messageDiv.textContent = data.message;
            messageDiv.className = "text-green-500";
            
            data.discounted_plans.forEach(plan => {
                const priceContainer = document.querySelector(`#plan_${plan.id}`);
                if (priceContainer) {
                    const priceDisplay = priceContainer.querySelector('.price-display');
                    const couponDiscount = priceContainer.querySelector(`#coupon_discount_${plan.id}`);
                    const percentageElement = priceContainer.closest('.p-6').querySelector('.percentage-difference');
                    const normalPrice = parseFloat(plan.original_price);
                    const discountedPrice = parseFloat(plan.discounted_price);
                    const discountAmount = normalPrice - discountedPrice;

                    // Reset previous discount display
                    if (percentageElement) {
                        const basePercentage = percentageElement.textContent.split('+')[0].trim();
                        percentageElement.textContent = basePercentage;
                    }

                    if (priceDisplay) {
                        priceDisplay.textContent = plan.discounted_price;
                    }

                    if (couponDiscount) {
                        couponDiscount.textContent = `(You save ₹${discountAmount.toFixed(2)})`;
                        couponDiscount.classList.remove('hidden');
                    }

                    if (percentageElement) {
                        const discountPercentage = (discountAmount / normalPrice) * 100;
                        percentageElement.textContent = `${percentageElement.textContent} + ${discountPercentage.toFixed(2)}% off`;
                    }

                    const form = priceContainer.closest('div').querySelector('form');
                    if (form) {
                        form.action = `/payment/${plan.id}/?coupon=${couponCode}`;
                    }
                }
            });
        } else {
            messageDiv.textContent = data.message;
            messageDiv.className = "text-red-500";
        }
    })
    .catch(error => {
        messageDiv.textContent = "An error occurred while applying the coupon";
        messageDiv.className = "text-red-500";
        console.error('Error:', error);
    });
}