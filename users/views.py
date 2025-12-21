from itertools import count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Q, Count
from monitoring.models import FinalGrade, Attendance
from datetime import datetime, timedelta
from .models import Teacher, Parent, Child
from .forms import (
    TeacherLoginForm, 
    ParentLoginForm,
    ParentProfileUpdateForm,
    TeacherProfileUpdateForm
)
from .decorators import teacher_required, parent_required
from monitoring.models import Class, Enrollment, FinalGrade, Attendance
from information.models import Announcement, Event
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

# ========================================
# Login Selection & Common Views
# ========================================

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


@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard"""
    if request.user.role != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    teacher = request.user.teacher_profile
    
    # Get teacher's classes
    classes = Class.objects.filter(
        teacher=teacher
    ).annotate(
        student_count=Count('enrollments')
    )
    
    # Calculate statistics
    total_classes = classes.count()
    total_students = sum(c.student_count for c in classes)
    
    # Count pending grades (students without grades for current quarter)
    current_quarter = get_current_quarter()
    pending_grades = 0
    for class_obj in classes:
        enrolled_students = Enrollment.objects.filter(class_obj=class_obj).count()
        graded_students = FinalGrade.objects.filter(
            class_obj=class_obj,
            quarter=current_quarter
        ).count()
        pending_grades += (enrolled_students - graded_students)
    
    # Get teacher's announcements
    try:
        my_announcements = Announcement.objects.filter(
            teacher=teacher
        ).order_by('-publish_date')[:5]
        announcements_count = Announcement.objects.filter(teacher=teacher).count()
    except:
        my_announcements = []
        announcements_count = 0
    
    # Get today's classes (simplified - returns first 3 classes)
    todays_classes = classes[:3] if classes.exists() else []
    
    # Recent activity (placeholder - implement when Activity model exists)
    recent_activities = []
    
    # Count missing attendance (placeholder - implement your logic)
    missing_attendance = 0
    
    # Upcoming deadlines (placeholder - implement when Deadline model exists)
    upcoming_deadlines = []
    
    context = {
        'teacher': teacher,
        'classes': classes[:5],  # Show first 5 classes
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


def get_attendance_stats(child, start_date=None, end_date=None):
    """
    Helper function to calculate attendance statistics for a child
    """
    if not end_date:
        end_date = timedelta.localdate()
    
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


@login_required
def parent_dashboard(request):
    """Parent dashboard with children info"""
    # Check if user is a parent
    if request.user.role != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    # Get parent profile
    try:
        parent = request.user.parent_profile
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('users:login_selection')
    
    # Get all children
    children = parent.children.all()
    
    # Prepare data for each child
    children_data = []
    
    for child in children:
        # ========== GET LATEST GRADES ==========
        latest_grades = FinalGrade.objects.filter(
            student=child
        ).select_related('class_obj').order_by('-quarter', '-created_at')[:3]
        
        # ========== CALCULATE CURRENT AVERAGE ==========
        current_quarter = get_current_quarter()
        current_average = FinalGrade.objects.filter(
            student=child,
            quarter=current_quarter
        ).aggregate(Avg('final_grade'))['final_grade__avg']
        
        # ========== GET ATTENDANCE STATS (LAST 30 DAYS) ==========
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        # Query attendance records
        attendance_records = Attendance.objects.filter(
            child=child,
            date__gte=thirty_days_ago
        )
        
        # Count days
        total_days = attendance_records.count()
        present_days = attendance_records.filter(
            Q(status='present') | Q(status='late')
        ).count()
        
        # Calculate attendance rate (with safety check)
        if total_days > 0:
            attendance_rate = round((present_days / total_days * 100), 1)
        else:
            attendance_rate = 0  # Default if no attendance records
        
        # ========== BUILD DICTIONARY ==========
        children_data.append({
            'child': child,
            'latest_grades': latest_grades,
            'current_average': round(current_average, 2) if current_average else None,
            'attendance_rate': attendance_rate,
            'present_days': present_days,
            'total_days': total_days,
        })
    
    # ========== GET ANNOUNCEMENTS (FIXED) ==========
    # Changed from 'posted_by' to 'teacher__user' and limited to 2
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=datetime.now()
    ).select_related('teacher__user').order_by('-publish_date')[:2]
    
    # ========== GET UPCOMING EVENTS ==========
    events = Event.objects.filter(
        start_date__gte=datetime.now().date(),
        is_active=True
    ).order_by('start_date')[:4]
    
    # ========== BUILD CONTEXT ==========
    context = {
        'parent': parent,
        'children_data': children_data,
        'announcements': announcements,
        'events': events,
    }
    
    # ========== DEBUG OUTPUT (Optional - remove in production) ==========
    print("=" * 60)
    print("DEBUG: Parent Dashboard")
    print(f"Parent: {parent.user.get_full_name()}")
    print(f"Number of children: {len(children_data)}")
    print(f"Number of announcements: {announcements.count()}")
    for data in children_data:
        print(f"\nChild: {data['child'].get_full_name()}")
        print(f"  Attendance Rate: {data['attendance_rate']}%")
        print(f"  Present Days: {data['present_days']}")
        print(f"  Total Days: {data['total_days']}")
    print("=" * 60)
    
    return render(request, 'users/parent_dashboard.html', context)

# If you need this in multiple places, create a reusable function:
def get_child_dashboard_data(child):
    """
    Get all dashboard data for a child
    Returns a dictionary with child info, attendance stats, and grades
    """
    return {
        'child': child,
        'attendance_stats': get_attendance_stats(child),
        'latest_grades': FinalGrade.objects.filter(
            student=child
        ).select_related('class_obj').order_by('-created_at')[:3],
    }


# Then use it like this in your view:
@login_required
@parent_required
def parent_dashboard_clean(request):
    """Clean parent dashboard using helper function"""
    parent = request.user.parent_profile
    
    # Get dashboard data for all children
    children_data = [
        get_child_dashboard_data(child) 
        for child in parent.children.all()
    ]
    
    context = {
        'parent': parent,
        'children_data': children_data,
    }
    
    return render(request, 'users/parent_dashboard.html', context)




@login_required
def parent_dashboard(request):
    """Parent dashboard with children info"""
    # Check if user is a parent
    if request.user.role != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('users:login_selection')
    
    # Get parent profile
    try:
        parent = request.user.parent_profile
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('users:login_selection')
    
    # Get all children
    children = parent.children.all()
    
    # Prepare data for each child
    children_data = []
    
    for child in children:
        # ========== GET LATEST GRADES ==========
        latest_grades = FinalGrade.objects.filter(
            student=child
        ).select_related('class_obj').order_by('-quarter', '-created_at')[:3]
        
        # ========== CALCULATE CURRENT AVERAGE ==========
        current_quarter = get_current_quarter()
        current_average = FinalGrade.objects.filter(
            student=child,
            quarter=current_quarter
        ).aggregate(Avg('final_grade'))['final_grade__avg']
        
        # ========== GET ATTENDANCE STATS (LAST 30 DAYS) ==========
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        # Query attendance records
        attendance_records = Attendance.objects.filter(
            child=child,
            date__gte=thirty_days_ago
        )
        
        # Count days
        total_days = attendance_records.count()
        present_days = attendance_records.filter(
            Q(status='present') | Q(status='late')
        ).count()
        
        # Calculate attendance rate (with safety check)
        if total_days > 0:
            attendance_rate = round((present_days / total_days * 100), 1)
        else:
            attendance_rate = 0  # Default if no attendance records
        
        # ========== BUILD DICTIONARY ==========
        children_data.append({
            'child': child,
            'latest_grades': latest_grades,
            'current_average': round(current_average, 2) if current_average else None,
            'attendance_rate': attendance_rate,
            'present_days': present_days,
            'total_days': total_days,
        })
    
    # ========== GET ANNOUNCEMENTS ==========
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=datetime.now()
    ).select_related('posted_by').order_by('-publish_date')[:5]
    
    # ========== GET UPCOMING EVENTS ==========
    # FIXED: Changed from date__gte to start_date__gte
    events = Event.objects.filter(
        start_date__gte=datetime.now().date(),
        is_active=True  # Also filter for active events
    ).order_by('start_date')[:4]
    
    # ========== BUILD CONTEXT ==========
    context = {
        'parent': parent,
        'children_data': children_data,
        'announcements': announcements,
        'events': events,
    }
    
    # ========== DEBUG OUTPUT (Optional - remove in production) ==========
    print("=" * 60)
    print("DEBUG: Parent Dashboard")
    print(f"Parent: {parent.user.get_full_name()}")
    print(f"Number of children: {len(children_data)}")
    for data in children_data:
        print(f"\nChild: {data['child'].get_full_name()}")
        print(f"  Attendance Rate: {data['attendance_rate']}%")
        print(f"  Present Days: {data['present_days']}")
        print(f"  Total Days: {data['total_days']}")
    print("=" * 60)
    
    return render(request, 'users/parent_dashboard.html', context)

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
    """Detailed view of a child's information for parent"""
    parent = request.user.parent_profile
    
    # Ensure parent has access to this child
    try:
        child = Child.objects.get(id=child_id, parents=parent)
    except Child.DoesNotExist:
        messages.error(request, 'Child not found or you do not have access.')
        return redirect('users:parent_dashboard')
    
    # Get all enrolled classes
    enrolled_classes = Class.objects.filter(enrollments__student=child)
    
    # All final grades grouped by quarter
    grades_by_quarter = {}
    for quarter in range(1, 5):
        grades = FinalGrade.objects.filter(
            student=child,
            quarter=quarter
        ).select_related('class_obj')
        if grades.exists():
            grades_by_quarter[quarter] = grades
    
    # Attendance records (last 30 days)
    attendance = Attendance.objects.filter(
        child=child
    ).order_by('-date')[:30]
    
    # Attendance summary
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(
        child=child,
        date__gte=thirty_days_ago
    )
    
    total_days = recent_attendance.count()
    present_days = recent_attendance.filter(status='present').count()
    absent_days = recent_attendance.filter(status='absent').count()
    late_days = recent_attendance.filter(status='late').count()
    
    context = {
        'child': child,
        'enrolled_classes': enrolled_classes,
        'grades_by_quarter': grades_by_quarter,
        'attendance': attendance,
        'attendance_summary': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': round((present_days / total_days * 100) if total_days > 0 else 0, 1)
        }
    }
    
    return render(request, 'users/child_detail.html', context)


# ========================================
# Teacher - View Classes and Students
# ========================================

@login_required
@teacher_required
def teacher_classes(request):
    """View all classes taught by teacher"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher).prefetch_related('enrollments__student')
    
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
    
    # Ensure teacher owns this class
    try:
        class_obj = Class.objects.get(id=class_id, teacher=teacher)
    except Class.DoesNotExist:
        messages.error(request, 'Class not found or you do not have access.')
        return redirect('users:teacher_classes')
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(
        class_obj=class_obj
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    context = {
        'teacher': teacher,
        'class_obj': class_obj,
        'enrollments': enrollments,
    }
    
    return render(request, 'users/class_detail.html', context)


# ========================================
# Teacher Profile Management (UPDATED)
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
# Chatbot Management
# ========================================

@login_required
@parent_required
@csrf_exempt
def chatbot_view(request):
    """Handle chatbot API requests"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Get parent and children info for context
        parent = request.user.parent_profile
        children = parent.children.all()
        
        # Build context for the AI
        context = f"You are a helpful school assistant chatbot. The parent has {children.count()} child(ren) enrolled. "
        if children.exists():
            child_names = ", ".join([child.get_full_name() for child in children])
            context += f"Their names are: {child_names}. "
        
        context += "Answer questions about school policies, schedules, and provide general assistance. Be friendly and concise."
        
        # Prepare the prompt
        prompt = f"{context}\n\nParent: {user_message}\nAssistant:"
        
        # Call Hugging Face API
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 150,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                bot_response = result[0].get('generated_text', '').strip()
                # Remove the prompt from response
                bot_response = bot_response.replace(prompt, '').strip()
                
                if not bot_response:
                    bot_response = "I'm here to help! Can you please rephrase your question?"
                
                return JsonResponse({
                    'success': True,
                    'response': bot_response
                })
            else:
                return JsonResponse({
                    'success': False,
                    'response': "I'm currently processing. Please try again!"
                })
        else:
            return JsonResponse({
                'success': False,
                'response': "I'm having trouble connecting. Please try again in a moment."
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except requests.Timeout:
        return JsonResponse({
            'success': False,
            'response': "Request timed out. Please try again."
        })
    except Exception as e:
        print(f"Chatbot error: {str(e)}")
        return JsonResponse({
            'success': False,
            'response': "Something went wrong. Please try again later."
        })
    

def landing_page(request):
    return render(request, 'users/landing_page.html')
