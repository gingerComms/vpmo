"""
WSGI config for vpmoprj project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import sys

sys.path.append("/home/ubuntu/vpmo")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vpmoprj.settings")

from django.core.handlers.wsgi import WSGIHandler

class WSGIEnvironment(WSGIHandler):

    def __call__(self, environ, start_response):

    	env_variables = ["TWILIO_CHAT_SERVICE_SID", "TWILIO_ACCOUNT_SID", "TWILIO_API_KEY", "TWILIO_SECRET_KEY", "VPMO_TWILIO_AUTH_TOKEN", "VPMO_AWS_ACCESS", "VPMO_AWS_SECRET", "MONGO_HOST"]

    	for variable in env_variables:
        	os.environ[variable] = environ[variable]
        return super(WSGIEnvironment, self).__call__(environ, start_response)

application = WSGIEnvironment()

# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()
