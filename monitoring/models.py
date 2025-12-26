# monitoring/models.py
# CLEANED AND CORRECTED FOR KINDERGARTEN COMPETENCY-BASED SYSTEM

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from users.models import Child, Teacher


# ========================================
# CLASS & ENROLLMENT
# ========================================

class Class(models.Model):
    """Class/Section - managed by a teacher"""
    class_name = models.CharField(
        max_length=255, 
        help_text="e.g., Kindergarten - Section A"
    )
    grade_level = models.CharField(
        max_length=50,
        default='kindergarten',
        help_text="Grade level (typically 'kindergarten' for this system)"
    )
    school_year = models.CharField(
        max_length=20,
        help_text="e.g., 2024-2025"
    )
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='classes'
    )
    
    # Class schedule info (optional)
    room_number = models.CharField(max_length=50, blank=True)
    schedule = models.TextField(
        blank=True,
        help_text="Class schedule details"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_name} - SY {self.school_year}"
    
    def get_student_count(self):
        return self.enrollments.count()
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ['-school_year', 'class_name']


class Enrollment(models.Model):
    """Students enrolled in a class"""
    student = models.ForeignKey(
        Child, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    
    enrolled_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'class_obj')
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        ordering = ['student__last_name', 'student__first_name']

    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.class_obj}"


# ========================================
# COMPETENCY FRAMEWORK
# ========================================

class Domain(models.Model):
    """
    Learning/Development domains based on Kindergarten Framework
    e.g., Health & Motor Development, Socio-Emotional Development, etc.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in reports"
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Domain"
        verbose_name_plural = "Domains"

    def __str__(self):
        return self.name


class Competency(models.Model):
    """
    Fixed competencies under each domain
    Based on the Kindergarten Framework document provided
    """
    domain = models.ForeignKey(
        Domain, 
        on_delete=models.CASCADE, 
        related_name='competencies'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique competency code (e.g., HW-1, SE-2)"
    )
    description = models.TextField(
        help_text="Full competency description"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within domain"
    )

    class Meta:
        ordering = ['domain__order', 'order', 'code']
        verbose_name = "Competency"
        verbose_name_plural = "Competencies"

    def __str__(self):
        return f"{self.code} - {self.description[:50]}"


class QuarterlyCompetencyRecord(models.Model):
    """
    Stores B/D/C marking per quarter for a child per competency
    This is the core grading record for kindergarten
    """
    class QuarterChoices(models.IntegerChoices):
        Q1 = 1, _('Quarter 1')
        Q2 = 2, _('Quarter 2')
        Q3 = 3, _('Quarter 3')
        Q4 = 4, _('Quarter 4')

    LEVEL_CHOICES = [
        ('B', 'Beginning'),
        ('D', 'Developing'),
        ('C', 'Consistent'),
    ]

    child = models.ForeignKey(
        Child, 
        on_delete=models.CASCADE, 
        related_name='competency_records'
    )
    competency = models.ForeignKey(
        Competency, 
        on_delete=models.CASCADE, 
        related_name='records'
    )
    quarter = models.PositiveSmallIntegerField(
        choices=QuarterChoices.choices
    )
    level = models.CharField(
        max_length=1, 
        choices=LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="B = Beginning, D = Developing, C = Consistent"
    )
    
    # Metadata
    recorded_by = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or observations"
    )
    recorded_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('child', 'competency', 'quarter')
        ordering = ['child', 'quarter', 'competency__domain__order', 'competency__order']
        verbose_name = "Quarterly Competency Record"
        verbose_name_plural = "Quarterly Competency Records"
        indexes = [
            models.Index(fields=['child', 'quarter']),
            models.Index(fields=['competency', 'quarter']),
        ]

    def __str__(self):
        return f"{self.child.get_full_name()} - {self.competency.code} - Q{self.quarter}: {self.level or 'Not Assessed'}"


class QuarterlySummary(models.Model):
    """
    Summary of a child's performance for a quarter
    Includes overall assessment and teacher remarks
    """
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='quarterly_summaries'
    )
    quarter = models.PositiveSmallIntegerField(
        choices=QuarterlyCompetencyRecord.QuarterChoices.choices
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='quarterly_summaries'
    )
    
    # Summary counts
    total_competencies = models.PositiveIntegerField(default=0)
    beginning_count = models.PositiveIntegerField(default=0)
    developing_count = models.PositiveIntegerField(default=0)
    consistent_count = models.PositiveIntegerField(default=0)
    
    # Teacher assessment
    teacher_remarks = models.TextField(
        blank=True,
        help_text="Overall remarks for this quarter"
    )
    recorded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('child', 'quarter', 'class_obj')
        ordering = ['child', 'quarter']
        verbose_name = "Quarterly Summary"
        verbose_name_plural = "Quarterly Summaries"

    def __str__(self):
        return f"{self.child.get_full_name()} - Q{self.quarter} Summary"
    
    def calculate_summary(self):
        """Calculate summary statistics from competency records"""
        records = QuarterlyCompetencyRecord.objects.filter(
            child=self.child,
            quarter=self.quarter
        )
        
        self.total_competencies = records.count()
        self.beginning_count = records.filter(level='B').count()
        self.developing_count = records.filter(level='D').count()
        self.consistent_count = records.filter(level='C').count()
        self.save()


# ========================================
# ATTENDANCE SYSTEM
# ========================================

class Attendance(models.Model):
    """Daily attendance tracking"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    child = models.ForeignKey(
        Child, 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    
    # Time tracking
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='present'
    )
    
    # Additional info
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('child', 'date', 'class_obj')
        ordering = ['-date']
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        indexes = [
            models.Index(fields=['child', '-date']),
            models.Index(fields=['date', 'class_obj']),
        ]
    
    def is_absent(self):
        return self.status == 'absent'
    
    def is_present(self):
        return self.status in ['present', 'late']
    
    def __str__(self):
        return f"{self.child.get_full_name()} - {self.date} - {self.status}"


class AttendanceSummary(models.Model):
    """Monthly attendance summary for quick reports"""
    child = models.ForeignKey(
        Child, 
        on_delete=models.CASCADE, 
        related_name='attendance_summaries'
    )
    month = models.DateField(
        help_text="First day of the month"
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    
    # Counts
    total_days = models.PositiveIntegerField(default=0)
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    late_days = models.PositiveIntegerField(default=0)
    excused_days = models.PositiveIntegerField(default=0)
    
    # Calculated field
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('child', 'month', 'class_obj')
        ordering = ['-month']
        verbose_name = "Attendance Summary"
        verbose_name_plural = "Attendance Summaries"
    
    def calculate_percentage(self):
        """Calculate attendance percentage"""
        if self.total_days > 0:
            self.attendance_percentage = round(
                (self.present_days / self.total_days) * 100, 2
            )
        else:
            self.attendance_percentage = 0
        return self.attendance_percentage
    
    def update_from_records(self):
        """Update summary from actual attendance records"""
        from django.db.models import Count, Q
        from datetime import timedelta
        
        # Get date range for this month
        start_date = self.month
        if self.month.month == 12:
            end_date = self.month.replace(year=self.month.year + 1, month=1, day=1)
        else:
            end_date = self.month.replace(month=self.month.month + 1, day=1)
        end_date = end_date - timedelta(days=1)
        
        # Query attendance records
        records = Attendance.objects.filter(
            child=self.child,
            date__gte=start_date,
            date__lte=end_date,
            class_obj=self.class_obj
        )
        
        # Update counts
        self.total_days = records.count()
        self.present_days = records.filter(status='present').count()
        self.absent_days = records.filter(status='absent').count()
        self.late_days = records.filter(status='late').count()
        self.excused_days = records.filter(status='excused').count()
        
        # Calculate percentage
        self.calculate_percentage()
        self.save()
    
    def __str__(self):
        return f"{self.child.get_full_name()} - {self.month.strftime('%B %Y')}"