from django.apps import AppConfig


class VpmoauthConfig(AppConfig):
    name = 'vpmoauth'

    def ready(self):
    	import vpmoauth.signals
