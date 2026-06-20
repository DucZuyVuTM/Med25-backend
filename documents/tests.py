import time
import random
import string
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.forms import modelform_factory

from hypothesis import given, settings as hyp_settings
from hypothesis.extra.django import from_form, TestCase as HypothesisTestCase

from accounts.models import Position, Employee, Administrator
from .models import Document


User = get_user_model()

DocumentForm = modelform_factory(Document, fields=['content', 'formation_date'])

FUZZ_STRINGS = [
    '', 'a' * 1000, '<script>alert(1)</script>',
    "'; DROP TABLE documents_document; --",
]


def rand_str(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def rand_phone():
    return '+84' + ''.join(random.choices(string.digits, k=9))

# Create your tests here.
class DocumentFormFuzzTest(HypothesisTestCase):
    """Fuzzing tests for DocumentCreateView and DocumentUpdateView."""

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
        Document.objects.all().delete()
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

    def _login_as_administrator(self):
        """Create admin, login, return Administrator instance that signal created."""
        user = self._create_administrator_user()
        self.client.login(username=user.username, password='pass123')
        return user.employee_profile.administrator_profile

    # ===========================
    # Test for DocumentCreateView
    # ===========================
    @hyp_settings(deadline=None, max_examples=15)
    @given(from_form(DocumentForm))
    def test_create_document_with_fuzz_data(self, form_data):
        """Test DocumentCreateView with fuzzing data."""
        self._login_as_administrator()

        data = form_data.data
        self.assertNotEqual(data, {}, "Form data should not be empty")

        url = reverse('documents:create')
        response = self.client.post(url, data)

        self.assertNotEqual(response.status_code, 500)

    # ===========================
    # Test for DocumentUpdateView
    # ===========================
    @hyp_settings(deadline=None, max_examples=15)
    @given(from_form(DocumentForm))
    def test_update_document_with_fuzz_data(self, form_data):
        """Test DocumentUpdateView with fuzzing data."""
        administrator = self._login_as_administrator()

        document = Document.objects.create(
            administrator=administrator,
            content='Initial content',
            formation_date=date.today(),
        )

        data = form_data.data
        self.assertNotEqual(data, {}, "Form data should not be empty")

        url = reverse('documents:edit', kwargs={'pk': document.pk})
        response = self.client.post(url, data)

        self.assertNotEqual(
            response.status_code, 500,
            f"Server crashed with payload: {data}"
        )


class DocumentAdminFuzzTest(TestCase):
    """Fuzz tests for Document admin."""
    
    @classmethod
    def setUpTestData(cls):
        # Create superuser (general)
        cls.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
        )
        
        # Create default position (general)
        cls.position = Position.objects.create(
            title='Admin Position',
            salary=Decimal('10000000'),
            access_category='Full',
        )
    
    def setUp(self):
        # Login before each test
        self.client.login(username='superadmin', password='superpassword123')
        
        # Create fresh administrator for each test (unique to avoid conflicts)
        unique_username = f'test_admin_{int(time.time()*1000)}_{rand_str(5)}'
        
        self.admin_user = User.objects.create_user(
            username=unique_username,
            password='pass123',
            role='administrator'
        )
        
        # Use get_or_create to avoid signal conflicts
        self.employee, _ = Employee.objects.get_or_create(
            user=self.admin_user,
            defaults={
                'position': self.position,
                'employment_date': date.today(),
                'contract_end_date': date.today(),
            }
        )
        
        self.administrator, _ = Administrator.objects.get_or_create(
            employee=self.employee,
            defaults={
                'system_access_rights': 'Full',
            }
        )
    
    def test_create_document_fuzz_content(self):
        url = reverse('admin:documents_document_add')
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'administrator': self.administrator.pk,
                    'content': fuzz,
                    'formation_date': date.today().isoformat(),
                })
                self.assertNotEqual(response.status_code, 500, 
                                   f'Server error with fuzz: {fuzz}')
    
    def test_create_document_fuzz_date(self):
        url = reverse('admin:documents_document_add')
        date_cases = ['', 'not-a-date', '9999-99-99', '2000-01-01', 
                      '2024-13-45', '2024-02-30']
        for date_value in date_cases:
            with self.subTest(date=date_value):
                response = self.client.post(url, {
                    'administrator': self.administrator.pk,
                    'content': 'Test content',
                    'formation_date': date_value,
                })
                self.assertNotEqual(response.status_code, 500,
                                   f'Server error with date: {date_value}')
    
    def test_create_document_fuzz_long_content(self):
        """Test with extremely long content."""
        url = reverse('admin:documents_document_add')
        long_content = 'A' * 10000  # 10,000 characters
        
        response = self.client.post(url, {
            'administrator': self.administrator.pk,
            'content': long_content,
            'formation_date': date.today().isoformat(),
        })
        self.assertNotEqual(response.status_code, 500)
    
    def test_create_document_empty_content(self):
        """Test with empty content."""
        url = reverse('admin:documents_document_add')
        response = self.client.post(url, {
            'administrator': self.administrator.pk,
            'content': '',
            'formation_date': date.today().isoformat(),
        })
        # Should return 200 (form error) or 302, not 500
        self.assertNotEqual(response.status_code, 500)
