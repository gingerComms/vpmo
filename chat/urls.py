from django.urls import path
from chat.views import *

app_name = "chat"

urlpatterns = [
	path("token/", TwilioTokenView.as_view(), name="twilio-token")
]