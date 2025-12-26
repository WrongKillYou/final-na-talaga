# users/urls.py
# URL Configuration for USERS App - Authentication & Profiles

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ========================================
    # LANDING & LOGIN SELECTION
    # ========================================
    path('', 
         views.landing_page, 
         name='landing_page'),
    
    path('login/', 
         views.login_selection, 
         name='login_selection'),
    
    path('logout/', 
         views.logout_view, 
         name='logout'),
    
    # ========================================
    # TEACHER AUTHENTICATION & DASHBOARD
    # ========================================
    path('teacher/login/', 
         views.teacher_login, 
         name='teacher_login'),
    
    path('teacher/dashboard/', 
         views.teacher_dashboard, 
         name='teacher_dashboard'),
    
    path('teacher/profile/', 
         views.teacher_profile, 
         name='teacher_profile'),
    
    path('teacher/profile/edit/', 
         views.teacher_profile_edit, 
         name='teacher_profile_edit'),
    
    path('teacher/classes/', 
         views.teacher_classes, 
         name='teacher_classes'),
    
    path('teacher/class/<int:class_id>/', 
         views.class_detail, 
         name='class_detail'),
    
    # ========================================
    # PARENT AUTHENTICATION & DASHBOARD
    # ========================================
    path('parent/login/', 
         views.parent_login, 
         name='parent_login'),
    
    path('parent/dashboard/', 
         views.parent_dashboard, 
         name='parent_dashboard'),
    
    path('parent/profile/', 
         views.parent_profile, 
         name='parent_profile'),
    
    path('parent/profile/edit/', 
         views.parent_profile_edit, 
         name='parent_profile_edit'),
    
    # ========================================
    # CHILD DETAILS (for Parents)
    # ========================================
    path('child/<int:child_id>/', 
         views.child_detail, 
         name='child_detail'),
]