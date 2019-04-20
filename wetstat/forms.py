# coding=utf-8
import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import DateTimeField, ChoiceField, Field

from wetstat.sensors import SensorMaster

sensor_choices = ["Nicht anzeigen", "Primärachse", "Sekundärachse", "MinMaxAvg Prim.", "MinMaxAvg Sek."]


def set_var(name: str, value: str):
    allowed = "abcdefghijklmnopqrstuvwxyzäöü1234567890_"
    allowed += allowed.upper()
    for c in name:
        if c not in allowed:
            raise ValueError("'" + c + "' in varable name isn't allowed!")
    if ";" in value:
        raise ValueError("There's a semicolon in the Value String!")


class CustomPlotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        formats = ["%Y-%m-%dT%H:%M"]

        start_date = DateTimeField(label="Start", input_formats=formats,
                                   widget=forms.DateTimeInput(attrs={'type': 'datetime-local'},
                                                              format="%Y-%m-%dT%H:%M"))  #

        end_date = DateTimeField(label="Ende", initial=datetime.datetime.now(), input_formats=formats,
                                 widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format="%Y-%m-%dT%H:%M"))

        # use_minmaxavg = BooleanField(label="Min-Max-Mittel pro Tag verwenden", initial=False, required=False)
        self.fields["start_date"] = start_date
        self.fields["end_date"] = end_date
        self.fields["test"] = ChoiceField(label="Test", required=False, widget=forms.Select(choices=sensor_choices))

        for i, sensor in enumerate(SensorMaster.ALL_SENSORS):
            name = sensor.get_long_name()
            field = Field(label=name, required=False)
            self.fields["sensor_" + str(i)] = field
        self.declared_fields = self.fields

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
