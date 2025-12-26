# project/urls.py (or your_project_name/urls.py)
# Main URL Configuration - Kindergarten Monitoring System

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ========================================
    # ADMIN PANEL
    # ========================================
    path('admin/', admin.site.urls),
    
    # ========================================
    # USERS APP (Authentication & Profiles)
    # ========================================
    path('', include('users.urls')),  # Root URLs for landing page and login
    
    # ========================================
    # MONITORING APP (Classes, Competencies, Attendance)
    # ========================================
    path('monitoring/', include('monitoring.urls')),
    
    # ========================================
    # INFORMATION APP (Events, Announcements, Chat)
    # ========================================
    path('information/', include('information.urls')),
]

# ========================================
# MEDIA FILES (for development only)
# ========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)