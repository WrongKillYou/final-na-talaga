
import os
from django.core.wsgi import get_wsgi_application

# Ensure this matches your project folder name and settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_monitor.settings')

application = get_wsgi_application()
