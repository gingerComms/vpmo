from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/chat/(?P<node_id>[^/]+)/$', consumers.ChatConsumer),
]