from django.conf import settings

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import (
    SyncGrant,
    VideoGrant,
    ChatGrant
)

# Create your views here.
class TwilioTokenView(APIView):
	""" Generates and returns a Twilio token for authenticated user """
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		# get credentials for environment variables
	    identity = request.user.username

	    account_sid = settings.TWILIO_ACCOUNT_SID
	    api_key = settings.TWILIO_API_KEY
	    api_secret = os.settings.TWILIO_SECRET_KEY
	    chat_service_sid = settings.TWILIO_CHAT_SERVICE_SID

	    # Create access token with credentials
	    token = AccessToken(account_sid, api_key, api_secret, identity=identity)

	    # Create an Chat grant and add to token
	    if chat_service_sid:
	        chat_grant = ChatGrant(service_sid=chat_service_sid)
	        token.add_grant(chat_grant)

	    # Return token info as JSON
	    return Response({
	    	"identity": identity,
	    	"token": token.to_jwt().decode('utf-8')
	    })