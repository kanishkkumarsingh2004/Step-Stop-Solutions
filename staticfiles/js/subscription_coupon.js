document.addEventListener('DOMContentLoaded', function() {
    // Utility Functions
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

    function formatPrice(price) {
        return parseFloat(price).toFixed(2);
    }

    function showMessage(element, message, type = 'error') {
        if (!element) return;
        
        const colors = {
            success: 'green',
            error: 'red',
            info: 'blue'
        };
        element.innerHTML = `
            <div class="p-3 bg-${colors[type]}-50 border border-${colors[type]}-200 rounded-lg">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-${colors[type]}-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${type === 'success' ? 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' : 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'}"></path>
                    </svg>
                    <span class="text-${colors[type]}-700 text-sm">${message}</span>
                </div>
            </div>
        `;
    }

    // Price Update Functions
    function updateSubscriptionPrice(subscriptionId, data) {
        const priceSection = document.querySelector(`.price-section[data-subscription-id="${subscriptionId}"]`);
        const subscribeBtn = document.querySelector(`.subscribe-btn[data-subscription-id="${subscriptionId}"]`);
        
        if (!priceSection || !subscribeBtn) {
            console.error('Could not find price elements for subscription:', subscriptionId);
            return;
        }

        const originalPrice = parseFloat(priceSection.dataset.originalPrice);
        const discountedPrice = parseFloat(data.discounted_price);
        const savings = parseFloat(data.discount_amount);

        priceSection.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-gray-400 line-through text-sm">₹${formatPrice(originalPrice)}</span>
                <span class="text-3xl font-bold text-green-600">₹${formatPrice(discountedPrice)}</span>
            </div>
            <div class="text-sm text-green-600 font-medium text-right">
                Save ₹${formatPrice(savings)}
            </div>
        `;

        subscribeBtn.innerHTML = `
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
            Subscribe Now - ₹${formatPrice(discountedPrice)}
        `;
        subscribeBtn.dataset.currentPrice = discountedPrice;

        // Store coupon data in sessionStorage
        const couponData = {
            applied: true,
            coupon_code: data.coupon_code,
            original_price: originalPrice,
            discount_amount: savings,
            final_price: discountedPrice,
            discount_type: data.discount_type,
            discount_value: data.discount_value,
            subscription_name: data.subscription_name,
            subscription_id: subscriptionId,
            institution_uid: data.institution_uid,
            course_duration: data.course_duration,
            start_time: data.start_time,
            end_time: data.end_time,
            start_date: data.start_date
        };
        sessionStorage.setItem('coupon_data', JSON.stringify(couponData));
    }

    // Initialize with default values on page load
    function initializeCouponState() {
        const defaultCouponData = {
            applied: false,
            coupon_code: null,
            original_price: null,
            discount_amount: null,
            final_price: null,
            discount_type: null,
            discount_value: null,
            subscription_name: null,
            subscription_id: null,
            institution_uid: null,
            course_duration: null,
            start_time: null,
            end_time: null,
            start_date: null
        };
        sessionStorage.setItem('coupon_data', JSON.stringify(defaultCouponData));
    }

    // Call initialize on page load
    initializeCouponState();

    // Add event listener for the global apply button
    const applyGlobalCouponBtn = document.getElementById('apply-global-coupon-btn');
    const globalCouponInput = document.getElementById('global-coupon-input');
    const globalCouponMessage = document.getElementById('global-coupon-message');

    if (applyGlobalCouponBtn && globalCouponInput) {
        applyGlobalCouponBtn.addEventListener('click', async function() {
            try {
                // Check if coupon is already applied
                const currentCouponData = JSON.parse(sessionStorage.getItem('coupon_data') || '{}');
                if (currentCouponData.applied) {
                    showMessage(globalCouponMessage, 'A coupon has already been applied. Please refresh the page to apply a different coupon.', 'error');
                    return;
                }

                // Disable button and show loading state
                applyGlobalCouponBtn.disabled = true;
                
                const couponCode = globalCouponInput.value.trim();
                if (!couponCode) {
                    showMessage(globalCouponMessage, 'Please enter a coupon code', 'error');
                    setTimeout(() => {
                        applyGlobalCouponBtn.disabled = false;
                    }, 5000);
                    return;
                }

                // Get all subscription IDs
                const subscriptionIds = Array.from(document.querySelectorAll('.subscribe-btn'))
                    .map(btn => btn.dataset.subscriptionId)
                    .filter(id => id);

                if (subscriptionIds.length === 0) {
                    showMessage(globalCouponMessage, 'No subscriptions found', 'error');
                    setTimeout(() => {
                        applyGlobalCouponBtn.disabled = false;
                    }, 5000);
                    return;
                }
            
                let successCount = 0;
                let firstError = null;

                // Apply coupon to each subscription
                for (const subscriptionId of subscriptionIds) {
                    try {
                        const subscribeBtn = document.querySelector(`.subscribe-btn[data-subscription-id="${subscriptionId}"]`);
                        if (!subscribeBtn) {
                            console.error('Subscribe button not found for subscription:', subscriptionId);
                            continue;
                        }

                        const currentPrice = parseFloat(subscribeBtn.dataset.currentPrice);
                        if (isNaN(currentPrice)) {
                            console.error('Invalid current price for subscription:', subscriptionId);
                            continue;
                        }

                        const response = await fetch(`/subscription/${subscriptionId}/apply-coupon/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            body: JSON.stringify({
                                coupon_code: couponCode,
                                current_price: currentPrice
                            })
                        });

                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                
                        const data = await response.json();
                
                        if (data.success) {
                            updateSubscriptionPrice(subscriptionId, data);
                            successCount++;
                        } else {
                            if (!firstError) {
                                firstError = data.error;
                            }
                        }
                    } catch (error) {
                        console.error('Error applying coupon to subscription:', subscriptionId, error);
                        if (!firstError) {
                            firstError = 'An error occurred while applying the coupon';
                        }
                    }
                }

                if (successCount === subscriptionIds.length) {
                    showMessage(globalCouponMessage, 'Coupon applied successfully to all programs', 'success');
                    globalCouponInput.value = '';
                    // Mark coupon as applied in session storage
                    const couponData = {
                        applied: true,
                        coupon_code: couponCode
                    };
                    sessionStorage.setItem('coupon_data', JSON.stringify(couponData));
                } else if (successCount > 0) {
                    if (firstError && firstError.includes('not applicable')) {
                        showMessage(globalCouponMessage, `Coupon applied to some programs. ${firstError}`, 'info');
                    } else {
                        showMessage(globalCouponMessage, `Coupon applied to ${successCount} out of ${subscriptionIds.length} programs`, 'info');
                    }
                } else {
                    if (firstError && firstError.includes('not applicable')) {
                        showMessage(globalCouponMessage, firstError, 'error');
                    } else {
                        showMessage(globalCouponMessage, firstError || 'Failed to apply coupon to any programs', 'error');
                    }
                }

                setTimeout(() => {
                    applyGlobalCouponBtn.disabled = false;
                }, 5000);

            } catch (error) {
                console.error('Error in coupon application:', error);
                showMessage(globalCouponMessage, 'An unexpected error occurred. Please try again.', 'error');
                setTimeout(() => {
                    applyGlobalCouponBtn.disabled = false;
                }, 5000);
            }
        });
    }
    
    // Add click handler for subscribe buttons
    const subscribeButtons = document.querySelectorAll('.subscribe-btn');
    subscribeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const subscriptionId = this.dataset.subscriptionId;
            const couponData = JSON.parse(sessionStorage.getItem('coupon_data') || '{}');
            
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = this.href;
            
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = getCookie('csrftoken');
            form.appendChild(csrfInput);
            
            // Only add coupon data if it exists and was actually applied
            if (couponData.applied === true && couponData.subscription_id === subscriptionId) {
                const couponInput = document.createElement('input');
                couponInput.type = 'hidden';
                couponInput.name = 'coupon_data';
                couponInput.value = JSON.stringify({
                    coupon_code: couponData.coupon_code,
                    original_price: couponData.original_price,
                    discount_amount: couponData.discount_amount,
                    final_price: couponData.final_price,
                    discount_type: couponData.discount_type,
                    discount_value: couponData.discount_value,
                    subscription_name: couponData.subscription_name,
                    subscription_id: couponData.subscription_id,
                    institution_uid: couponData.institution_uid,
                    course_duration: couponData.course_duration,
                    start_time: couponData.start_time,
                    end_time: couponData.end_time,
                    start_date: couponData.start_date
                });
                form.appendChild(couponInput);
                
                // Clear session storage after form submission
                sessionStorage.removeItem('coupon_data');
            }
            
            document.body.appendChild(form);
            form.submit();
        });
    });

    // Clear session storage on page load
    window.addEventListener('load', function() {
        // Clear session storage
        sessionStorage.removeItem('coupon_data');
        
        // Clear message display
        if (globalCouponMessage) {
            globalCouponMessage.innerHTML = '';
        }

        // Clear coupon input
        if (globalCouponInput) {
            globalCouponInput.value = '';
        }

        // Initialize coupon state
        initializeCouponState();
    });
}); 