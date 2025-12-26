# users/models.py
# CLEANED VERSION - Minor improvements for kindergarten system

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    """
    Extended user model with role-based access
    Only Parent and Teacher accounts can log in
    Admin uses Django's default admin interface
    """
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', 
        null=True, 
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    
    # Fix related_name conflicts with Django's default User
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions'
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_parent(self):
        return self.role == 'parent'
    
    def is_admin(self):
        return self.role == 'admin'


class Teacher(models.Model):
    """Teacher profile with additional information"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile'
    )
    
    # Professional Info
    license_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Professional Teacher's License Number"
    )
    department = models.CharField(
        max_length=100,
        default='Kindergarten'
    )
    specialization = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., Early Childhood Education"
    )
    
    # Personal Info
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        blank=True
    )
    birth_date = models.DateField(null=True, blank=True)
    
    # Contact Info
    contact_email = models.EmailField(blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Profile Photo
    photo = models.ImageField(
        upload_to='photos/teacher_photos/', 
        blank=True, 
        null=True
    )
    
    # Employment Info
    date_hired = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department}"


class Parent(models.Model):
    """Parent/Guardian profile"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Legal Guardian'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='parent_profile'
    )
    
    # Personal Info
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        blank=True
    )
    birth_date = models.DateField(null=True, blank=True)
    
    # Contact Info
    parent_email = models.EmailField()
    parent_contact = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    
    # Emergency Contact
    emergency_contact = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Alternative contact number"
    )
    relationship_to_child = models.CharField(
        max_length=50,
        choices=RELATIONSHIP_CHOICES,
        default='parent',
        help_text="Relationship to enrolled child(ren)"
    )
    
    # Employment Info (optional)
    occupation = models.CharField(max_length=100, blank=True)
    workplace = models.CharField(max_length=200, blank=True)
    work_contact = models.CharField(max_length=50, blank=True)
    
    # Profile Photo
    photo = models.ImageField(
        upload_to='photos/parent_photos/', 
        blank=True, 
        null=True
    )
    
    # Primary contact flag
    is_primary_contact = models.BooleanField(
        default=True,
        help_text="Primary contact for school communications"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"
    
    def get_children(self):
        """Get all children associated with this parent"""
        return self.children.filter(is_active=True)


class Child(models.Model):
    """
    Child/Student record - NOT a User account
    Children don't log in; Parents and Teachers manage their data
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    # Basic Information
    lrn = models.CharField(
        "Learner Reference Number", 
        max_length=50, 
        unique=True
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(
        max_length=10, 
        blank=True,
        help_text="e.g., Jr., III"
    )
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200, blank=True)
    
    # Academic Information
    grade_level = models.CharField(
        max_length=20,
        default='kindergarten'
    )
    section = models.CharField(
        max_length=50,
        blank=True,
        help_text="Class section"
    )
    enrollment_date = models.DateField()
    
    # Parent Relationship (Many-to-Many: child can have multiple parents/guardians)
    parents = models.ManyToManyField(
        Parent, 
        related_name='children'
    )
    
    # Class Teacher (Homeroom/Adviser)
    class_teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='advisory_students'
    )
    
    # Medical Information
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(
        blank=True,
        help_text="List any known allergies"
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text="Any medical conditions to be aware of"
    )
    medications = models.TextField(
        blank=True,
        help_text="Regular medications being taken"
    )
    
    # Contact Info
    address = models.TextField(blank=True)
    
    # Photo
    photo = models.ImageField(
        upload_to='photos/student_photos/', 
        null=True, 
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False when student graduates or transfers"
    )
    
    # Additional Notes
    special_needs = models.TextField(
        blank=True,
        help_text="Any special educational needs or accommodations"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the child"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['lrn']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.lrn}"
    
    def get_full_name(self):
        """Return child's full name"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return ' '.join(parts)
    
    def get_age(self):
        """Calculate current age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_primary_parent(self):
        """Get primary contact parent"""
        primary = self.parents.filter(is_primary_contact=True).first()
        return primary if primary else self.parents.first()