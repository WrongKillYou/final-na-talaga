# information/forms.py
from django import forms
from .models import Announcement, Event

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title',
            'content',
            'category',
            'priority',
            'target_audience',
            'expiry_date',
            'attachment',
            
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement details...',
                'rows': 6
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'target_audience': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'all, parents, teachers, or specific grades',
                'value': 'all'
            }),
            'expiry_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
        }
    
    # Custom non-model fields
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Banner Image (Optional)',
        help_text='Upload an image to display with the announcement'
    )
    
    is_active = forms.BooleanField(
        required=False,  # Not required so form is still valid if unchecked
        initial=True,    # Default to checked/True
        label='Publish immediately',
        help_text='Uncheck to save as draft'
    )
    
    is_pinned = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pin to top',
        help_text='Keep this announcement at the top of the list'
    )
    
    send_notification = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Send notification to users',
        help_text='Notify target audience about this announcement'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set field properties
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['expiry_date'].required = False
        self.fields['attachment'].required = False
        
        # Set initial values for new forms
        if not self.instance.pk:
            self.fields['target_audience'].initial = 'all'
            self.fields['priority'].initial = 'normal'
            self.fields['category'].initial = 'general'
    
    def clean_attachment(self):
        """Validate attachment file size"""
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('File size must be less than 5MB')
        return attachment
    
    def clean_image(self):
        """Validate image file size"""
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Image size must be less than 5MB')
        return image
    
    def clean_target_audience(self):
        """Ensure target_audience has a value"""
        target = self.cleaned_data.get('target_audience', '').strip()
        if not target:
            return 'all'
        return target
    

from django import forms
from .models import Event
from datetime import datetime
from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_datetime', 'end_datetime',
            'location', 'venue_details', 'target_audience',
            'is_public', 'is_active', 'is_cancelled',
            'image', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'venue_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_audience': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')

        if not start or not end:
            raise forms.ValidationError("Start and end date/time are required.")

        if end < start:
            raise forms.ValidationError("End date/time cannot be before start date/time.")

        return cleaned_data
