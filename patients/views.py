from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from .models import CustomUser, MedicalCard

# Create your views here.
class AdminOrDoctorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('administrator', 'doctor')


class PatientListView(LoginRequiredMixin, AdminOrDoctorRequiredMixin, ListView):
    model = CustomUser
    template_name = 'patients/list.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(role='patient')


class PatientDetailView(LoginRequiredMixin, AdminOrDoctorRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'patients/detail.html'
    context_object_name = 'patient'


class MyCardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'patients/card.html'

    def test_func(self):
        return self.request.user.role == 'patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['medical_card'] = self.request.user.medical_card
        except (CustomUser.DoesNotExist, MedicalCard.DoesNotExist):
            context['medical_card'] = None
        return context
