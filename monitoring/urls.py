# monitoring/urls.py
# URL Configuration for MONITORING App - Competency-Based System

from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # ========================================
    # CLASS MANAGEMENT
    # ========================================
    path('classes/', 
         views.class_list, 
         name='class_list'),
    
    path('class/<int:class_id>/', 
         views.class_detail, 
         name='class_detail'),
    
    path('class/<int:class_id>/students/', 
         views.class_detail, 
         name='student_list'),  # Alias for class_detail

    # ========================================
    # COMPETENCY RECORD MANAGEMENT
    # ========================================
    path('class/<int:class_id>/competencies/', 
         views.competency_input, 
         name='competency_input'),
    
    path('class/<int:class_id>/competencies/template/', 
         views.download_competency_template, 
         name='download_competency_template'),
    
    path('class/<int:class_id>/competencies/upload/', 
         views.bulk_upload_competencies, 
         name='bulk_upload_competencies'),
    
    path('student/<int:student_id>/competencies/', 
         views.student_competency_detail, 
         name='student_competency_detail'),
    
    # ========================================
    # ATTENDANCE MANAGEMENT
    # ========================================
    path('attendance/', 
         views.attendance_list, 
         name='attendance_list'),
    
    path('attendance/record/', 
         views.record_attendance, 
         name='record_attendance'),
    
    path('student/<int:student_id>/attendance/', 
         views.student_attendance_detail, 
         name='student_attendance_detail'),
    
    # ========================================
    # REPORTS & DOWNLOADS
    # ========================================
    # Report Card (for Parents)
    path('report-card/<int:child_id>/<int:quarter>/', 
         views.download_report_card, 
         name='download_report_card'),
    
    # Class Report
    path('class/<int:class_id>/report/', 
         views.class_report, 
         name='class_report'),
    
    path('class/<int:class_id>/report/export/', 
         views.export_class_report, 
         name='export_class_report'),
]