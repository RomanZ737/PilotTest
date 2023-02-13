"""
WSGI config for PilotTest project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/etc/default/web_app/PilotTest')
sys.path.append('/etc/default/web_app/PilotTest/PilotTest')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PilotTest.settings')

application = get_wsgi_application()
