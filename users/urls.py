from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import TeacherPasswordChangeForm, ParentPasswordChangeForm

app_name = 'users'

urlpatterns = [
    # ========================================
    # Login & Logout
    # ========================================
    path('', views.login_selection, name='login_selection'),
    path('logout/', views.logout_view, name='logout'),
    
    # ========================================
    # Teacher URLs
    # ========================================
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/classes/', views.teacher_classes, name='teacher_classes'),
    path('teacher/class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('profile/edit/', views.teacher_profile_edit, name='teacher_profile_edit'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),  
    
    # Teacher password change
    path(
        'teacher/change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='users/teacher_change_password.html',
            success_url='/users/teacher/password-changed/',
            form_class=TeacherPasswordChangeForm
        ),
        name='teacher_change_password'
    ),
    path(
        'teacher/password-changed/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/teacher_password_changed.html'
        ),
        name='teacher_password_changed'
    ),
    
    # ========================================
    # Parent URLs
    # ========================================
    path('parent/login/', views.parent_login, name='parent_login'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/profile/', views.parent_profile, name='parent_profile'),
    path('parent/profile/edit/', views.parent_profile_edit, name='parent_profile_edit'),
    path('parent/child/<int:child_id>/', views.child_detail, name='child_detail'),
    
    # Parent password change
    path(
        'parent/change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='users/parent_change_password.html',
            success_url='/users/parent/password-changed/',
            form_class=ParentPasswordChangeForm
        ),
        name='parent_change_password'
    ),
    path(
        'parent/password-changed/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/parent_password_changed.html'
        ),
        name='parent_password_changed'
    ),

    # ========================================
    # Chatbot URLs
    # ========================================
    path('chatbot/', views.chatbot_view, name='chatbot'),

     # ========================================
    #  URLs
    # ========================================
    path('landing-page/', views.landing_page, name='landing_page'),
]