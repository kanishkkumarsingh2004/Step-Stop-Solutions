# TODO: Optimize all_attendance View

- [ ] Fix pagination from 250 to 25 per page
- [ ] Apply search filter early on the queryset before fetching data
- [ ] Use prefetch_related for 'user' and 'user__role_numbers' to avoid N+1 queries
- [ ] Prefetch UserSubscription for users in the library to optimize duration/color calculation
- [ ] Ensure role_number is attached correctly after filtering and pagination
- [ ] Test the changes by running the server and checking the attendance page
