from django.contrib import admin
from django.db import models
from django.forms import DateInput, DateTimeInput, TimeInput


_original = admin.ModelAdmin.formfield_for_dbfield


def _patched(self, db_field, request, **kwargs):
    field = _original(self, db_field, request, **kwargs)
    if field and field.widget:
        if isinstance(db_field, models.DateTimeField):
            field.widget = DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            )
        elif isinstance(db_field, models.DateField):
            field.widget = DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d',
            )
        elif isinstance(db_field, models.TimeField):
            field.widget = TimeInput(
                attrs={'type': 'time'},
                format='%H:%M',
            )
    return field


admin.ModelAdmin.formfield_for_dbfield = _patched
