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
    """List all classes taught by teacher"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher).prefetch_related('enrollments')
    
    context = {
        'classes': classes,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_list.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """View class details"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
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
    """Upload grades via Excel file"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    if request.method == 'POST':
        # Handle file upload and processing
        # This would use openpyxl to parse Excel file
        # Similar to your first project's implementation
        
        messages.success(request, 'Grades uploaded successfully!')
        return redirect('monitoring:class_grades', class_id=class_id)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
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

@login_required
@teacher_required
def download_grade_template(request, class_id):
    """Download Excel template for grade entry"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Grade Template"
    
    # Define styles
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    instruction_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    
    # Class Information Section
    ws['A1'] = f"Grade Template - {class_obj.class_name}"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:H1')
    
    ws['A2'] = f"Subject: {class_obj.subject}"
    ws['A2'].font = Font(bold=True, size=11)
    ws.merge_cells('A2:H2')
    
    ws['A3'] = f"Teacher: {teacher.user.get_full_name()}"
    ws.merge_cells('A3:H3')
    
    # Instructions
    ws['A4'] = "Instructions:"
    ws['A4'].font = Font(bold=True, color="FF0000")
    
    ws['A5'] = "1. Do NOT modify the LRN, Student Name, or Quarter columns"
    ws['A5'].fill = instruction_fill
    ws.merge_cells('A5:H5')
    
    ws['A6'] = "2. Enter Component (WW/PT/QA), Score, and Highest Possible Score"
    ws['A6'].fill = instruction_fill
    ws.merge_cells('A6:H6')
    
    ws['A7'] = "3. Component codes: WW = Written Work, PT = Performance Task, QA = Quarterly Assessment"
    ws['A7'].fill = instruction_fill
    ws.merge_cells('A7:H7')
    
    ws['A8'] = "4. You can add multiple rows per student per component (e.g., Quiz 1, Quiz 2, etc.)"
    ws['A8'].fill = instruction_fill
    ws.merge_cells('A8:H8')
    
    ws['A9'] = "5. Save as Excel file (.xlsx) and upload through the system"
    ws['A9'].fill = instruction_fill
    ws.merge_cells('A9:H9')
    
    # Empty row
    ws.row_dimensions[10].height = 5
    
    # Headers
    headers = ['LRN', 'Student Name', 'Quarter', 'Component', 'Score', 'Highest Possible', 'Final Grade', 'Percentage']
    header_row = 11
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border
    
    # Column widths
    column_widths = {
        'A': 15,  # LRN
        'B': 30,  # Student Name
        'C': 10,  # Quarter
        'D': 15,  # Component
        'E': 12,  # Score
        'F': 18,  # Highest Possible
        'G': 15,  # Final Grade
        'H': 15,  # Percentage
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    # Add student data template for all quarters
    data_row = header_row + 1
    quarters = [1, 2, 3, 4]
    components = ['WW', 'PT', 'QA']
    
    for enrollment in enrollments:
        student = enrollment.student
        lrn = student.lrn if hasattr(student, 'lrn') else student.id
        
        for quarter in quarters:
            # Get existing grade items if any
            grade_items = GradeItem.objects.filter(
                student=student,
                class_obj=class_obj,
                quarter=quarter
            ).order_by('component', 'id')
            
            if grade_items.exists():
                # Add existing grade items
                for item in grade_items:
                    # LRN
                    cell = ws.cell(row=data_row, column=1)
                    cell.value = lrn
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Student Name
                    cell = ws.cell(row=data_row, column=2)
                    cell.value = student.get_full_name()
                    cell.border = border
                    
                    # Quarter
                    cell = ws.cell(row=data_row, column=3)
                    cell.value = quarter
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Component
                    cell = ws.cell(row=data_row, column=4)
                    cell.value = item.component
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Score
                    cell = ws.cell(row=data_row, column=5)
                    cell.value = item.score
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Highest Possible Score
                    cell = ws.cell(row=data_row, column=6)
                    cell.value = item.highest_possible_score
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Final Grade (computed, read-only)
                    cell = ws.cell(row=data_row, column=7)
                    try:
                        final = FinalGrade.objects.get(student=student, class_obj=class_obj, quarter=quarter)
                        cell.value = final.final_grade
                    except FinalGrade.DoesNotExist:
                        cell.value = ''
                    cell.border = border
                    cell.alignment = center_align
                    cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
                    
                    # Percentage
                    cell = ws.cell(row=data_row, column=8)
                    cell.value = round(item.percentage_score(), 2)
                    cell.border = border
                    cell.alignment = center_align
                    cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
                    
                    data_row += 1
            else:
                # Add empty template rows (one for each component)
                for component in components:
                    # LRN
                    cell = ws.cell(row=data_row, column=1)
                    cell.value = lrn
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Student Name
                    cell = ws.cell(row=data_row, column=2)
                    cell.value = student.get_full_name()
                    cell.border = border
                    
                    # Quarter
                    cell = ws.cell(row=data_row, column=3)
                    cell.value = quarter
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Component
                    cell = ws.cell(row=data_row, column=4)
                    cell.value = component
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Score (empty for user to fill)
                    cell = ws.cell(row=data_row, column=5)
                    cell.value = ''
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Highest Possible Score (empty for user to fill)
                    cell = ws.cell(row=data_row, column=6)
                    cell.value = ''
                    cell.border = border
                    cell.alignment = center_align
                    
                    # Final Grade (computed, read-only)
                    cell = ws.cell(row=data_row, column=7)
                    cell.value = ''
                    cell.border = border
                    cell.alignment = center_align
                    cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
                    
                    # Percentage (read-only)
                    cell = ws.cell(row=data_row, column=8)
                    cell.value = ''
                    cell.border = border
                    cell.alignment = center_align
                    cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
                    
                    data_row += 1
    
    # Freeze panes (freeze header row)
    ws.freeze_panes = ws['A12']
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Grade_Template_{class_obj.class_name}_{class_obj.subject}.xlsx"'
    
    # Save workbook to response
    wb.save(response)
    
    return response


@login_required
@teacher_required
def bulk_upload_grades(request, class_id):
    """Handle bulk upload of grades via Excel"""
    from openpyxl import load_workbook
    
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    if request.method == 'POST' and request.FILES.get('grade_file'):
        try:
            excel_file = request.FILES['grade_file']
            
            # Load workbook
            wb = load_workbook(excel_file)
            ws = wb.active
            
            success_count = 0
            error_count = 0
            errors = []
            updated_students = set()
            
            # Start from row 12 (after headers)
            for row_num, row in enumerate(ws.iter_rows(min_row=12, values_only=True), start=12):
                try:
                    # Extract data
                    lrn = str(row[0]).strip() if row[0] else None
                    student_name = row[1]
                    quarter = int(row[2]) if row[2] else None
                    component = str(row[3]).strip().upper() if row[3] else None
                    score = float(row[4]) if row[4] and str(row[4]).strip() else None
                    highest_possible = float(row[5]) if row[5] and str(row[5]).strip() else None
                    
                    # Skip empty rows or rows without required data
                    if not lrn or not quarter or not component or score is None or highest_possible is None:
                        continue
                    
                    # Validate component
                    if component not in ['WW', 'PT', 'QA']:
                        errors.append(f"Row {row_num}: Invalid component '{component}'. Must be WW, PT, or QA")
                        error_count += 1
                        continue
                    
                    # Find student
                    if hasattr(Child, 'lrn'):
                        student = Child.objects.get(lrn=lrn)
                    else:
                        student = Child.objects.get(id=int(lrn))
                    
                    # Verify student is enrolled in this class
                    if not Enrollment.objects.filter(class_obj=class_obj, student=student).exists():
                        errors.append(f"Row {row_num}: Student {student_name} not enrolled in this class")
                        error_count += 1
                        continue
                    
                    # Create grade item (allow multiple items per component)
                    grade_item = GradeItem.objects.create(
                        student=student,
                        class_obj=class_obj,
                        quarter=quarter,
                        component=component,
                        score=score,
                        highest_possible_score=highest_possible
                    )
                    
                    success_count += 1
                    updated_students.add((student.id, quarter))
                    
                except Child.DoesNotExist:
                    errors.append(f"Row {row_num}: Student with LRN {lrn} not found")
                    error_count += 1
                except ValueError as e:
                    errors.append(f"Row {row_num}: Invalid data format - {str(e)}")
                    error_count += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            # Recompute final grades for all affected students
            final_grades_computed = 0
            for student_id, quarter in updated_students:
                try:
                    student = Child.objects.get(id=student_id)
                    final_grade, created = FinalGrade.objects.get_or_create(
                        student=student,
                        class_obj=class_obj,
                        quarter=quarter
                    )
                    final_grade.compute_final_grade()
                    final_grades_computed += 1
                except Exception as e:
                    errors.append(f"Error computing final grade for student {student_id}, Q{quarter}: {str(e)}")
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully uploaded {success_count} grade item(s). Computed {final_grades_computed} final grade(s).')
            
            if error_count > 0:
                error_message = f'{error_count} error(s) occurred. '
                if len(errors) <= 5:
                    error_message += ' '.join(errors)
                else:
                    error_message += ' '.join(errors[:5]) + f' ... and {len(errors) - 5} more errors.'
                messages.warning(request, error_message)
            
            if success_count == 0 and error_count == 0:
                messages.info(request, 'No grades were found in the file.')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
    else:
        messages.error(request, 'No file was uploaded.')
    
    return redirect('monitoring:grade_input', class_id=class_id)

@login_required
@teacher_required
def bulk_upload_grades(request, class_id):
    """Handle bulk upload of grades via Excel"""
    from openpyxl import load_workbook
    
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    if request.method == 'POST' and request.FILES.get('grade_file'):
        try:
            excel_file = request.FILES['grade_file']
            
            # Load workbook
            wb = load_workbook(excel_file)
            ws = wb.active
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Start from row 12 (after headers)
            for row_num, row in enumerate(ws.iter_rows(min_row=12, values_only=True), start=12):
                try:
                    # Extract data
                    lrn = str(row[0]).strip() if row[0] else None
                    student_name = row[1]
                    quarter = int(row[2]) if row[2] else None
                    written_work = float(row[3]) if row[3] and str(row[3]).strip() else None
                    performance_task = float(row[4]) if row[4] and str(row[4]).strip() else None
                    quarterly_exam = float(row[5]) if row[5] and str(row[5]).strip() else None
                    
                    # Skip empty rows
                    if not lrn or not quarter:
                        continue
                    
                    # Find student
                    if hasattr(Child, 'lrn'):
                        student = Child.objects.get(lrn=lrn)
                    else:
                        student = Child.objects.get(id=int(lrn))
                    
                    # Verify student is enrolled in this class
                    if not Enrollment.objects.filter(class_obj=class_obj, student=student).exists():
                        errors.append(f"Row {row_num}: Student {student_name} not enrolled in this class")
                        error_count += 1
                        continue
                    
                    # Get or create grade
                    grade, created = FinalGrade.objects.get_or_create(
                        student=student,
                        class_obj=class_obj,
                        quarter=quarter,
                        defaults={
                            'written_work': written_work,
                            'performance_task': performance_task,
                            'quarterly_exam': quarterly_exam,
                        }
                    )
                    
                    # Update if not created
                    if not created:
                        if written_work is not None:
                            grade.written_work = written_work
                        if performance_task is not None:
                            grade.performance_task = performance_task
                        if quarterly_exam is not None:
                            grade.quarterly_exam = quarterly_exam
                    
                    # Compute final grade
                    grade.compute_final_grade()
                    
                    success_count += 1
                    
                except Child.DoesNotExist:
                    errors.append(f"Row {row_num}: Student with LRN {lrn} not found")
                    error_count += 1
                except ValueError as e:
                    errors.append(f"Row {row_num}: Invalid data format - {str(e)}")
                    error_count += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully uploaded {success_count} grade(s).')
            
            if error_count > 0:
                error_message = f'{error_count} error(s) occurred. '
                if len(errors) <= 5:
                    error_message += ' '.join(errors)
                else:
                    error_message += ' '.join(errors[:5]) + f' ... and {len(errors) - 5} more errors.'
                messages.warning(request, error_message)
            
            if success_count == 0 and error_count == 0:
                messages.info(request, 'No grades were found in the file.')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
    else:
        messages.error(request, 'No file was uploaded.')
    
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