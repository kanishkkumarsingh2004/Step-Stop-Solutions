# TODO: Add Verify Payment Feature to Gym Dashboard

## Steps Completed:

1. **✓ Add "Verify Payment" button to Quick Actions in gym_dashboard.html**
   - Located the Quick Actions card in the template.
   - Added a new link/button for "Verify Payments" that points to 'verify_gym_payments' URL.

2. **✓ Create verify_payment_page view in views.py**
   - Added verify_gym_payments view function that fetches pending GymTransaction objects for the gym.
   - Ensured only the gym owner can access it using get_object_or_404 with owner=request.user.
   - Passed the transactions to the template.

3. **✓ Create verify_payments.html template**
   - Created a new template that lists pending transactions in a table.
   - Included columns for transaction ID, user, plan, amount, date, and action buttons.
   - Added AJAX functionality via included JS file.

4. **✓ Add URL for verify_payment_page in urls.py**
   - Added path 'verify-payments/<str:gym_id>/' for verify_gym_payments view.

5. **✓ Create AJAX view for verifying payment status**
   - Added verify_gym_payment_status view that accepts POST requests to update transaction status.
   - Used JsonResponse to return success/error messages.

6. **✓ Add URL for AJAX endpoint in urls.py**
   - Added path 'verify-payment-status/<str:gym_id>/<int:transaction_id>/' for AJAX view.

7. **✓ Create JavaScript file for AJAX calls**
   - Created gym_verify_payment.js in static/gym_js/.
   - Implemented verifyPayment function to send AJAX requests and update UI.

8. **✓ Update template to include the JS file**
   - Loaded the new JS file in verify_payments.html.

9. **Test the functionality**
   - Ensure buttons work, AJAX updates status, and page reflects changes.
   - Note: URL in JS is hardcoded to /my_library/gym/... - may need adjustment based on actual URL structure.
