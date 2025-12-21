from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*required_roles):
    """
    Decorator to restrict access based on user role.
    
    Usage:
        @role_required('teacher')
        def teacher_only_view(request):
            ...
        
        @role_required('teacher', 'parent')
        def teacher_or_parent_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to access this page.')
                return redirect('login_selection')
            
            if request.user.role in required_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('login_selection')
        
        return _wrapped_view
    return decorator


def student_required(view_func):
    """Shortcut decorator for student-only views"""
    return role_required('student')(view_func)


def teacher_required(view_func):
    """Shortcut decorator for teacher-only views"""
    return role_required('teacher')(view_func)


def parent_required(view_func):
    """Shortcut decorator for parent-only views"""
    return role_required('parent')(view_func)


def admin_required(view_func):
    """Shortcut decorator for admin-only views"""
    return role_required('admin')(view_func)