from django import forms
from .models import MaintenanceRequest
from .models import Student

from django import forms
from .models import MaintenanceRequest

from django import forms
from .models import MaintenanceRequest

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['description', 'location','status']

    def __init__(self, *args, **kwargs):
        super(MaintenanceRequestForm, self).__init__(*args, **kwargs)
        # Add CSS classes to the fields
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Describe the maintenance issue'})
        self.fields['location'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Location of the issue'})

from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'gender', 'school_class', 'date_of_birth', 'admission_date', 'residency_status']

# forms.py

from django import forms
from .models import Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'level', 'code', 'description', 'teacher']
from django import forms
from .models import IncidentReport

from django import forms
from .models import IncidentReport

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ['incident_type', 'description', 'location']
        widgets = {
            'incident_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

# in forms.py
from django import forms
from .models import Budget

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'allocated_amount', 'spent_amount', 'description']

from django import forms

from django import forms

class UploadClassListForm(forms.Form):
    csv_file = forms.FileField(label='Select a CSV file')




from django import forms
from django.contrib.auth.models import User
from main.models import UserProfile


class RegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label='Username')
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Role")

    class Meta:
        model = UserProfile
        fields = ['role']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def save(self, commit=True):
        # Create the user using `create_user`, which automatically hashes the password
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data["password1"]  # `create_user` will hash this
        )
        
        # Save the associated profile
        user_profile = super().save(commit=False)
        user_profile.user = user  # Link the profile to the user
        if commit:
            user_profile.save()
        
        return user_profile

from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date']  # Remove 'description' since it's no longer in the model

from django import forms
from .models import AttendanceImage

class AttendanceImageForm(forms.ModelForm):
    class Meta:
        model = AttendanceImage
        fields = ['teacher', 'class_name', 'attendance_date', 'uploaded_by', 'subject', 'remarks']  # Remove 'image'
