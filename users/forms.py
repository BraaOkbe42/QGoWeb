from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser , Business


class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


from django import forms

class BusinessForm(forms.Form):
    business_name = forms.CharField(max_length=255)
    branch_name = forms.CharField(max_length=255)
    hours_of_operation = forms.CharField(max_length=50)  # Example: "8:00 to 17:00"
    working_days = forms.CharField(max_length=50)        # Example: "Monday to Friday"
