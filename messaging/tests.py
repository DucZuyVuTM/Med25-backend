import random
import string

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from hypothesis import given, settings as hyp_settings
from hypothesis.extra.django import from_form, TestCase as HypothesisTestCase
from hypothesis.strategies import text

from accounts.models import Position, Employee, Administrator
from .forms import MessageForm
from .models import Email

User = get_user_model()

FUZZ_STRINGS = [
    '', 'a' * 1000, '<script>alert(1)</script>',
    "'; DROP TABLE messaging_message; --",
    '\x00\x01\x02',
]


def rand_str(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Create your tests here.
class MessagingFormFuzzTest(HypothesisTestCase):
    """Fuzzing tests for EmailCreateView and ThreadView."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
        )
        self.position = Position.objects.create(
            title='Test Position',
            salary=0,
            access_category='Basic',
        )

    def tearDown(self):
        """Clean up after each test."""
        Email.objects.all().delete()
        Administrator.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        User.objects.filter(username='superadmin').delete()
        Position.objects.all().delete()

    def _create_administrator_user(self):
        """Create user with role='administrator'."""
        user = User.objects.create_user(
            username=rand_str(),
            password='pass123',
            role='administrator',
            first_name='Alice',
            last_name='Admin',
            email='admin@example.com',
        )
        return user

    def _create_patient_user(self):
        user = User.objects.create_user(
            username=rand_str(),
            password='pass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            email='patient@example.com',
        )
        return user

    def _create_administrator(self):
        """Create administrator without login for adding to Email thread."""
        user = self._create_administrator_user()
        return user.employee_profile.administrator_profile

    def _login_as_administrator(self):
        administrator = self._create_administrator()
        self.client.login(
            username=administrator.employee.user.username, password='pass123'
        )
        return administrator

    def _login_as_patient(self):
        user = self._create_patient_user()
        self.client.login(username=user.username, password='pass123')
        return user

    # ========================
    # Test for EmailCreateView
    # ========================
    @hyp_settings(deadline=None, max_examples=15)
    @given(text(max_size=200))
    def test_create_email_as_administrator_with_fuzz_data(self, patient_value):
        """Admin creates new thread - need to fuzz the value POST['patient']."""
        self._login_as_administrator()
        url = reverse('messaging:create')
        response = self.client.post(url, {'patient': patient_value})
        self.assertNotEqual(response.status_code, 500)

    @hyp_settings(deadline=None, max_examples=15)
    @given(text(max_size=200))
    def test_create_email_as_patient_with_fuzz_data(self, administrator_value):
        """Patient creates new thread - need to fuzz the value POST['administrator']."""
        self._login_as_patient()
        url = reverse('messaging:create')
        response = self.client.post(url, {'administrator': administrator_value})
        self.assertNotEqual(response.status_code, 500)

    # ===================
    # Test for ThreadView
    # ===================
    @hyp_settings(deadline=None, max_examples=15)
    @given(from_form(MessageForm))
    def test_thread_reply_as_administrator_with_fuzz_data(self, form_data):
        """Admin sends message in his/her own thread."""
        administrator = self._login_as_administrator()
        patient = self._create_patient_user()
        thread = Email.objects.create(
            administrator=administrator,
            patient=patient,
            status='open',
        )

        data = form_data.data
        self.assertNotEqual(data, {}, "Form data should not be empty")

        url = reverse('messaging:thread', kwargs={'pk': thread.pk})
        response = self.client.post(url, data)

        self.assertNotEqual(response.status_code, 500)

    @hyp_settings(deadline=None, max_examples=15)
    @given(from_form(MessageForm))
    def test_thread_reply_as_patient_with_fuzz_data(self, form_data):
        """Patient sends message in his/her own thread."""
        administrator = self._create_administrator()
        patient = self._create_patient_user()
        thread = Email.objects.create(
            administrator=administrator,
            patient=patient,
            status='open',
        )
        self.client.login(username=patient.username, password='pass123')

        data = form_data.data
        self.assertNotEqual(data, {}, "Form data should not be empty")

        url = reverse('messaging:thread', kwargs={'pk': thread.pk})
        response = self.client.post(url, data)

        self.assertNotEqual(
            response.status_code, 500,
            f"Server crashed with payload: {data}"
        )


class MessagingAdminFuzzTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
        )
        cls.position = Position.objects.create(
            title='Admin Position',
            salary=Decimal('10000000'),
            access_category='Full',
        )
        cls.admin_user = User.objects.create_user(
            username='admin_msg', password='pass123', role='administrator'
        )
        cls.employee, _ = Employee.objects.get_or_create(
            user=cls.admin_user,
            defaults={
                'position': cls.position,
                'surname': 'Admin', 'name': 'Test',
                'phone': '0900000001', 'address': 'Test St',
                'employment_date': date.today(),
                'end_date_of_the_contract': date.today(),
            }
        )
        cls.administrator, _ = Administrator.objects.get_or_create(
            employee=cls.employee,
            defaults={'system_access_rights': 'Full'},
        )
        cls.patient_user = User.objects.create_user(
            username='patient_msg', password='pass123', role='patient'
        )
        cls.email = Email.objects.create(
            administrator=cls.administrator,
            patient=cls.patient_user,
            status='open',
        )

    def setUp(self):
        self.client.login(username='superadmin', password='superpassword123')

    def test_create_message_fuzz_content(self):
        url = reverse('admin:messaging_message_add')
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'email': self.email.pk,
                    'content': fuzz,
                    'send_date': date.today().isoformat(),
                    'send_time': '10:00:00',
                    'sender_type': 'admin',
                })
                self.assertNotEqual(response.status_code, 500)

    def test_create_message_fuzz_sender_type(self):
        url = reverse('admin:messaging_message_add')
        for sender in ['admin', 'patient', '', 'unknown', '<script>', '123']:
            with self.subTest(sender=sender):
                response = self.client.post(url, {
                    'email': self.email.pk,
                    'content': 'Test message',
                    'send_date': date.today().isoformat(),
                    'send_time': '10:00:00',
                    'sender_type': sender,
                })
                self.assertNotEqual(response.status_code, 500)
