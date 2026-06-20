from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Doctor

class PatientRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic', 
                  'phone', 'address', 'password1', 'password2')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'  # Get default role
        if commit:
            user.save()
        return user


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['speciality', 'work_experience']
        widgets = {
            'speciality': forms.Textarea(attrs={'rows': 5}),
            'work_experience': forms.Textarea(attrs={'rows': 5}),
        }
