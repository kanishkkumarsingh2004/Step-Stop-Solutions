from django.test import TestCase, Client
from django.utils import timezone
from .models import CustomUser, Library, Attendance, UserSubscription
import json

# Create your tests here.

class AttendanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@gmail.com',
            password='Kumar2004@123',
            nfc_serial='123456'
        )
        self.library = Library.objects.create(
            venue_name='KK_library',
            owner=self.user
        )
        UserSubscription.objects.create(
            user=self.user,
            library=self.library,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )

    def test_mark_attendance(self):
        # First tap - check in
        response = self.client.post('/mark-attendance/', 
            json.dumps({'nfc_serial': '123456', 'library_id': self.library.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('checkin', response.json()['action'])

        # Second tap - check out
        response = self.client.post('/mark-attendance/', 
            json.dumps({'nfc_serial': '123456', 'library_id': self.library.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('checkout', response.json()['action'])
