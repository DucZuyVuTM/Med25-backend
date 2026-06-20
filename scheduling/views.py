from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from .models import Schedule

# Create your views here.
class ScheduleListView(LoginRequiredMixin, ListView):
    model = Schedule
    template_name = 'scheduling/list.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = Schedule.objects.select_related('administrator__employee')
        # Doctors and patients only see the schedule relevant to them.
        if user.role == 'doctor':
            qs = qs.filter(receptions__doctor__employee__user=user).distinct()
        elif user.role == 'patient':
            qs = qs.filter(receptions__patient=user).distinct()
        return qs


class ScheduleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Schedule
    template_name = 'scheduling/detail.html'
    context_object_name = 'schedule'

    def test_func(self):
        user = self.request.user
        schedule = self.get_object()
        
        if user.role == 'administrator':
            return True
        elif user.role == 'doctor':
            # Check if this doctor's reception is on the schedule.
            return schedule.receptions.filter(doctor__employee__user=user).exists()
        elif user.role == 'patient':
            # Check if this patient's reception is on the schedule.
            return schedule.receptions.filter(patient=user).exists()
        return False
