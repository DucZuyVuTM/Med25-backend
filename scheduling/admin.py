from django.contrib import admin
from .models import Schedule, Reception

# Register your models here.
class ReceptionInline(admin.TabularInline):
    model = Reception
    extra = 0
    show_change_link = True
    fields = ('doctor', 'patient', 'medical_card', 'clinic_equipment', 'document', 'status')
    autocomplete_fields = ('doctor', 'patient', 'medical_card', 'clinic_equipment', 'document')
    verbose_name_plural = 'Reception'


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'administrator', 'reception_start_time',
        'reception_end_time', 'reception_place', 'reception_count'
    )
    search_fields = (
        'reception_place',
        'administrator__employee__first_name',
        'administrator__employee__last_name',
    )
    list_filter = ('reception_start_time', 'administrator')
    ordering = ('-reception_start_time',)
    inlines = [ReceptionInline]

    def reception_count(self, obj):
        return obj.receptions.count()
    reception_count.short_description = 'Reception amount'


@admin.register(Reception)
class ReceptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_patient', 'get_doctor',
        'get_schedule_time', 'status'
    )
    search_fields = (
        'patient__first_name', 'patient__last_name',
        'doctor__employee__first_name', 'doctor__employee__first_name',
    )
    list_filter = ('status', 'schedule__reception_start_time')
    ordering = ('-schedule__reception_start_time',)
    autocomplete_fields = ('doctor', 'patient', 'medical_card', 'document', 'schedule')
    fieldsets = (
        ('Reception information', {
            'fields': ('doctor', 'patient', 'medical_card', 'schedule', 'clinic_equipment', 'document')
        }),
        ('Result', {
            'fields': ('result', 'prescription', 'status')
        }),
    )

    def get_patient(self, obj):
        return obj.patient.full_name
    get_patient.short_description = 'Patient'

    def get_doctor(self, obj):
        return obj.doctor.employee.full_name
    get_doctor.short_description = 'Doctor'

    def get_schedule_time(self, obj):
        return obj.schedule.reception_start_time
    get_schedule_time.short_description = 'Schedule time'
