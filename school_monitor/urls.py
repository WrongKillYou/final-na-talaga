from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Redirect root to login selection
    path('', RedirectView.as_view(pattern_name='users:login_selection', permanent=False)),


    
    # App URLs
    path('users/', include('users.urls')),
    path('monitoring/', include('monitoring.urls')),
    path('information/', include('information.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar (if installed)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# Custom error handlers (optional)
# handler404 = 'users.views.custom_404'
# handler500 = 'users.views.custom_500'
# handler403 = 'users.views.custom_403'
# handler400 = 'users.views.custom_400'