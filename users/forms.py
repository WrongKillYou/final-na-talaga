from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Child, User, Parent, Teacher

class StudentLoginForm(forms.Form):
    """Student login using LRN (Learner Reference Number)"""
    lrn = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your LRN'
        })
    )

    def clean_lrn(self):
        lrn = self.cleaned_data.get('lrn')
        if not Child.objects.filter(lrn=lrn).exists():
            raise forms.ValidationError("Invalid LRN. Please check and try again.")
        return lrn


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

class TeacherProfileUpdateForm(forms.ModelForm):
    """Form for teachers to update their profile"""
    class Meta:
        model = Teacher
        fields = ['contact_number', 'address', 'photo']  # only actual fields
        widgets = {
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your address'
            }),
            'photo': forms.FileInput(attrs={'class': 'form-control'})
        }

        



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


class StudentProfileUpdateForm(forms.ModelForm):
    """Form for students to update their profile"""
    class Meta:
        model = Child
        fields = ['photo', 'address']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your address'
            })
        }


class ParentProfileUpdateForm(forms.ModelForm):
    """Form for parents to update their profile"""
    class Meta:
        model = Parent
        fields = ['parent_email', 'parent_contact', 'occupation', 'workplace']
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
            })
        }