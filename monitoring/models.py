from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Child, Teacher


# ========================================
# CLASS & ENROLLMENT (from first project)
# ========================================

class Class(models.Model):
    """Class/Subject - taught by a teacher"""
    class_name = models.CharField(max_length=255, help_text="e.g., 9-Sapphire Math")
    subject = models.CharField(max_length=255)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='classes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_name} - {self.subject}"
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"


class Enrollment(models.Model):
    """Students enrolled in a class"""
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='enrollments')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrollments')
    
    enrolled_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'class_obj')
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.class_obj}"


# ========================================
# GRADING SYSTEM (from first project)
# ========================================

class GradingScheme(models.Model):
    """Grading weights per class (from first project)"""
    class_obj = models.OneToOneField(Class, on_delete=models.CASCADE, related_name='grading_scheme')
    written_work_weight = models.FloatField(default=0.4, help_text="Default: 0.4 (40%)")
    performance_task_weight = models.FloatField(default=0.4, help_text="Default: 0.4 (40%)")
    quarterly_assessment_weight = models.FloatField(default=0.2, help_text="Default: 0.2 (20%)")

    def __str__(self):
        return f"Grading Scheme for {self.class_obj}"
    
    class Meta:
        verbose_name = "Grading Scheme"
        verbose_name_plural = "Grading Schemes"


class GradeItem(models.Model):
    """Individual grade components (from first project)"""
    COMPONENT_CHOICES = [
        ('WW', 'Written Work'),
        ('PT', 'Performance Task'),
        ('QA', 'Quarterly Assessment'),
    ]

    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='grade_items')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='grade_items')
    component = models.CharField(max_length=2, choices=COMPONENT_CHOICES)
    score = models.FloatField()
    highest_possible_score = models.FloatField()
    quarter = models.PositiveSmallIntegerField(default=1, help_text="1 to 4")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def percentage_score(self):
        """Get percentage score"""
        if self.highest_possible_score == 0:
            return 0.0
        return (self.score / self.highest_possible_score) * 100

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.get_component_display()} - Q{self.quarter}"
    
    class Meta:
        verbose_name = "Grade Item"
        verbose_name_plural = "Grade Items"
        ordering = ['quarter', 'student', 'component']


class FinalGrade(models.Model):
    """Final computed grade per quarter (from first project)"""
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='final_grades')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='final_grades')
    quarter = models.PositiveSmallIntegerField(default=1, help_text="1 to 4")
    final_grade = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'class_obj', 'quarter')
        verbose_name = "Final Grade"
        verbose_name_plural = "Final Grades"

    def compute_final_grade(self):
        """Compute weighted final grade (from first project logic)"""
        items = GradeItem.objects.filter(
            student=self.student,
            class_obj=self.class_obj,
            quarter=self.quarter
        )
        
        scheme = self.class_obj.grading_scheme

        total_scores = {'WW': 0, 'PT': 0, 'QA': 0}
        total_highest = {'WW': 0, 'PT': 0, 'QA': 0}

        for item in items:
            total_scores[item.component] += item.score
            total_highest[item.component] += item.highest_possible_score

        def weighted(component, weight):
            if total_highest[component] == 0:
                return 0
            percent = (total_scores[component] / total_highest[component]) * 100
            return percent * weight

        final = sum([
            weighted('WW', scheme.written_work_weight),
            weighted('PT', scheme.performance_task_weight),
            weighted('QA', scheme.quarterly_assessment_weight),
        ])

        self.final_grade = round(final, 2)
        self.save()
        return self.final_grade

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.class_obj} - Q{self.quarter} = {self.final_grade or 'N/A'}"


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
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    
    # Time tracking (from first project)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    
    # Class-specific attendance (required)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendances')
    
    # Additional info
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_absent(self):
        """Check if student was absent"""
        return self.status == 'absent'
    
    def is_present(self):
        """Check if student was present"""
        return self.status == 'present'
    
    def __str__(self):
        return f"{self.child.get_full_name()} - {self.date} - {self.status}"
    
    class Meta:
        unique_together = ('child', 'date')
        ordering = ['-date']
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"


class ClassSession(models.Model):
    """Class session management (from first project)"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    is_active = models.BooleanField(default=False, help_text="True when class is ongoing")

    class Meta:
        unique_together = ('class_obj', 'date', 'class_obj')
        verbose_name = "Class Session"
        verbose_name_plural = "Class Sessions"

    def __str__(self):
        return f"{self.class_obj} on {self.date} ({'Ongoing' if self.is_active else 'Closed'})"


# ========================================
# ATTENDANCE SUMMARY
# ========================================

class AttendanceSummary(models.Model):
    """Monthly attendance summary for quick reports"""
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendance_summaries')
    month = models.DateField(help_text="First day of the month")
    
    total_days = models.PositiveIntegerField(default=0)
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    late_days = models.PositiveIntegerField(default=0)
    excused_days = models.PositiveIntegerField(default=0)
    
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_percentage(self):
        """Calculate attendance percentage"""
        if self.total_days > 0:
            self.attendance_percentage = (self.present_days / self.total_days) * 100
        return self.attendance_percentage
    
    def __str__(self):
        return f"{self.child.get_full_name()} - {self.month.strftime('%B %Y')}"
    
    class Meta:
        unique_together = ('child', 'month')
        ordering = ['-month']
        verbose_name = "Attendance Summary"
        verbose_name_plural = "Attendance Summaries"