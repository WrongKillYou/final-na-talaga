from django.contrib import admin
from django import forms
from users.models import Child, Teacher
from .models import (
    Class, Enrollment, GradingScheme, 
    GradeItem, FinalGrade, 
    Attendance, ClassSession, AttendanceSummary
)


# ========================================
# Custom Form for Class Creation (from first project)
# ========================================

class ClassWithExtrasForm(forms.ModelForm):
    """Unified form for creating Class + GradingScheme + Enrollments"""
    
    # GradingScheme fields
    written_work_weight = forms.FloatField(initial=0.4, help_text="Default: 40%")
    performance_task_weight = forms.FloatField(initial=0.4, help_text="Default: 40%")
    quarterly_assessment_weight = forms.FloatField(initial=0.2, help_text="Default: 20%")

    # Enrollment selection
    enrolled_students = forms.ModelMultipleChoiceField(
        queryset=Child.objects.filter(is_active=True),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Students", is_stacked=False),
        help_text="Select students to enroll in this class"
    )

    class Meta:
        model = Class
        fields = ['class_name', 'subject', 'teacher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing existing Class, preselect currently enrolled students
        if self.instance.pk:
            self.fields['enrolled_students'].initial = Child.objects.filter(
                enrollments__class_obj=self.instance
            )
            
            # Load existing grading scheme
            try:
                scheme = self.instance.grading_scheme
                self.fields['written_work_weight'].initial = scheme.written_work_weight
                self.fields['performance_task_weight'].initial = scheme.performance_task_weight
                self.fields['quarterly_assessment_weight'].initial = scheme.quarterly_assessment_weight
            except GradingScheme.DoesNotExist:
                pass

    def save(self, commit=True):
        # Always get the instance but ensure it has a PK
        class_instance = super().save(commit=False)
        class_instance.save()  # Ensure it has a PK

        # Create or update GradingScheme
        GradingScheme.objects.update_or_create(
            class_obj=class_instance,
            defaults={
                'written_work_weight': self.cleaned_data['written_work_weight'],
                'performance_task_weight': self.cleaned_data['performance_task_weight'],
                'quarterly_assessment_weight': self.cleaned_data['quarterly_assessment_weight'],
            }
        )

        # Update enrollments
        selected_students = set(self.cleaned_data.get('enrolled_students', []))
        current_enrollments = set(Enrollment.objects.filter(class_obj=class_instance))
        current_students = {e.student for e in current_enrollments}

        # Remove enrollments for students not in selected list
        for enrollment in current_enrollments:
            if enrollment.student not in selected_students:
                enrollment.delete()

        # Add new enrollments
        for student in selected_students - current_students:
            Enrollment.objects.create(student=student, class_obj=class_instance)

        return class_instance


# ========================================
# Admin Classes
# ========================================

class ClassAdmin(admin.ModelAdmin):
    form = ClassWithExtrasForm
    list_display = ('class_name', 'subject', 'teacher', 'enrolled_count', 'created_at')
    list_filter = ('teacher', 'subject')
    search_fields = ('class_name', 'subject', 'teacher__user__last_name')

    fieldsets = (
        ('Class Information', {
            'fields': ('class_name', 'subject', 'teacher')
        }),
        ('Grading Scheme', {
            'fields': ('written_work_weight', 'performance_task_weight', 'quarterly_assessment_weight'),
            'description': 'Set the weight for each component (must total to 1.0)'
        }),
        ('Enroll Students', {
            'fields': ('enrolled_students',)
        }),
    )

    def enrolled_count(self, obj):
        return obj.enrollments.count()
    enrolled_count.short_description = 'Enrolled Students'

    def save_model(self, request, obj, form, change):
        form.save()


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'enrolled_date')
    list_filter = ('class_obj', 'enrolled_date')
    search_fields = ('student__first_name', 'student__last_name', 'student__lrn')
    raw_id_fields = ('student', 'class_obj')


class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'written_work_weight', 'performance_task_weight', 'quarterly_assessment_weight')
    list_filter = ('class_obj__subject',)
    
    def has_add_permission(self, request):
        # Grading schemes are created automatically with Class
        return False


class GradeItemAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'component', 'score', 'highest_possible_score', 'quarter', 'percentage_score')
    list_filter = ('class_obj', 'component', 'quarter')
    search_fields = ('student__first_name', 'student__last_name', 'student__lrn')
    raw_id_fields = ('student', 'class_obj')
    
    fieldsets = (
        ('Student & Class', {
            'fields': ('student', 'class_obj', 'quarter')
        }),
        ('Grade Details', {
            'fields': ('component', 'score', 'highest_possible_score')
        }),
    )


class FinalGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'quarter', 'final_grade', 'updated_at')
    list_filter = ('class_obj', 'quarter')
    search_fields = ('student__first_name', 'student__last_name', 'student__lrn')
    raw_id_fields = ('student', 'class_obj')
    readonly_fields = ('final_grade', 'created_at', 'updated_at')
    
    actions = ['recompute_grades']
    
    def recompute_grades(self, request, queryset):
        """Action to recompute selected final grades"""
        count = 0
        for final_grade in queryset:
            final_grade.compute_final_grade()
            count += 1
        self.message_user(request, f'{count} grades recomputed successfully.')
    recompute_grades.short_description = 'Recompute selected final grades'


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('child', 'date', 'status', 'time_in', 'time_out', 'recorded_by')
    list_filter = ('status', 'date', 'class_obj')
    search_fields = ('child__first_name', 'child__last_name', 'child__lrn')
    date_hierarchy = 'date'
    raw_id_fields = ('child', 'class_obj', 'recorded_by')
    
    fieldsets = (
        ('Student & Date', {
            'fields': ('child', 'date', 'class_obj')
        }),
        ('Attendance Details', {
            'fields': ('status', 'time_in', 'time_out')
        }),
        ('Additional Info', {
            'fields': ('remarks', 'recorded_by')
        }),
    )


class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'date', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('class_obj__class_name', 'class_obj__subject')
    date_hierarchy = 'date'


class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('child', 'month', 'total_days', 'present_days', 'absent_days', 'attendance_percentage')
    list_filter = ('month',)
    search_fields = ('child__first_name', 'child__last_name', 'child__lrn')
    date_hierarchy = 'month'
    readonly_fields = ('attendance_percentage', 'created_at', 'updated_at')


# ========================================
# Register Models
# ========================================

admin.site.register(Class, ClassAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(GradingScheme, GradingSchemeAdmin)
admin.site.register(GradeItem, GradeItemAdmin)
admin.site.register(FinalGrade, FinalGradeAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(ClassSession, ClassSessionAdmin)
admin.site.register(AttendanceSummary, AttendanceSummaryAdmin)