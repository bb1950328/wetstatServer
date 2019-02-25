import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import DateTimeField, BooleanField


class CustomPlotForm(forms.Form):
    formats = ["%Y-%m-%dT%H:%M"]

    start_date = DateTimeField(label="Start", input_formats=formats,
                               widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format="%Y-%m-%dT%H:%M"))  #

    end_date = DateTimeField(label="Ende", initial=datetime.datetime.now(), input_formats=formats,
                             widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format="%Y-%m-%dT%H:%M"))

    use_minmaxavg = BooleanField(label="Min-Max-Mittel pro Tag verwenden", initial=False, required=False)

    def clean_start_date(self):
        d = self.cleaned_data["start_date"]
        d = d.replace(tzinfo=None)
        if d > datetime.datetime.now():
            raise ValidationError("Start liegt in der Zukunft!")

        return d

    def clean_end_date(self):
        d = self.cleaned_data["end_date"]
        d = d.replace(tzinfo=None)
        if d > datetime.datetime.now():
            raise ValidationError("Ende liegt in der Zukunft!")

        return d

    def clean_use_minmaxavg(self):
        # cleaning booleans doesn't make sense ;-)
        return self.cleaned_data["use_minmaxavg"]
