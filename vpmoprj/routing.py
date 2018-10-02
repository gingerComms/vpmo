from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import vpmotree.routing


application = ProtocolTypeRouter({
	# Contains routing for tasks
	"websocket": 
		URLRouter(
			vpmotree.routing.websocket_urlpatterns
		)
})