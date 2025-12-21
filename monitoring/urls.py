from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # ========================================
    # Class Management (Teacher)
    # ========================================
    path('classes/', views.class_list, name='class_list'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('class/<int:class_id>/students/', views.student_list, name='student_list'),
    
    # ========================================
    # Grade Management (Teacher)
    # ========================================
    path('class/<int:class_id>/grades/', views.class_grades, name='class_grades'),
    path('class/<int:class_id>/upload-grades/', views.grade_input, name='grade_input'),
    path('class/<int:class_id>/download-template/', views.download_grade_template, name='download_grade_template'),
    path('student/<int:student_id>/grades/', views.student_grades, name='class_grades'),
    path('grade/<int:grade_id>/edit/', views.edit_grade, name='edit_grade'),
    path('class/<int:class_id>/bulk-upload-grades/', views.bulk_upload_grades, name='bulk_upload_grades'),
    path('class/<int:class_id>/download-template/', views.download_grade_template, name='download_grade_template'),

    
    # ========================================
    # Attendance Management (Teacher)
    # ========================================
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/record/', views.record_attendance, name='record_attendance'),
    path('student/<int:student_id>/attendance/', views.student_attendance, name='student_attendance'),
    
    # ========================================
    # Reports (Teacher)
    # ========================================
    path('reports/grades/', views.grade_report, name='grade_report'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
     path('reports/class-summary/', views.class_summary_report, name='class_summary_report'), 
    path('reports/student-performance/', views.student_performance_report, name='generate_student_report'), 
    path('class/<int:class_id>/report/', views.class_report, name='class_report'),


    path('class/<int:class_id>/students/', views.student_list, name='student_list'),
    path('class/<int:class_id>/export/', views.export_students, name='export_students'),
]