from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Document

# Create your views here.
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'administrator'


class DocumentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Document
    template_name = 'documents/list.html'
    context_object_name = 'page_obj'
    paginate_by = 10


class DocumentDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'doc'


class DocumentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Document
    template_name = 'documents/create.html'
    fields = ['content', 'formation_date']
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        form.instance.administrator = self.request.user.employee_profile.administrator_profile
        return super().form_valid(form)


class DocumentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Document
    template_name = 'documents/create.html'
    fields = ['content', 'formation_date']
    context_object_name = 'doc'

    def get_success_url(self):
        return reverse_lazy('documents:detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Document
    success_url = reverse_lazy('documents:list')

    # No separate template needed — use modal in detail.html
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
