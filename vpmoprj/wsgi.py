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

from django.core.wsgi import get_wsgi_application
from django.core.handlers.wsgi import WSGIHandler

KEYS_TO_LOAD = ["TWILIO_CHAT_SERVICE_SID", "TWILIO_ACCOUNT_SID", "TWILIO_API_KEY", "TWILIO_SECRET_KEY", "VPMO_TWILIO_AUTH_TOKEN", "VPMO_AWS_ACCESS", "VPMO_AWS_SECRET", "MONGO_HOST"]


def loading_app(wsgi_environ, start_response):
    global real_app
    import os
    for key in KEYS_TO_LOAD:
        try:
            os.environ[key] = wsgi_environ[key]
        except KeyError:
            # The WSGI environment doesn't have the key
            pass
    from django.core.wsgi import get_wsgi_application
    real_app = get_wsgi_application()
    return real_app(wsgi_environ, start_response)

real_app = loading_app

application = lambda env, start: real_app(env, start)

"""

class WSGIEnvironment(WSGIHandler):

    def __call__(self, environ, start_response):

        
        for variable in env_variables:
            os.environ[variable] = environ[variable]
        return super(WSGIEnvironment, self).__call__(environ, start_response)

application = WSGIEnvironment()
"""

# application = get_wsgi_application()
