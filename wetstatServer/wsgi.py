# coding=utf-8
"""
WSGI config for wetstatServer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

# import os
#
# from django.core.wsgi import get_wsgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wetstatServer.settings')
#
# application = get_wsgi_application()

import os
import signal
import sys
import time
import traceback

from django.core.wsgi import get_wsgi_application

sys.path.append('/home/pi/wetstatServer')
# adjust the Python version in the line below as needed
sys.path.append('/home/pi/wetstatServer/venv/lib/python3.7/site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wetstatServer.settings")

try:
    application = get_wsgi_application()
except Exception:
    # Error loading applications
    if 'mod_wsgi' in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)
