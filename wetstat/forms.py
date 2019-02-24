import datetime

from django import forms
from django.core.exceptions import ValidationError


class CustomPlotForm(forms.Form):
    start_date = forms.DateTimeField(help_text="Startdatum", label="Start")
    end_date = forms.DateTimeField(help_text="Enddatum", label="Ende", initial=datetime.datetime.now())

    def clean_start_date(self):
        d = self.cleaned_data["start_date"]

        if d > datetime.datetime.now():
            raise ValidationError("Start liegt in der Zukunft!")

        return d

    def clean_end_date(self):
        d = self.cleaned_data["end_date"]

        if d > datetime.datetime.now():
            raise ValidationError("Ende liegt in der Zukunft!")

        return d
