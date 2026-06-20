from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import CustomUser
from patients.models import MedicalCard


User = get_user_model()


FUZZ_STRINGS = [
    '', 'a' * 1000, '<script>alert(1)</script>',
    "'; DROP TABLE patients_patient; --", '../../../etc/passwd',
]

# Create your tests here.
class PatientFormFuzzTest(TestCase):
    """Send unusual data to the patient form"""
    
    def test_registration_form_with_fuzz_data(self):
        url = reverse('registration')

        fuzz_payloads = [
            # === 1. Field username ===
            # Long name
            {'username': 'a'*151, 'password1': 'pass', 'password2': 'pass', 
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # Path traversal
            {'username': '../etc/passwd', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # XSS
            {'username': '<script>alert(1)</script>', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # SQL injection
            {'username': "' OR '1'='1", 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # === 2. Field password ===
            # Password doesn't match
            {'username': 'helloworld', 'password1': 'samesame', 'password2': 'different',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # Short password
            {'username': 'user123', 'password1': 'short', 'password2': 'short',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # === 3. Field email ===
            # Invalid email
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'invalid-email', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # Long email
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'a'*100 + '@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # === 4. Fields first_name and last_name ===
            # Long fields
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'a'*100, 'last_name': 'b'*100,
            'phone': '+1234567890', 'address': '123 Main St'},

            # Special character
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': '<script>', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '123 Main St'},

            # === 5. Field phone ===
            # Invalid phone number
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': 'invalid_phone', 'address': '123 Main St'},

            # Long phone number
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '1'*30, 'address': '123 Main St'},

            # === 6. Field address ===
            # Long address
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': 'a'*1000},

            # Address with special number
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'phone': '+1234567890', 'address': '<script>alert(1)</script>'},

            # === 7. Missing required fields ===
            # Missing username
            {'password1': 'pass', 'password2': 'pass', 'email': 'test@example.com',
            'first_name': 'John', 'last_name': 'Doe', 'phone': '+1234567890',
            'address': '123 Main St'},

            # Missing password
            {'username': 'testuser', 'email': 'test@example.com',
            'first_name': 'John', 'last_name': 'Doe', 'phone': '+1234567890',
            'address': '123 Main St'},

            # Missing phone number
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'address': '123 Main St'},

            # Missing email
            {'username': 'testuser', 'password1': 'pass', 'password2': 'pass',
            'first_name': 'John', 'last_name': 'Doe', 'phone': '+1234567890',
            'address': '123 Main St'},
        ]

        for payload in fuzz_payloads:
            response = self.client.post(url, payload)

            # Response cannot be error - it must return 200 and validation error
            self.assertNotEqual(
                response.status_code, 500,
                f"Server crashed with payload: {payload}"
            )

            # Ensure no users are created
            self.assertEqual(
                CustomUser.objects.filter(
                    username=payload.get('username')
                ).count(), 0,
                f"User was unexpectedly created with payload: {payload}"
            )


class PatientAdminFuzzBase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='superadmin',
            password='superpassword123',
        )
        
        cls.patient_user = User.objects.create_user(
            username='testpatient',
            password='testpass123',
            role='patient',
        )
        cls.patient = CustomUser.objects.create(
            first_name='Test',
            last_name='Patient',
            phone='0987654321',
            address='456 Test Ave',
        )
        cls.medical_card = MedicalCard.objects.create(
            patient=cls.patient,
            allergy_info='None',
            blood_group='A+',
            current_medication='None',
        )

    def setUp(self):
        self.client.login(username='superadmin', password='superpassword123')


class MedicalCardAdminFuzzTest(PatientAdminFuzzBase):

    def test_edit_medical_card_fuzz_allergy(self):
        url = reverse('admin:patients_medicalcard_change', args=[self.medical_card.pk])
        inline_fields = {
            'history_entries-TOTAL_FORMS': '0',
            'history_entries-INITIAL_FORMS': '0',
            'diagnoses-TOTAL_FORMS': '0',
            'diagnoses-INITIAL_FORMS': '0',
            'analyses-TOTAL_FORMS': '0',
            'analyses-INITIAL_FORMS': '0',
        }
        
        for fuzz in FUZZ_STRINGS:
            with self.subTest(fuzz=repr(fuzz)):
                response = self.client.post(url, {
                    'patient': self.patient.pk,
                    'allergy_info': fuzz,
                    'blood_group': 'A+',
                    'current_medication': 'None',
                    **inline_fields,
                })
                self.assertNotEqual(response.status_code, 500)

    def test_edit_medical_card_fuzz_blood_group(self):
        url = reverse('admin:patients_medicalcard_change', args=[self.medical_card.pk])
        blood_cases = ['A+', 'AB-', 'O+', 'XYZ', '', '123', '<script>']
        
        for blood in blood_cases:
            with self.subTest(blood=blood):
                response = self.client.post(url, {
                    'patient': self.patient.pk,
                    'allergy_info': 'None',
                    'blood_group': blood,
                    'current_medication': 'None',
                })
                self.assertNotEqual(response.status_code, 500)
