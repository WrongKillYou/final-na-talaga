from django.contrib import admin
from django import forms
from users.models import Child
from .models import (
    Class, Enrollment, Attendance, AttendanceSummary,
    Domain, Competency, QuarterlyCompetencyRecord
)

# ========================================
# Class & Enrollment Admin
# ========================================

class ClassWithExtrasForm(forms.ModelForm):
    """Form to manage Class + Enrollment (ECCD system)"""

    enrolled_students = forms.ModelMultipleChoiceField(
        queryset=Child.objects.filter(is_active=True),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Students", is_stacked=False),
    )

    class Meta:
        model = Class
        fields = [
            'class_name',
            'grade_level',
            'school_year',
            'teacher',
            'room_number',
            'schedule',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['enrolled_students'].initial = Child.objects.filter(
                enrollments__class_obj=self.instance
            )

    def save(self, commit=True):
        class_instance = super().save(commit=False)
        class_instance.save()

        selected_students = set(self.cleaned_data.get('enrolled_students', []))
        current_enrollments = Enrollment.objects.filter(class_obj=class_instance)
        current_students = {e.student for e in current_enrollments}

        for enrollment in current_enrollments:
            if enrollment.student not in selected_students:
                enrollment.delete()

        for student in selected_students - current_students:
            Enrollment.objects.create(student=student, class_obj=class_instance)

        return class_instance


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    form = ClassWithExtrasForm

    list_display = (
        'class_name',
        'grade_level',
        'school_year',
        'teacher',
        'student_count',
        'is_active',
    )
    list_filter = ('grade_level', 'school_year', 'teacher', 'is_active')
    search_fields = ('class_name', 'school_year', 'teacher__user__last_name')

    fieldsets = (
        ('Class Information', {
            'fields': (
                'class_name',
                'grade_level',
                'school_year',
                'teacher',
                'room_number',
                'schedule',
                'is_active',
            )
        }),
        ('Enroll Students', {
            'fields': ('enrolled_students',),
        }),
    )

    def student_count(self, obj):
        return obj.get_student_count()

    student_count.short_description = 'Enrolled Students'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'enrolled_date', 'is_active')
    list_filter = ('class_obj', 'is_active')
    search_fields = ('student__first_name', 'student__last_name', 'student__lrn')
    raw_id_fields = ('student', 'class_obj')


# ========================================
# ECCD Competency Admin
# ========================================

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'domain', 'order')
    list_filter = ('domain',)
    search_fields = ('code', 'description')
    ordering = ('domain__order', 'order')


@admin.register(QuarterlyCompetencyRecord)
class QuarterlyCompetencyRecordAdmin(admin.ModelAdmin):
    list_display = ('child', 'competency', 'quarter', 'level', 'recorded_by')
    list_filter = ('quarter', 'competency__domain', 'level')
    search_fields = ('child__first_name', 'child__last_name')
    raw_id_fields = ('child', 'competency', 'recorded_by')


# ========================================
# Attendance Admin
# ========================================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('child', 'date', 'class_obj', 'status', 'recorded_by')
    list_filter = ('status', 'date', 'class_obj')
    search_fields = ('child__first_name', 'child__last_name', 'child__lrn')
    date_hierarchy = 'date'
    raw_id_fields = ('child', 'class_obj', 'recorded_by')


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'child',
        'month',
        'class_obj',
        'total_days',
        'present_days',
        'absent_days',
        'attendance_percentage',
    )
    list_filter = ('month', 'class_obj')
    date_hierarchy = 'month'
    readonly_fields = ('attendance_percentage', 'created_at', 'updated_at')
