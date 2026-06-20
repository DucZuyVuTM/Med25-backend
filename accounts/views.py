from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from .forms import PatientRegistrationForm, DoctorProfileForm
from .models import CustomUser

# Create your views here.
class HomeView(TemplateView):
    template_name = 'pages/home.html'


class RegistrationView(CreateView):
    form_class = PatientRegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email']
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == 'doctor':
            try:
                doctor = self.request.user.employee_profile.doctor_profile
                context['doctor'] = doctor
                context['doctor_form'] = DoctorProfileForm(instance=doctor)
            except Exception:
                context['doctor'] = None
        return context

    def post(self, request, *args, **kwargs):
        if request.user.role == 'doctor':
            try:
                doctor = request.user.employee_profile.doctor_profile
                form = DoctorProfileForm(request.POST, instance=doctor)
                if form.is_valid():
                    form.save()
            except Exception:
                pass
        return redirect('accounts:profile')
