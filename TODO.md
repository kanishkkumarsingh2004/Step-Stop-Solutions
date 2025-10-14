# TODO: Implement Gym Payment Page

## Steps to Complete

1. **Modify gym_subscription.html**
   - Change subscribe button to a form that submits to payment page
   - Pass gym_id, plan_id, and coupon_code (if applied) to payment page

2. **Create gym_payment.html template**
   - Display final amount (after coupon discount)
   - Show QR code for UPI payment (using gym's UPI ID)
   - Input field for transaction ID
   - Dropdown for payment mode (UPI/Cash)
   - Proceed button enabled only when transaction ID is entered

3. **Create payment_success.html template**
   - Display success message: "Payment will be validated within 24 hours"

4. **Create gym_payment.js**
   - Handle enabling proceed button when transaction ID is filled
   - For cash mode, generate transaction ID automatically

5. **Update views.py**
   - Add gym_payment_page view: calculate amount, display QR
   - Add gym_payment_success view: create GymTransaction, redirect to success
   - Handle coupon application in payment page

6. **Update urls.py**
   - Add route for gym_payment_page
   - Add route for gym_payment_success

7. **Install qrcode library if needed**
   - Use python-qrcode to generate QR for UPI payment

## Followup Steps
- Test the payment flow
- Ensure QR code generation works
- Handle validation and error messages
- Verify transaction creation in DB
