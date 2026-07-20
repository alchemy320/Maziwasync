"""
WSGI config for maziwasyncbck project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

sys.path.append('/home/alchemy/www/Maziwasync/maziwasyncbck')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maziwasyncbck.settings')

application = get_wsgi_application()
