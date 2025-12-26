# users/views.py
# CORRECTED - Removed FinalGrade references, using competency system

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q, Count
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.utils.timezone import now

from .models import Teacher, Parent, Child, User
from .forms import (
    TeacherLoginForm, 
    ParentLoginForm,
    ParentProfileUpdateForm,
    TeacherProfileUpdateForm
)
from .decorators import teacher_required, parent_required

# Import monitoring models
from monitoring.models import (
    Class, Enrollment, Attendance, 
    QuarterlyCompetencyRecord, Domain, QuarterlySummary
)
from information.models import Announcement, Event, Activity


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_current_quarter():
    """Helper function to determine current quarter based on date"""
    month = datetime.now().month
    
    # Philippine school year quarters (adjust if needed)
    if month in [6, 7, 8]:
        return 1  # 1st Quarter (June-August)
    elif month in [9, 10, 11]:
        return 2  # 2nd Quarter (September-November)
    elif month in [12, 1, 2]:
        return 3  # 3rd Quarter (December-February)
    else:  # [3, 4, 5]
        return 4  # 4th Quarter (March-May)


def get_attendance_stats(child, start_date=None, end_date=None):
    """Helper function to calculate attendance statistics for a child"""
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


# ========================================
# Login Selection & Common Views
# ========================================

def landing_page(request):
    """Landing page for the system"""
    return render(request, 'users/landing_page.html')


def login_selection(request):
    """Main login page - user selects role (Parent or Teacher)"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    return render(request, 'users/login_selection.html')


def redirect_to_dashboard(user):
    """Redirect user to appropriate dashboard based on role"""
    if user.role == 'teacher':
        return redirect('users:teacher_dashboard')
    elif user.role == 'parent':
        return redirect('users:parent_dashboard')
    elif user.role == 'admin':
        return redirect('admin:index')
    return redirect('users:login_selection')


def logout_view(request):
    """Logout user and redirect to login selection"""
    django_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:landing_page')


# ========================================
# Teacher Authentication & Dashboard
# ========================================

def teacher_login(request):
    """Teacher login with username and password"""
    if request.user.is_authenticated:
        return redirect('users:teacher_dashboard')

    form = TeacherLoginForm(request.POST or None)
    error = None

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == 'teacher':
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('users:teacher_dashboard')
        else:
            error = "Invalid credentials or not a teacher account."

    return render(request, 'users/teacher_login.html', {
        'form': form,
        'error': error
    })


from datetime import date
from django.db.models import Q
from information.models import Event, Announcement
# other imports...

from datetime import date, datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import date
from users.decorators import teacher_required



@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard showing classes, announcements, attendance, and categorized events."""
    teacher = request.user.teacher_profile

    # -------------------------
    # Teacher's active classes
    # -------------------------
    classes = Class.objects.filter(teacher=teacher, is_active=True).annotate(
        student_count=Count('enrollments')
    )
    total_classes = classes.count()
    total_students = sum(c.student_count for c in classes)

    # -------------------------
    # Pending competency records
    # -------------------------
    current_quarter = get_current_quarter()
    pending_records = 0
    for class_obj in classes:
        enrolled_students = Enrollment.objects.filter(class_obj=class_obj, is_active=True).count()
        students_with_records = QuarterlyCompetencyRecord.objects.filter(
            child__enrollments__class_obj=class_obj,
            quarter=current_quarter
        ).values('child').distinct().count()
        pending_records += max(0, enrolled_students - students_with_records)

    # -------------------------
    # Teacher's announcements
    # -------------------------
    my_announcements = Announcement.objects.filter(
        teacher=teacher,
        is_active=True
    ).order_by('-publish_date')[:5]
    announcements_count = Announcement.objects.filter(teacher=teacher).count()

    # -------------------------
    # Today's classes (for sidebar)
    # -------------------------
    todays_classes = classes[:3] if classes.exists() else []

    # -------------------------
    # Recent activity
    # -------------------------
    recent_activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:5]

    # -------------------------
    # Missing attendance today
    # -------------------------
    today = date.today()
    missing_attendance = 0
    for class_obj in classes:
        enrolled_count = Enrollment.objects.filter(class_obj=class_obj, is_active=True).count()
        recorded_count = Attendance.objects.filter(class_obj=class_obj, date=today).count()
        missing_attendance += max(0, enrolled_count - recorded_count)

    # -------------------------
    # Categorize events
    # -------------------------
    now = timezone.now()
    teacher_audience_filter = Q(target_audience='all') | Q(target_audience__icontains='teacher')

    past_events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        end_datetime__lt=now
    ).filter(teacher_audience_filter).order_by('-start_datetime')[:5]

    ongoing_events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_datetime__lte=now,
        end_datetime__gte=now
    ).filter(teacher_audience_filter).order_by('start_datetime')[:5]

    upcoming_events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_datetime__gt=now
    ).filter(teacher_audience_filter).order_by('start_datetime')[:5]

    # -------------------------
    # Context for template
    # -------------------------
    context = {
        'teacher': teacher,
        'classes': classes[:5],
        'total_classes': total_classes,
        'total_students': total_students,
        'pending_records': pending_records,
        'announcements_count': announcements_count,
        'my_announcements': my_announcements,
        'todays_classes': todays_classes,
        'recent_activities': recent_activities,
        'missing_attendance': missing_attendance,
        'past_events': past_events,
        'ongoing_events': ongoing_events,
        'upcoming_events': upcoming_events,
    }

    return render(request, 'users/teacher_dashboard.html', context)




# ========================================
# Parent Authentication & Dashboard
# ========================================

def parent_login(request):
    """Parent login with username and password"""
    if request.user.is_authenticated:
        return redirect('users:parent_dashboard')

    form = ParentLoginForm(request.POST or None)
    error = None

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == 'parent':
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('users:parent_dashboard')
        else:
            error = "Invalid credentials or not a parent account."

    return render(request, 'users/parent_login.html', {
        'form': form,
        'error': error
    })


from monitoring.models import Attendance

def get_total_attendance(child):
    """
    Calculate total attendance of a child across all recorded days.
    Returns dict with:
        - attendance_rate (0-100 %)
        - present_days
        - total_days
    """
    attendance_records = Attendance.objects.filter(child=child)

    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='present').count()

    attendance_rate = 0
    if total_days > 0:
        attendance_rate = round((present_days / total_days) * 100, 1)

    return {
        'attendance_rate': attendance_rate,
        'present_days': present_days,
        'total_days': total_days,
    }
@login_required
@parent_required
def parent_dashboard(request):
    parent = request.user.parent_profile
    children = parent.children.filter(is_active=True)

    # ================= CHILDREN DATA =================
    children_data = []
    for child in children:
        attendance_stats = get_total_attendance(child)

        children_data.append({
            'child': child,
            'attendance_rate': attendance_stats['attendance_rate'],
            'present_days': attendance_stats['present_days'],
            'total_days': attendance_stats['total_days'],
        })

    # ================= DATE REFERENCES =================
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)

    # ================= ANNOUNCEMENTS =================
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=now
    ).filter(
        Q(target_audience='all') | Q(target_audience='parents')
    ).order_by('-publish_date')[:5]

    recent_announcements_count = Announcement.objects.filter(
        is_active=True,
        publish_date__gte=seven_days_ago
    ).filter(
        Q(target_audience='all') | Q(target_audience='parents')
    ).count()

    # ================= EVENTS =================
    ongoing_events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_datetime__lte=now,
        end_datetime__gte=now
    ).filter(
        Q(target_audience='all') | Q(target_audience__icontains='parent')
    )

    upcoming_events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_datetime__gt=now
    ).filter(
        Q(target_audience='all') | Q(target_audience__icontains='parent')
    ).order_by('start_datetime')

    context = {
        'parent': parent,
        'children_data': children_data,

        # summary counts
        'children_count': children.count(),
        'recent_announcements_count': recent_announcements_count,
        'ongoing_events_count': ongoing_events.count(),
        'upcoming_events_count': upcoming_events.count(),

        # lists
        'announcements': announcements,
        'ongoing_events': ongoing_events[:3],
        'upcoming_events': upcoming_events[:3],
    }

    return render(request, 'users/parent_dashboard.html', context)



# ========================================
# Parent Profile Management
# ========================================

@login_required
@parent_required
def parent_profile(request):
    """View parent profile (read-only)"""
    parent = request.user.parent_profile
    
    context = {
        'parent': parent,
    }
    return render(request, 'users/parent_profile.html', context)


@login_required
@parent_required
def parent_profile_edit(request):
    """Edit parent profile"""
    parent = request.user.parent_profile
    
    if request.method == 'POST':
        form = ParentProfileUpdateForm(request.POST, request.FILES, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:parent_profile')
    else:
        form = ParentProfileUpdateForm(instance=parent)
    
    context = {
        'parent': parent,
        'form': form
    }
    return render(request, 'users/parent_profile_edit.html', context)


# ========================================
# Child Details View (for Parents)
# ========================================

@login_required
@parent_required
def child_detail(request, child_id):
    parent = request.user.parent_profile

    child = get_object_or_404(
        Child,
        id=child_id,
        parents=parent,
        is_active=True
    )

    enrollment = Enrollment.objects.filter(
        student=child,
        is_active=True
    ).select_related('class_obj__teacher__user').first()

    class_obj = enrollment.class_obj if enrollment else None
    current_quarter = get_current_quarter()

    # Competency records grouped by domain
    domains_data = []
    for domain in Domain.objects.prefetch_related('competencies'):
        competencies = []
        for competency in domain.competencies.all():
            record = QuarterlyCompetencyRecord.objects.filter(
                child=child,
                competency=competency,
                quarter=current_quarter
            ).first()

            competencies.append({
                'competency': competency,
                'level': record.level if record else None
            })

        domains_data.append({
            'domain': domain,
            'competencies': competencies
        })

    # Attendance
    thirty_days_ago = date.today() - timedelta(days=30)
    attendance_records = Attendance.objects.filter(
        child=child,
        date__gte=thirty_days_ago
    ).order_by('-date')

    attendance_stats = get_attendance_stats(
        child,
        thirty_days_ago,
        date.today()
    )

    context = {
        'child': child,
        'class_obj': class_obj,
        'current_quarter': current_quarter,
        'domains_data': domains_data,
        'attendance_records': attendance_records,
        'attendance_stats': attendance_stats,
        'enrolled_classes': [class_obj] if class_obj else [],
    }

    return render(request, 'users/child_detail.html', context)



# ========================================
# Teacher Profile Management
# ========================================

@login_required
@teacher_required
def teacher_profile(request):
    """View teacher profile (read-only)"""
    teacher = request.user.teacher_profile
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'users/teacher_profile.html', context)


@login_required
@teacher_required
def teacher_profile_edit(request):
    """Edit teacher profile"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        form = TeacherProfileUpdateForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:teacher_profile')
    else:
        form = TeacherProfileUpdateForm(instance=teacher)
    
    context = {
        'teacher': teacher,
        'form': form
    }
    return render(request, 'users/teacher_profile_edit.html', context)


# ========================================
# Teacher - View Classes and Students
# ========================================

@login_required
@teacher_required
def teacher_classes(request):
    """View all classes taught by teacher"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(
        teacher=teacher,
        is_active=True
    ).prefetch_related('enrollments__student')
    
    context = {
        'teacher': teacher,
        'classes': classes,
    }
    
    return render(request, 'users/teacher_classes.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """View students in a specific class"""
    teacher = request.user.teacher_profile
    
    try:
        class_obj = Class.objects.get(id=class_id, teacher=teacher, is_active=True)
    except Class.DoesNotExist:
        messages.error(request, 'Class not found or you do not have access.')
        return redirect('users:teacher_classes')
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(
        class_obj=class_obj,
        is_active=True
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    context = {
        'teacher': teacher,
        'class_obj': class_obj,
        'enrollments': enrollments,
    }
    
    return render(request, 'users/class_detail.html', context)