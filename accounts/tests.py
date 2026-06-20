import random
import string
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from hypothesis import given, settings as hyp_settings
from hypothesis.extra.django import from_form, TestCase as HypothesisTestCase
from hypothesis.strategies import text, emails

from .forms import DoctorProfileForm
from .models import Administrator, Doctor, Employee, Position


User = get_user_model()


def rand_str(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def rand_phone():
    return '+84' + ''.join(random.choices(string.digits, k=9))


FUZZ_STRINGS = [
    '', 'a' * 1000, '<script>alert(1)</script>',
    "'; DROP TABLE accounts_employee; --", '\x00\x01\x02',
    '../../../etc/passwd', '%s %s %s', '\n\r\t', '0', '-1',
    '99999999999999999999',
]

# Create your tests here.
class UserFormFuzzTest(TestCase):
    """Send unusual data to the user form"""

    def _create_valid_reset_password_token(self, email):
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'username': email.split('@')[0]}
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return {'uid': uid, 'token': token}
    
    def test_login_form_with_fuzz_data(self):
        url = reverse('login')

        fuzz_payloads = [
            # === 1. Field username ===
            # Long username
            {'username': 'a' * 151, 'password': 'pass'},

            # Path traversal
            {'username': '../etc/passwd', 'password': 'pass'},

            # XSS
            {'username': '<script>alert(1)</script>', 'password': 'pass'},

            # SQL injection
            {'username': "' OR '1'='1", 'password': 'pass'},

            # === 2. Field password ===
            # Short password
            {'username': 'testuser', 'password': 'short'},

            # SQL injection in password
            {'username': 'testuser', 'password': "' OR '1'='1"},

            # XSS in password
            {'username': 'testuser', 'password': '<script>alert(1)</script>'},

            # === 3. Missing fields ===
            # Missing username
            {'password': 'pass'},

            # Missing password
            {'username': 'testuser'},

            # Both missing
            {},
        ]

        for payload in fuzz_payloads:
            response = self.client.post(url, payload)

            # Response cannot be error - it must return 200 and validation error
            self.assertNotEqual(
                response.status_code, 500,
                f"Server crashed with payload: {payload}"
            )

    def test_password_change_form_with_fuzz_data(self):
        self.client.login(username='testuser', password='oldpass123')
        url = reverse('password_change')

        fuzz_payloads = [
            # Long old password
            {'old_password': 'a'*1000,
             'new_password1': 'newpass123', 'new_password2': 'newpass123'},

            # New password doesn't match
            {'old_password': 'oldpass123',
             'new_password1': 'newpass123', 'new_password2': 'different'},

            # XSS in new password
            {'old_password': 'oldpass123',
             'new_password1': '<script>', 'new_password2': '<script>'},

            # SQL injection
            {'old_password': 'oldpass123',
             'new_password1': "' OR '1'='1", 'new_password2': "' OR '1'='1"},

            # Missing new_password2
            {'old_password': 'oldpass123', 'new_password1': 'newpass123'},

            # All fields empty
            {},
        ]

        for payload in fuzz_payloads:
            response = self.client.post(url, payload)
            self.assertNotEqual(response.status_code, 500,
                                f"Server crashed with payload: {payload}")

    def test_password_reset_form_with_fuzz_data(self):
        url = reverse('password_reset')

        fuzz_payloads = [
            # XSS in email
            {'email': '<script>alert(1)</script>'},

            # SQL injection
            {'email': "' OR '1'='1"},

            # Long email
            {'email': 'a'*100 + '@example.com'},

            # Invalid email format
            {'email': 'invalid-email'},

            # Missing email
            {},
        ]

        for payload in fuzz_payloads:
            response = self.client.post(url, payload)
            self.assertNotEqual(response.status_code, 500,
                                f"Server crashed with payload: {payload}")

    def test_password_reset_confirm_form_with_fuzz_data(self):
        # Create a valid token first
        token = self._create_valid_reset_password_token('testuser@example.com')
        url = reverse('password_reset_confirm',
                      kwargs={'uidb64': token['uid'], 'token': token['token']})

        fuzz_payloads = [
            # Password doesn't match
            {'new_password1': 'newpass123', 'new_password2': 'different'},

            # XSS in new password
            {'new_password1': '<script>', 'new_password2': '<script>'},

            # Short password
            {'new_password1': 'short', 'new_password2': 'short'},

            # Missing new_password2
            {'new_password1': 'newpass123'},

            # All fields empty
            {},
        ]

        for payload in fuzz_payloads:
            response = self.client.post(url, payload)
            self.assertNotEqual(response.status_code, 500,
                                f"Server crashed with payload: {payload}")


class ProfileFuzzTest(HypothesisTestCase):
    """Fuzzing tests for profile edit views."""

    def setUp(self):
        # Create superuser and position for test
        self.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
        )
        self.position = Position.objects.create(
            title='Test Position',
            salary=0,
            access_category='Basic'
        )

    def tearDown(self):
        """Clean up after each test."""
        Doctor.objects.all().delete()
        Administrator.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        User.objects.filter(username='superadmin').delete()
        Position.objects.all().delete()

    def _create_doctor_user(self):
        """Helper for creating doctor user with full profiles."""
        user = User.objects.create_user(
            username=rand_str(),
            password='pass123',
            role='doctor',
            first_name='John',
            last_name='Doe',
            email='doctor@example.com',
            phone='+1234567890',
            address='123 Main St'
        )
        return user

    def _create_patient_user(self):
        """Helper for creating patient user."""
        user = User.objects.create_user(
            username=rand_str(),
            password='pass123',
            role='patient',
            first_name='Jane',
            last_name='Smith',
            email='patient@example.com',
            phone='+9876543210',
            address='456 Oak St'
        )
        return user

    # ==============================================================
    # Test for ProfileView with method='POST' and user.role='doctor'
    # ==============================================================
    def _login_as_doctor(self):
        # Create doctor user and login
        user = self._create_doctor_user()
        self.client.login(username=user.username, password='pass123')
        return reverse('accounts:profile')

    @hyp_settings(deadline=None, max_examples=15)
    @given(from_form(DoctorProfileForm))
    def test_doctor_profile_form_with_fuzz_data(self, form_data):
        """Test ProfileView with fuzzing data."""
        url = self._login_as_doctor()

        # Get data from form
        data = form_data.data
        self.assertNotEqual(data, {}, "Form data should not be empty")

        # Send POST request
        response = self.client.post(url, data)

        self.assertNotEqual(response.status_code, 500)

    # ========================
    # Test for EditProfileView
    # ========================
    def _login_as_patient(self):
        # Create patient user and login
        user = self._create_patient_user()
        self.client.login(username=user.username, password='pass123')
        return reverse('accounts:edit_profile')

    @hyp_settings(deadline=None, max_examples=15)
    @given(
        first_name=text(max_size=1000),
        last_name=text(max_size=1000),
        email=emails()
    )
    def test_edit_profile_with_fuzz_data(self, first_name, last_name, email):
        """Test EditProfileView with fuzzing data."""
        url = self._login_as_patient()

        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }

        response = self.client.post(url, data)
        self.assertNotEqual(
            response.status_code, 500,
            f"Server crashed with payload: {data}"
        )


class AdminFuzzBase(TestCase):
    """Base class with common setup for all admin fuzz tests."""

    @classmethod
    def setUpTestData(cls):
        # Clean up existing test data
        Doctor.objects.all().delete()
        Administrator.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.filter(username__startswith='test').delete()
        User.objects.filter(username='superadmin').delete()

        # Create superuser
        cls.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
            email='super@med25.com',
        )
        
        # Create default position
        cls.position = Position.objects.create(
            title='Test Position',
            salary=Decimal('5000000'),
            access_category='Basic',
        )

    def setUp(self):
        """Login before each test."""
        self.client.login(username='superadmin', password='superpassword123')

    def assertNoServerError(self, response, url=''):
        self.assertNotEqual(response.status_code, 500, f'Server error at {url}')


class PositionAdminFuzzTest(AdminFuzzBase):
    """Fuzz tests for Position admin."""

    def test_create_position_valid(self):
        url = reverse('admin:accounts_position_add')
        response = self.client.post(url, {
            'title': 'Pediatrician',
            'salary': '8000000',
            'access_category': 'Level 2',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_create_position_fuzz_title(self):
        url = reverse('admin:accounts_position_add')
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'title': fuzz,
                    'salary': '5000000',
                    'access_category': 'Basic',
                })
                self.assertNoServerError(response, url)

    def test_create_position_fuzz_salary(self):
        url = reverse('admin:accounts_position_add')
        salary_cases = ['0', '-1', '99999999999', 'abc', '', '1.5']
        for salary in salary_cases:
            with self.subTest(salary=salary):
                response = self.client.post(url, {
                    'title': rand_str(),
                    'salary': salary or '0',
                    'access_category': 'Basic',
                })
                self.assertNoServerError(response, url)


class EmployeeAdminFuzzTest(AdminFuzzBase):
    """Fuzz tests for Employee admin."""

    def test_create_employee_valid(self):
        url = reverse('admin:accounts_employee_add')
        new_user = User.objects.create_user(
            username=rand_str(), 
            password='pass123', 
            role='doctor'
        )
        response = self.client.post(url, {
            'user': new_user.pk,
            'position': self.position.pk,
            'employment_date': date.today().isoformat(),
            'contract_end_date': (date.today() + timedelta(days=365)).isoformat(),
        })
        self.assertNoServerError(response, url)

    def test_create_employee_fuzz_dates(self):
        url = reverse('admin:accounts_employee_add')
        date_cases = ['2099-01-01', '1900-01-01', 'not-a-date', '', '2024-13-45']
        for date_value in date_cases:
            with self.subTest(date=date_value):
                new_user = User.objects.create_user(
                    username=rand_str(), 
                    password='pass123'
                )
                response = self.client.post(url, {
                    'user': new_user.pk,
                    'position': self.position.pk,
                    'employment_date': date_value,
                    'contract_end_date': date_value,
                })
                self.assertNoServerError(response, url)


class DoctorAdminFuzzTest(AdminFuzzBase):
    """Fuzz tests for Doctor admin."""

    def setUp(self):
        super().setUp()
        # Create fresh doctor data for each test
        self.doctor_user = User.objects.create_user(
            username=rand_str(),  # Unique username each time
            password='pass123',
            role='doctor'
        )
        
        # Use get_or_create to avoid signal conflicts
        self.doctor_employee, _ = Employee.objects.get_or_create(
            user=self.doctor_user,
            defaults={
                'position': self.position,
                'employment_date': date.today(),
                'contract_end_date': date.today() + timedelta(days=365),
            }
        )
        
        self.doctor, _ = Doctor.objects.get_or_create(
            employee=self.doctor_employee,
            defaults={
                'speciality': 'General',
                'work_experience': '5 years',
            }
        )

    def test_edit_doctor_fuzz_speciality(self):
        url = reverse('admin:accounts_doctor_change', args=[self.doctor.pk])
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'employee': self.doctor_employee.pk,
                    'speciality': fuzz,
                    'work_experience': 'Updated',
                })
                self.assertNoServerError(response, url)

    def test_edit_doctor_fuzz_experience(self):
        url = reverse('admin:accounts_doctor_change', args=[self.doctor.pk])
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'employee': self.doctor_employee.pk,
                    'speciality': 'Cardiology',
                    'work_experience': fuzz,
                })
                self.assertNoServerError(response, url)


class AdministratorAdminFuzzTest(AdminFuzzBase):
    """Fuzz tests for Administrator admin."""

    def setUp(self):
        super().setUp()
        # Create fresh administrator data for each test
        self.admin_user = User.objects.create_user(
            username=rand_str(),
            password='pass123',
            role='administrator'
        )
        
        self.admin_employee, _ = Employee.objects.get_or_create(
            user=self.admin_user,
            defaults={
                'position': self.position,
                'employment_date': date.today(),
                'contract_end_date': date.today() + timedelta(days=365),
            }
        )
        
        self.administrator, _ = Administrator.objects.get_or_create(
            employee=self.admin_employee,
            defaults={
                'system_access_rights': 'Full',
            }
        )

    def test_edit_administrator_fuzz_access_rights(self):
        url = reverse('admin:accounts_administrator_change', args=[self.administrator.pk])
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'employee': self.admin_employee.pk,
                    'system_access_rights': fuzz,
                })
                self.assertNoServerError(response, url)
