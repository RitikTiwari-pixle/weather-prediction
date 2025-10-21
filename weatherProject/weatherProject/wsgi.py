import os
import sys

# Path to your project directory (the one with manage.py)
# ======== !! CHANGE THIS !! ========
path = '/home/YOUR-USERNAME/your-repo-name'  

if path not in sys.path:
    sys.path.insert(0, path)

# Set the settings module
# ======== !! CHANGE THIS !! ========
os.environ['DJANGO_SETTINGS_MODULE'] = 'weatherProject.settings'

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()