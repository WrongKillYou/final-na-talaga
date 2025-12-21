from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Parent

class ParentLoginForm(forms.Form):
    """Parent login with username and password"""
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username=username, role='parent').exists():
            raise forms.ValidationError("Invalid username or not a parent account.")
        return username


class TeacherLoginForm(forms.Form):
    """Teacher login with username and password"""
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username=username, role='teacher').exists():
            raise forms.ValidationError("Invalid username or not a teacher account.")
        return username


class TeacherPasswordChangeForm(PasswordChangeForm):
    """Custom password change form for teachers"""
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter old password'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )


class ParentPasswordChangeForm(PasswordChangeForm):
    """Custom password change form for parents"""
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter old password'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )


class ParentProfileUpdateForm(forms.ModelForm):
    """Form for parents to update their profile"""
    class Meta:
        model = Parent
        fields = ['parent_email', 'parent_contact', 'occupation', 'workplace', 'photo']
        widgets = {
            'parent_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'parent_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your occupation'
            }),
            'workplace': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your workplace'
            }),
            'photo': forms.FileInput(attrs={'class': 'form-control'})
        }