from django import forms
from .models import Zone, Device


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ["name", "organization"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la zona"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return name

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        # ⚠️ Importante: usar serial_number y max_power_w (ambos existen en tu modelo)
        fields = [
            "name",
            "serial_number",
            "product",
            "zone",
            "organization",
            "max_power_w",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "product": forms.Select(attrs={"class": "form-select"}),
            "zone": forms.Select(attrs={"class": "form-select"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "max_power_w": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "1"}),
        }