from django.apps import AppConfig


class VpmodocConfig(AppConfig):
    name = 'vpmodoc'

    def ready(self):
    	import vpmodoc.signals
