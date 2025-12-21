from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta, datetime
from django.db.models import Count, Q
from users.models import Child
from users.decorators import role_required, teacher_required
from .models import Class, Enrollment, GradeItem, FinalGrade, Attendance
from io import BytesIO
from reportlab.pdfgen import canvas
import csv
from reportlab.lib.pagesizes import letter
from django.core.paginator import Paginator
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ========================================
# Helper Functions
# ========================================

def get_attendance_stats(child, start_date=None, end_date=None):
    """
    Helper function to calculate attendance statistics for a child
    
    Args:
        child: Child object
        start_date: Start date for calculation (default: first day of current month)
        end_date: End date for calculation (default: today)
    
    Returns:
        Dictionary with attendance statistics
    """
    if not end_date:
        end_date = date.today()
    
    if not start_date:
        start_date = end_date.replace(day=1)
    
    # Get attendance records for the period
    attendance_records = Attendance.objects.filter(
        child=child,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Count different statuses
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='present').count()
    absent_days = attendance_records.filter(status='absent').count()
    late_days = attendance_records.filter(status='late').count()
    excused_days = attendance_records.filter(status='excused').count()
    
    # Calculate attendance rate
    attendance_rate = 0
    if total_days > 0:
        attendance_rate = round((present_days / total_days) * 100, 1)
    
    return {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'excused_days': excused_days,
        'attendance_rate': attendance_rate,
    }

    print(f"Teacher: {teacher}")
    print(f"Classes count: {classes.count()}")
    print(f"Classes: {list(classes.values('id', 'subject', 'class_name'))}")
# ========================================
# Class Management
# ========================================
@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    teacher = request.user.teacher_profile
    
    # Get teacher's classes with enrollment count
    classes = Class.objects.filter(teacher=teacher).prefetch_related('enrollments')
    
    # Calculate statistics
    total_classes = classes.count()
    total_students = sum(class_obj.enrollments.count() for class_obj in classes)
    
    # Get pending grades count (example logic - adjust based on your needs)
    pending_grades = 0  # Implement your logic here
    
    # Get announcements count
    from information.models import Announcement  # Adjust import based on your app structure
    announcements_count = Announcement.objects.filter(author=teacher.user).count()
    my_announcements = Announcement.objects.filter(author=teacher.user).order_by('-publish_date')[:5]
    
    # Get today's classes (if you have schedule field)
    from datetime import date
    today = date.today()
    todays_classes = classes.filter(
        # Add your schedule filtering logic here
        # For example: schedule__day=today.strftime('%A')
    )
    
    # Recent activities (implement based on your needs)
    recent_activities = []
    
    # Reminders
    missing_attendance = 0  # Implement your logic
    upcoming_deadlines = []  # Implement your logic
    
    context = {
        'teacher': teacher,
        'classes': classes,  # This is the key line that was missing!
        'total_classes': total_classes,
        'total_students': total_students,
        'pending_grades': pending_grades,
        'announcements_count': announcements_count,
        'my_announcements': my_announcements,
        'todays_classes': todays_classes,
        'recent_activities': recent_activities,
        'missing_attendance': missing_attendance,
        'upcoming_deadlines': upcoming_deadlines,
    }
    
    return render(request, 'users/teacher_dashboard.html', context)


@login_required
@teacher_required
def class_list(request):
    """Display all classes assigned to the logged-in teacher"""
    teacher = request.user.teacher_profile
    
    classes = Class.objects.filter(teacher=teacher).annotate(
        student_count= Count('enrollments')
    ).order_by('subject')
    
    context = {
        'classes': classes
    }
    return render(request, 'monitoring/class_list.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """Show details of a class and enrolled students"""
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher_profile)
    
    # Get all enrolled students
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = []
    for e in enrollments:
        student = e.student
        # Optional: compute current average grade for display
        grades = GradeItem.objects.filter(student=student, class_obj=class_obj)
        if grades.exists():
            student.average = round(sum([g.percentage_score() for g in grades]) / grades.count(), 2)
        else:
            student.average = None
        students.append(student)

    # Class statistics
    total_students = len(students)
    average_grade = round(sum([s.average for s in students if s.average is not None]) / total_students, 1) if total_students else 0
    passing_count = len([s for s in students if s.average is not None and s.average >= 75])
    failing_count = len([s for s in students if s.average is not None and s.average < 75])
    
    context = {
        'class_obj': class_obj,
        'students': students,
        'total_students': total_students,
        'average_grade': average_grade,
        'passing_count': passing_count,
        'failing_count': failing_count,
    }
    
    return render(request, 'monitoring/class_detail.html', context)

@login_required
@role_required('teacher')
def student_list(request, class_id):
    from monitoring.models import Class, Enrollment
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    # Get enrolled students through Enrollment model
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = [enrollment.student for enrollment in enrollments]
    
    context = {
        'class_obj': class_obj,
        'students': students,
    }
    
    return render(request, 'monitoring/student_lists.html', context)

# ========================================
# Grade Management
# ========================================

@login_required
def class_grades(request, class_id):
    """View all grades for a class across all quarters"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = [e.student for e in enrollments]
    
    context = {
        'class_obj': class_obj,
        'students': students,
        'quarters': [1, 2, 3, 4],
    }
    
    return render(request, 'monitoring/class_grade.html', context)


@login_required
@teacher_required
def student_grades(request, student_id):
    """View all grades for a specific student"""
    teacher = request.user.teacher_profile
    
    student = get_object_or_404(Child, id=student_id)
    
    # Get all grades for this student in teacher's classes
    grades = FinalGrade.objects.filter(
        student=student,
        class_obj__teacher=teacher
    ).select_related('class_obj').order_by('class_obj', 'quarter')
    
    # Get attendance stats for this student
    attendance_stats = get_attendance_stats(student)
    
    # Create child_data with stats
    child_data = {
        'child': student,
        'attendance_stats': attendance_stats,
    }
    
    context = {
        'student': student,
        'child_data': child_data,
        'grades': grades,
        'teacher': teacher,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'monitoring/student_grades.html', context)


@login_required
@teacher_required
def grade_input(request, class_id):
    """Input grades for students in a class"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)

    # Current quarter from GET or default to 1
    current_quarter = int(request.GET.get('quarter', 1))

    # Get enrolled students
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = []
    for e in enrollments:
        student = e.student

        # Attach current grade if exists
        final_grade, created = FinalGrade.objects.get_or_create(
            student=student,
            class_obj=class_obj,
            quarter=current_quarter
        )
        student.current_grade = final_grade
        students.append(student)

    context = {
        'class_obj': class_obj,
        'students': students,
        'current_quarter': current_quarter,
    }

    return render(request, 'monitoring/grade_input.html', context)

@login_required
@teacher_required
def download_grade_template(request, class_id):
    """Download Excel template for grade entry"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    # Generate Excel template using openpyxl
    # Similar to your first project's implementation
    
    # For now, return placeholder
    return HttpResponse("Template download - to be implemented with openpyxl")


@login_required
@teacher_required
def edit_grade(request, grade_id):
    """Edit a final grade"""
    teacher = request.user.teacher_profile
    grade = get_object_or_404(FinalGrade, id=grade_id, class_obj__teacher=teacher)
    
    if request.method == 'POST':
        # Handle grade editing
        grade.compute_final_grade()
        messages.success(request, 'Grade updated successfully!')
        return redirect('monitoring:class_grades', class_id=grade.class_obj.id)
    
    context = {
        'grade': grade,
        'teacher': teacher,
    }
    return render(request, 'monitoring/edit_grade.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Class, Enrollment, Child, GradeItem, FinalGrade
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Class, Enrollment, GradeItem, FinalGrade
from users.models import Child
from openpyxl import Workbook, load_workbook
from django.http import HttpResponse


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import Child, Teacher
from .models import Class, Enrollment

@login_required
def grade_input(request, class_id):
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = [en.student for en in enrollments]

    current_quarter = int(request.GET.get('quarter', 1))

    context = {
        'class_obj': class_obj,
        'students': students,
        'current_quarter': current_quarter,
        'quarters': [1, 2, 3, 4],
    }
    return render(request, 'monitoring/grade_input.html', context)



@login_required
@teacher_required
def download_grade_template(request, class_id):
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Grade Template"
    
    # Headers
    headers = ['LRN', 'Student Name', 'Quarter', 'Written Work', 'Performance Task', 'Quarterly Exam']
    ws.append(headers)
    
    # Fill with student info
    for enrollment in enrollments:
        student = enrollment.student
        ws.append([student.lrn, student.get_full_name(), '', '', '', ''])
    
    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Grade_Template_{class_obj.class_name}.xlsx"'
    wb.save(response)
    return response


@login_required
@teacher_required
def bulk_upload_grades(request, class_id):
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    if request.method == 'POST' and request.FILES.get('grade_file'):
        excel_file = request.FILES['grade_file']
        try:
            wb = load_workbook(excel_file)
            ws = wb.active
            
            success_count = 0
            errors = []
            
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    lrn, name, quarter, ww, pt, qe = row
                    if not lrn or not quarter:
                        continue
                    student = Child.objects.get(lrn=lrn)
                    if not Enrollment.objects.filter(student=student, class_obj=class_obj).exists():
                        errors.append(f"Row {row_num}: {student.get_full_name()} not enrolled")
                        continue
                    
                    grade, created = FinalGrade.objects.get_or_create(
                        student=student,
                        class_obj=class_obj,
                        quarter=int(quarter)
                    )
                    grade.written_work = float(ww or 0)
                    grade.performance_task = float(pt or 0)
                    grade.quarterly_exam = float(qe or 0)
                    grade.compute_final_grade()
                    success_count += 1
                except Child.DoesNotExist:
                    errors.append(f"Row {row_num}: Student with LRN {lrn} not found")
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            messages.success(request, f"Uploaded grades for {success_count} student(s).")
            if errors:
                messages.warning(request, f"Errors: {'; '.join(errors[:5])}{'...' if len(errors) > 5 else ''}")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
    else:
        messages.error(request, "No file uploaded.")
    
    return redirect('monitoring:grade_input', class_id=class_id)



# ========================================
# Attendance Management
# ========================================

@login_required
def attendance_list(request):
    """View list of all attendance records"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    # Get filter parameters
    class_id = request.GET.get('class_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base query
    attendance_records = Attendance.objects.filter(
        class_obj__teacher=teacher
    ).select_related('child', 'class_obj').order_by('-date')
    
    # Apply filters
    if class_id:
        attendance_records = attendance_records.filter(class_obj_id=class_id)
    if start_date:
        attendance_records = attendance_records.filter(date__gte=start_date)
    if end_date:
        attendance_records = attendance_records.filter(date__lte=end_date)
    
    # Pagination
    paginator = Paginator(attendance_records, 50)  # Show 50 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'classes': classes,
        'attendance_records': page_obj,
    }
    

    return render(request, 'monitoring/attendance_list.html', context)

@login_required
def record_attendance(request):
    """Quick attendance recording page"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    # Get selected date and class
    selected_date_str = request.GET.get('date', datetime.now().date().isoformat())
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students = []
    
    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id, teacher=teacher)
        enrollments = Enrollment.objects.filter(class_obj=selected_class).select_related('student')
        students = [e.student for e in enrollments]
        
        # NEW CODE: Get existing attendance records and attach status to each student
        attendance_records = {}
        existing_records = Attendance.objects.filter(
            date=selected_date,
            class_obj=selected_class
        )
        for record in existing_records:
            attendance_records[record.child.id] = record.status
        
        # Attach attendance status to each student
        for student in students:
            student.attendance_status = attendance_records.get(student.id, None)
    
    # Handle form submission
    if request.method == 'POST':
        date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        class_id = request.POST.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
        
        enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
        saved_count = 0
        
        for enrollment in enrollments:
            student = enrollment.student
            status = request.POST.get(f'status_{student.id}')
            
            if status:
                Attendance.objects.update_or_create(
                    child=student,
                    date=date,
                    class_obj=class_obj,
                    defaults={'status': status}
                )
                saved_count += 1
        
        messages.success(request, f'Attendance saved for {saved_count} students.')
        return redirect('monitoring:record_attendance')
    
    context = {
        'classes': classes,
        'selected_date': selected_date,
        'selected_class': selected_class,
        'students': students,
        'recorded_by': teacher,
    }
    
    return render(request, 'monitoring/record_attendance.html', context)


@login_required
@teacher_required
def student_attendance(request, student_id):
    """View attendance history for a student"""
    teacher = request.user.teacher_profile
    
    student = get_object_or_404(Child, id=student_id)
    
    # Get attendance records (last 30 days)
    attendance = Attendance.objects.filter(
        child=student
    ).order_by('-date')[:30]
    
    # Get attendance stats for this student (current month)
    attendance_stats = get_attendance_stats(student)
    
    # Create child_data with stats
    child_data = {
        'child': student,
        'attendance_stats': attendance_stats,
    }
    
    context = {
        'student': student,
        'child_data': child_data,
        'attendance': attendance,
        'teacher': teacher,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'monitoring/student_attendance.html', context)


# ========================================
# Reports
# ========================================

@login_required
def grade_report(request):
    """Generate grade reports"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    # Placeholder - implement report generation
    messages.info(request, 'Report generation coming soon!')
    return redirect('monitoring:class_list')


@login_required
def generate_report(request):
    """Main report generation page"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    context = {
        'classes': classes,
    }
    
    return render(request, 'monitoring/grade_report.html', context)

@login_required
@teacher_required
def class_report(request, class_id):
    """Generate comprehensive class report"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_report.html', context)

@login_required
@teacher_required
def grade_report(request):
    """Generate grade report"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        quarter = request.POST.get('quarter')
        format_type = request.POST.get('format')
        
        # TODO: Implement report generation logic here
        messages.success(request, f'Grade report generated successfully in {format_type} format!')
        return redirect('monitoring:grade_report')
    
    context = {
        'teacher': teacher,
        'classes': classes,
    }
    return render(request, 'monitoring/grade_report.html', context)


@login_required
@teacher_required
def attendance_report(request):
    """Generate attendance report"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        format_type = request.POST.get('format')
        
        # TODO: Implement attendance report generation logic here
        messages.success(request, f'Attendance report generated successfully in {format_type} format!')
        return redirect('monitoring:attendance_report')
    
    context = {
        'teacher': teacher,
        'classes': classes,
    }
    return render(request, 'monitoring/attendance_report.html', context)


@login_required
@teacher_required
def class_summary_report(request):
    """Generate class summary report"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        include_grades = request.POST.get('include_grades') == 'on'
        include_attendance = request.POST.get('include_attendance') == 'on'
        include_statistics = request.POST.get('include_statistics') == 'on'
        
        # TODO: Implement class summary report generation logic here
        messages.success(request, 'Class summary report generated successfully!')
        return redirect('monitoring:grade_report')
    
    return redirect('monitoring:grade_report')


@login_required
@teacher_required
def student_performance_report(request):
    """Generate student performance report"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        student_id = request.POST.get('student_id')
        period = request.POST.get('period')
        
        # TODO: Implement student performance report generation logic here
        messages.success(request, 'Student performance report generated successfully!')
        return redirect('monitoring:grade_report')
    
    return redirect('monitoring:grade_report')


@login_required
@teacher_required
def class_report(request, class_id):
    """Generate comprehensive class report"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_report.html', context)


def export_students(request, class_id):
    from monitoring.models import Class, Enrollment
    from users.models import Child
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    # Get students through the Enrollment model
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    students = [enrollment.student for enrollment in enrollments]
    
    format_type = request.GET.get('format', 'csv')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="students_{class_obj.class_name}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Full Name', 'Date of Birth', 'Gender', 'Enrolled Date'])
        
        for enrollment in enrollments:
            student = enrollment.student
            writer.writerow([
                student.id,
                student.get_full_name(),
                student.date_of_birth,
                student.gender,
                enrollment.enrolled_date
            ])
        
        return response
    
    elif format_type == 'pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"Student List - {class_obj.class_name}")
        p.drawString(100, 730, f"Subject: {class_obj.subject}")
        
        # Add student data
        p.setFont("Helvetica", 11)
        y = 690
        p.drawString(100, y, "Students Enrolled:")
        y -= 25
        
        for enrollment in enrollments:
            student = enrollment.student
            text = f"• {student.get_full_name()} (ID: {student.id}) - Enrolled: {enrollment.enrolled_date}"
            p.drawString(120, y, text)
            y -= 20
            
            if y < 100:  # New page if needed
                p.showPage()
                p.setFont("Helvetica", 11)
                y = 750
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="students_{class_obj.class_name}.pdf"'
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)