from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django import forms
from .models import User, Teacher, Parent, Child

# ========================================
# Admin Site Customization
# ========================================
admin.site.site_header = "School Monitor Admin"
admin.site.site_title = "School Portal Admin"
admin.site.index_title = "Welcome to the Admin Panel"


# ========================================
# Custom Forms for Creating Profiles with User
# ========================================

class TeacherCreationForm(forms.ModelForm):
    """Form for creating Teacher with associated User account"""
    # User fields
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = Teacher
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Editing: fill user fields from related user
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['password'].help_text = "Leave blank if you don't want to change the password."

        # Field order
        user_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        teacher_fields = [f for f in self.fields if f not in user_fields]
        self.order_fields(user_fields + teacher_fields)

    def save(self, commit=True):
        teacher = super().save(commit=False)

        if not teacher.user_id:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                role='teacher'
            )
        else:
            # Update existing user
            user = teacher.user
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            user.save()

        teacher.user = user
        if commit:
            teacher.save()
        return teacher


class ParentCreationForm(forms.ModelForm):
    """Form for creating Parent with associated User account"""
    # User fields
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = Parent
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Editing: fill user fields from related user
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['password'].help_text = "Leave blank if you don't want to change the password."

        # Field order
        user_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        parent_fields = [f for f in self.fields if f not in user_fields]
        self.order_fields(user_fields + parent_fields)

    def save(self, commit=True):
        parent = super().save(commit=False)

        if not parent.user_id:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                role='parent'
            )
        else:
            # Update existing user
            user = parent.user
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            user.save()

        parent.user = user
        if commit:
            parent.save()
        return parent


# ========================================
# Custom Admin Classes
# ========================================

class TeacherAdmin(admin.ModelAdmin):
    form = TeacherCreationForm
    list_display = ('get_full_name', 'license_number', 'department', 'contact_number', 'is_active')
    list_filter = ('department', 'is_active', 'gender')
    search_fields = ('user__username', 'license_number', 'user__first_name', 'user__last_name')
    
    fieldsets = (
        ('User Account', {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Teacher Information', {
            'fields': ('license_number', 'department')
        }),
        ('Personal Information', {
            'fields': ('gender', 'birth_date', 'contact_email', 'contact_number', 'photo')
        }),
        ('Additional Info', {
            'fields': ('address', 'is_active')
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Teacher Name'


class ParentAdmin(admin.ModelAdmin):
    form = ParentCreationForm
    list_display = ('get_full_name', 'parent_email', 'parent_contact', 'is_primary_contact')
    list_filter = ('is_primary_contact', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'parent_email')
    
    fieldsets = (
        ('User Account', {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Parent Information', {
            'fields': ('parent_email', 'parent_contact', 'relationship_to_child', 'is_primary_contact')
        }),
        ('Personal Information', {
            'fields': ('gender', 'birth_date', 'photo')
        }),
        ('Work Information', {
            'fields': ('occupation', 'workplace')
        }),
        ('Additional Info', {
            'fields': ('address', 'emergency_contact')
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Parent Name'


class ChildAdmin(admin.ModelAdmin):
    """Admin for Child model"""
    list_display = ('get_full_name', 'lrn', 'grade_level', 'section', 'class_teacher', 'is_active')
    list_filter = ('grade_level', 'section', 'is_active', 'gender')
    search_fields = ('lrn', 'first_name', 'last_name')
    filter_horizontal = ('parents',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lrn', 'first_name', 'middle_name', 'last_name')
        }),
        ('Personal Information', {
            'fields': ('gender', 'date_of_birth', 'place_of_birth', 'photo')
        }),
        ('Academic Information', {
            'fields': ('grade_level', 'section', 'enrollment_date', 'class_teacher')
        }),
        ('Parents/Guardians', {
            'fields': ('parents',)
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'allergies', 'medical_conditions'),
            'classes': ('collapse',)
        }),
        ('Contact Info', {
            'fields': ('address',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


# ========================================
# Register Models
# ========================================

# Optional: hide default User, Group, and Permission from admin
# Uncomment if you want to hide them
# for model in [User, Group, Permission]:
#     try:
#         admin.site.unregister(model)
#     except admin.sites.NotRegistered:
#         pass

# Register custom user management
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(Child, ChildAdmin)