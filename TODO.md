# TODO: Merge CoachingAttendance with LibraryAttendance in User Attendance View

## Tasks
- [x] Import CoachingAttendance in views.py
- [x] Modify user_attendance function to fetch both LibraryAttendance and CoachingAttendance
- [x] Create combined list with 'type' field ('library' or 'coaching')
- [x] Sort combined list by check_in_time descending
- [x] Update search logic for both library and coaching records
- [x] Handle duration and color calculations for both types
- [x] Apply pagination to combined sorted list
- [x] Update user_attendance.html template to display attendance type
- [ ] Test the merged view functionality
- [ ] Verify search works for both types
- [ ] Check pagination on combined results
