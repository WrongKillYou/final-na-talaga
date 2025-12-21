from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    """Extended user model with role-based access - Parent, Teacher, Admin only"""
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    
    # Fix related_name conflicts
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_parent(self):
        return self.role == 'parent'
    
    def is_admin(self):
        return self.role == 'admin'


class Teacher(models.Model):
    """Teacher profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    license_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    
    # Personal info (from first project)
    sex = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female')], 
        blank=True
    )
    birth_date = models.DateField(null=True, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photos/teacher_photos/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"
    
    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        ordering = ['user__last_name', 'user__first_name']


class Parent(models.Model):
    """Parent profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    
    # Contact info
    parent_email = models.EmailField()
    parent_contact = models.CharField(max_length=50)
    
    # Additional info
    occupation = models.CharField(max_length=100, blank=True)
    workplace = models.CharField(max_length=200, blank=True)
    
    # Personal info
    sex = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female')], 
        blank=True
    )
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photos/parent_photos/', blank=True, null=True)
    
    # Emergency Contact
    emergency_contact = models.CharField(max_length=20, blank=True)
    relationship_to_child = models.CharField(
        max_length=50,
        blank=True,
        help_text="Father, Mother, Guardian, etc."
    )
    
    is_primary_contact = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"
    
    def get_children(self):
        """Get all children associated with this parent"""
        return self.children.all()
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
        ordering = ['user__last_name', 'user__first_name']


class Child(models.Model):
    """
    Child/Student record - NOT a User (children don't log in)
    Parents and Teachers manage their data
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    GRADE_CHOICES = [
        ('kindergarten', 'Kindergarten'),
        ('grade_1', 'Grade 1'),
        ('grade_2', 'Grade 2'),
        ('grade_3', 'Grade 3'),
        ('grade_4', 'Grade 4'),
        ('grade_5', 'Grade 5'),
        ('grade_6', 'Grade 6'),
        ('grade_7', 'Grade 7'),
        ('grade_8', 'Grade 8'),
        ('grade_9', 'Grade 9'),
        ('grade_10', 'Grade 10'),
        ('grade_11', 'Grade 11'),
        ('grade_12', 'Grade 12'),
    ]
    
    # Basic Information
    lrn = models.CharField("Learner Reference Number", max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200, blank=True)
    
    # Academic Information
    grade_level = models.CharField(max_length=20, choices=GRADE_CHOICES)
    section = models.CharField(max_length=50)
    enrollment_date = models.DateField()
    
    # Parent Relationship (Many-to-Many: child can have multiple parents)
    parents = models.ManyToManyField(Parent, related_name='children')
    
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
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # Contact Info (for emergencies)
    address = models.TextField(blank=True)
    
    # Photo
    photo = models.ImageField(upload_to='photos/student_photos/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.lrn}"
    
    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"
        ordering = ['grade_level', 'section', 'last_name', 'first_name']