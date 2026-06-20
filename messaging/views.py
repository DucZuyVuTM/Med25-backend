from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django import forms

from accounts.models import Administrator, CustomUser
from .forms import MessageForm
from .models import Email, Message

# Create your views here.
class AdminOrPatientRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('administrator', 'patient')


class EmailCreateView(LoginRequiredMixin, AdminOrPatientRequiredMixin, View):
    template_name = 'messaging/create.html'

    def get_form(self, user):
        form = forms.Form()

        if user.role == 'administrator':
            form.fields['patient'] = forms.ModelChoiceField(
                queryset=CustomUser.objects.filter(role='patient'),
                label='Patient',
            )
        elif user.role == 'patient':
            form.fields['administrator'] = forms.ModelChoiceField(
                queryset=Administrator.objects.select_related('employee'),
                label='Administrator',
            )

        return form

    def get(self, request):
        form = self.get_form(request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        user = request.user

        if user.role == 'administrator':
            patient_id = request.POST.get('patient')
            try:
                patient = CustomUser.objects.get(pk=patient_id, role='patient')
                email, created = Email.objects.get_or_create(
                    administrator=user.employee_profile.administrator_profile,
                    patient=patient,
                    defaults={'status': 'open'},
                )
                return redirect(reverse_lazy('messaging:thread', kwargs={'pk': email.pk}))
            except (CustomUser.DoesNotExist, ValueError):
                pass

        elif user.role == 'patient':
            administrator_id = request.POST.get('administrator')
            try:
                administrator = Administrator.objects.get(pk=administrator_id)
                email, created = Email.objects.get_or_create(
                    administrator=administrator,
                    patient=user,
                    defaults={'status': 'open'},
                )
                return redirect(reverse_lazy('messaging:thread', kwargs={'pk': email.pk}))
            except (Administrator.DoesNotExist, ValueError):
                pass

        return render(request, self.template_name, {'form': self.get_form(user)})


class InboxView(LoginRequiredMixin, AdminOrPatientRequiredMixin, ListView):
    model = Email
    template_name = 'messaging/inbox.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'administrator':
            return Email.objects.filter(
                administrator__employee__user=user
            ).select_related('patient')
        elif user.role == 'patient':
            return Email.objects.filter(
                patient=user
            ).select_related('administrator__employee')
        return Email.objects.none()


class ThreadView(LoginRequiredMixin, DetailView):
    model = Email
    template_name = 'messaging/thread.html'
    context_object_name = 'thread'

    def dispatch(self, request, *args, **kwargs):
        thread = self.get_object()
        user = request.user

        if user.role == 'patient':
            if thread.patient != user:
                raise PermissionDenied("You don't have permission to view this conversation.")

        elif user.role == 'administrator':
            if thread.administrator.employee.user != user:
                raise PermissionDenied("You don't have permission to view this conversation.")

        else:
            raise PermissionDenied("You don't have permission to view this conversation.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MessageForm()
        return context

    def post(self, request, *args, **kwargs):
        thread = self.get_object()
        form = MessageForm(request.POST)
        if form.is_valid():
            sender_type = 'admin' if request.user.role == 'administrator' else 'patient'
            from django.utils import timezone
            now = timezone.now()
            Message.objects.create(
                email=thread,
                content=form.cleaned_data['content'],
                send_date=now.date(),
                send_time=now.time(),
                sender_type=sender_type,
            )
        return self.get(request, *args, **kwargs)
