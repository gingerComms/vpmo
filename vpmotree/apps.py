from django.apps import AppConfig


class VpmotreeConfig(AppConfig):
    name = 'vpmotree'

    def ready(self):
    	import vpmotree.signals
